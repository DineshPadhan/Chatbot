import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.gemini_utils import parse_query_with_gemini, model

# Load dataset using path relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "data", "udemy_courses.csv")
df = pd.read_csv(csv_path)

df.drop_duplicates(inplace=True)
df.fillna("", inplace=True)

df["course_title"] = df["course_title"].str.lower()
df["subject"] = df["subject"].str.lower()
df["level"] = df["level"].str.lower()
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
df["is_paid"] = df["is_paid"].astype(bool)

df["semantic_text"] = df["course_title"] + " " + df["subject"]

# TF-IDF
tfidf = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2
)

tfidf_matrix = tfidf.fit_transform(df["semantic_text"])


def recommend_with_gemini(user_query, min_match_percent=50, top_n=10, parsed_override=None):
    # Allow passing pre-parsed filters for conversational flow
    if parsed_override:
        parsed = parsed_override
    else:
        parsed = parse_query_with_gemini(user_query)

    semantic_query = " ".join(parsed["keywords"])
    if not semantic_query:
        semantic_query = user_query.lower()

    query_vector = tfidf.transform([semantic_query])
    similarity_scores = cosine_similarity(
        query_vector, tfidf_matrix
    )[0]

    results = df.copy()
    results["match_percent"] = similarity_scores * 100

    # Confidence threshold
    results = results[
        results["match_percent"] >= min_match_percent
    ]

    # Level filter
    if parsed["level"] != "all levels":
        results = results[
            results["level"] == parsed["level"]
        ]

    # Paid filter
    if parsed["is_paid"] is not None:
        results = results[
            results["is_paid"] == parsed["is_paid"]
        ]

    # Price filter
    if parsed["is_paid"]:
        if parsed["min_price"] is not None:
            results = results[
                results["price"] >= parsed["min_price"]
            ]
        if parsed["max_price"] is not None:
            results = results[
                results["price"] <= parsed["max_price"]
            ]

    return results.sort_values(
        by="match_percent", ascending=False
    )[[
        "course_id",
        "match_percent"
    ]].head(top_n)


def answer_dataset_question(question):
    sample_data = df.sample(
        min(40, len(df))
    ).to_csv(index=False)

    prompt = f"""
Answer ONLY using the dataset below.
If the answer is not present, say:
"Not available in the dataset."

Dataset:
{sample_data}

Question:
{question}
"""

    response = model.generate_content(prompt)
    return response.text
