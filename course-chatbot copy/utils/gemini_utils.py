import google.generativeai as genai
import json
import re
import os
import streamlit as st
from utils.prompt_templates import QUERY_PARSER_PROMPT

# Configure Gemini with API key from environment or Streamlit secrets
api_key = None

# Try Streamlit secrets first (for cloud deployment)
try:
    api_key = st.secrets.get("GOOGLE_API_KEY")
except:
    pass

# Fall back to environment variable
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")

# If still no key, raise error
if not api_key:
    raise ValueError(
        "GOOGLE_API_KEY not found! "
        "Please set it in:\n"
        "- Local: .env file or environment variable\n"
        "- Cloud: Streamlit Cloud Secrets"
    )

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")


def safe_json_parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    return {
        "keywords": [],
        "level": "all levels",
        "is_paid": None,
        "min_price": None,
        "max_price": None
    }


def parse_query_with_gemini(user_query):
    response = model.generate_content(
        QUERY_PARSER_PROMPT + user_query
    )

    parsed = safe_json_parse(response.text)

    if "keywords" not in parsed:
        parsed["keywords"] = []

    if parsed.get("level") not in {
        "all levels",
        "beginner level",
        "intermediate level",
        "expert level"
    }:
        parsed["level"] = "all levels"

    return parsed


def classify_user_intent(query):
    prompt = f"""
Classify intent as ONE word only:
- recommendation (looking for course recommendations, course search, learning requests)
- dataset_question (asking about statistics, facts, information about courses)

User query:
{query}

Response (ONE WORD ONLY):"""
    response = model.generate_content(prompt)
    intent = response.text.strip().lower()
    
    # Ensure we return valid intent
    if "recommend" in intent:
        return "recommendation"
    elif "dataset" in intent or "question" in intent:
        return "dataset_question"
    
    # Default to recommendation for course-related queries
    query_lower = query.lower()
    if any(word in query_lower for word in ["course", "learn", "budget", "price", "show", "find", "want"]):
        return "recommendation"
    
    return "dataset_question"


def generate_empathetic_no_results_message(user_query, filters):
    """Generate a personalized, empathetic response when no courses are found"""
    filter_desc = []
    if filters.get("keywords"):
        filter_desc.append(f"on {' '.join(filters['keywords'])}")
    if filters.get("level") != "all levels":
        filter_desc.append(f"at {filters['level']}")
    if filters.get("is_paid") is False:
        filter_desc.append("that are free")
    if filters.get("max_price"):
        filter_desc.append(f"under ₹{filters['max_price']}")
    
    criteria = " ".join(filter_desc) if filter_desc else "matching your criteria"
    
    prompt = f"""
You are a helpful course recommendation assistant. A user searched for courses {criteria}, but we couldn't find any matches.

Generate a warm, empathetic, and helpful response (2-3 sentences) that:
1. Acknowledges their interest and validates their learning goal
2. Offers 2-3 specific, actionable alternatives (like trying a broader search, different level, adjusting budget, or related topics)
3. Keeps them motivated and engaged

User's original query: "{user_query}"

Response:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"😔 I couldn't find courses {criteria}. Let's try something different! You could:\n• Search for a broader topic\n• Try a different skill level\n• Adjust your budget range\n\nWhat would you like to explore?"


def generate_course_description(course_data):
    """Generate an engaging AI description for a course based on its details"""
    prompt = f"""
You are a course advisor. Generate an engaging, informative course description (3-4 sentences) based on these details:

Course Title: {course_data['course_title']}
Subject: {course_data['subject']}
Level: {course_data['level']}
Number of Lectures: {course_data['num_lectures']}
Duration: {course_data['content_duration']} hours
Subscribers: {course_data['num_subscribers']}

The description should:
1. Explain what the course covers and who it's for
2. Highlight key learning outcomes or skills
3. Be encouraging and motivational
4. Sound natural and friendly

Description:"""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"This {course_data['level']} course on {course_data['subject']} covers {course_data['num_lectures']} lectures over {round(float(course_data['content_duration']), 1)} hours. Perfect for learners looking to master {course_data['subject']}!"
