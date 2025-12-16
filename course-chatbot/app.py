import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from recommender import recommend_with_gemini, answer_dataset_question
from utils.gemini_utils import classify_user_intent, parse_query_with_gemini
from utils.conversation_manager import (
    needs_more_info,
    build_conversational_response,
    should_ask_followup,
    extract_level_from_text,
    extract_paid_preference,
    extract_price_range
)

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Course Recommendation Chatbot",
    page_icon="🎓",
    layout="wide"
)

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "data", "udemy_courses.csv")
    return pd.read_csv(csv_path)

df = load_data()

# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "messages": [],
    "recommended": None,
    "page": 0,
    "view": "chat",          # "chat" or "details"
    "selected_course_id": None,
    "awaiting_info": None,   # What info are we waiting for: "subject", "level", "budget", etc.
    "partial_query": "",      # Accumulated query text
    "last_query": "",         # Last successful query for context retention
    "last_parsed": {},        # Last parsed filters
    "conversation_context": {  # Track conversation state
        "has_subject": False,
        "has_level": False,
        "has_budget": False,
        "asked_level": 0,
        "asked_budget": 0,
        "asked_refinement": False
    },
    "partial_filters": {},     # Accumulated filters
    "course_description": "",  # AI-generated course description
    "last_described_course": None  # Track which course was last described
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================
# CHIT CHAT & HELPERS
# =====================================================
def handle_chitchat(text):
    t = text.lower().strip()
    if t in ["hi", "hello", "hey", "hii", "hello there", "hi there"]:
        return "👋 Hi! I'm your course recommendation assistant. What would you like to learn today?"
    if "thank" in t:
        return "😊 You're very welcome! Feel free to ask if you need more courses."
    if t in ["bye", "goodbye", "see you"]:
        return "👋 Goodbye! Happy learning! Come back anytime."
    if t in ["help", "how does this work", "what can you do"]:
        return "I can help you find the perfect course! Just tell me:\n- What subject you want to learn\n- Your skill level (beginner/intermediate/advanced)\n- Your budget preference\n\nI'll ask questions to understand your needs better!"
    if "reset" in t or "start over" in t or "clear" in t:
        # Reset conversation
        st.session_state.awaiting_info = None
        st.session_state.partial_query = ""
        st.session_state.partial_filters = {}
        st.session_state.conversation_context = {
            "has_subject": False,
            "has_level": False,
            "has_budget": False,
            "asked_level": 0,
            "asked_budget": 0,
            "asked_refinement": False
        }
        return "🔄 Conversation reset! What would you like to learn?"
    return None

# =====================================================
# ----------- COURSE DETAILS VIEW ---------------------
# =====================================================
if st.session_state.view == "details":

    course = df[df["course_id"] == st.session_state.selected_course_id].iloc[0]

    # Header
    col1, col2 = st.columns([10, 1])
    with col1:
        st.title(course["course_title"])
    with col2:
        if st.button("❌"):
            st.session_state.view = "chat"
            st.rerun()

    # Generate and display AI description
    if "course_description" not in st.session_state or st.session_state.get("last_described_course") != st.session_state.selected_course_id:
        with st.spinner("🤖 Generating course overview..."):
            from utils.gemini_utils import generate_course_description
            st.session_state.course_description = generate_course_description(course)
            st.session_state.last_described_course = st.session_state.selected_course_id
    
    st.markdown("### 📝 Course Overview")
    st.info(st.session_state.course_description)
    
    st.divider()

    # Formatting
    price = "FREE" if course["price"] == 0 else f"₹{course['price']}"
    duration = round(float(course["content_duration"]), 2)
    published = pd.to_datetime(course["published_timestamp"]).strftime("%d %B %Y")

    # Layout
    colA, colB = st.columns(2)

    with colA:
        st.subheader("📘 Course Info")
        st.write("**Course ID:**", course["course_id"])
        st.write("**Subject:**", course["subject"])
        st.write("**Level:**", course["level"])
        st.write("**Lectures:**", course["num_lectures"])
        st.write("**Duration:**", f"{duration} hours")

    with colB:
        st.subheader("💰 Engagement")
        st.write("**Price:**", price)
        st.write("**Subscribers:**", course["num_subscribers"])
        st.write("**Reviews:**", course["num_reviews"])
        st.write("**Published:**", published)
        st.write("**Paid:**", "Yes" if course["is_paid"] else "No")

    st.divider()
    st.markdown(
        f"### 🔗 Course Link\n[{course['url']}]({course['url']})",
        unsafe_allow_html=True
    )

    st.stop()  # Stop rendering chat screen below

def handle_followup_response(user_response):
    """Handle user's response to our clarifying question"""
    awaiting = st.session_state.awaiting_info
    
    if awaiting == "subject":
        # User provided subject/topic
        st.session_state.partial_query += " " + user_response
        st.session_state.conversation_context["has_subject"] = True
        st.session_state.awaiting_info = None
        
        # Now ask about level
        st.session_state.awaiting_info = "level"
        st.session_state.conversation_context["asked_level"] += 1
        return f"Great! I'll look for courses on **{user_response}**. What's your current skill level?\n- Beginner (just starting)\n- Intermediate (some experience)\n- Advanced (experienced)\n- Any level"
    
    elif awaiting == "level":
        # Extract level from response
        level = extract_level_from_text(user_response)
        if level:
            st.session_state.partial_filters["level"] = level
            st.session_state.conversation_context["has_level"] = True
        st.session_state.awaiting_info = None
        
        # Now ask about budget
        st.session_state.awaiting_info = "budget"
        st.session_state.conversation_context["asked_budget"] += 1
        return f"Perfect! And what about your budget? Are you looking for free courses or open to paid ones?"
    
    elif awaiting == "budget":
        # Extract budget preference
        paid_pref = extract_paid_preference(user_response)
        if paid_pref is not None:
            st.session_state.partial_filters["is_paid"] = paid_pref
            
            # If paid, ask for price range
            if paid_pref:
                st.session_state.awaiting_info = "price_range"
                return "What's your budget range? (e.g., 'under 200', 'between 100 and 500')"
        
        st.session_state.conversation_context["has_budget"] = True
        st.session_state.awaiting_info = None
        
        # Now we have enough info - do the search
        return perform_search_with_filters()
    
    elif awaiting == "price_range":
        # Extract price range
        min_p, max_p = extract_price_range(user_response)
        if min_p is not None:
            st.session_state.partial_filters["min_price"] = min_p
        if max_p is not None:
            st.session_state.partial_filters["max_price"] = max_p
        
        st.session_state.awaiting_info = None
        
        # Now do the search
        return perform_search_with_filters()
    
    elif awaiting == "refinement":
        # User wants to refine results
        st.session_state.awaiting_info = None
        st.session_state.partial_query = user_response
        return handle_recommendation_flow(user_response)
    
    return "I didn't quite catch that. Could you please rephrase?"


def perform_search_with_filters():
    """Execute search with accumulated filters"""
    # Build query from partial_query and filters
    query_text = st.session_state.partial_query.strip()
    
    # Parse with Gemini to get keywords
    parsed = parse_query_with_gemini(query_text)
    
    # Override with our accumulated filters
    if "level" in st.session_state.partial_filters:
        parsed["level"] = st.session_state.partial_filters["level"]
    if "is_paid" in st.session_state.partial_filters:
        parsed["is_paid"] = st.session_state.partial_filters["is_paid"]
    if "min_price" in st.session_state.partial_filters:
        parsed["min_price"] = st.session_state.partial_filters["min_price"]
    if "max_price" in st.session_state.partial_filters:
        parsed["max_price"] = st.session_state.partial_filters["max_price"]
    
    # Get recommendations
    recs = recommend_with_gemini(query_text, parsed_override=parsed)
    
    if recs.empty:
        # Reset for new search
        st.session_state.partial_query = ""
        st.session_state.partial_filters = {}
        # Generate empathetic response
        from utils.gemini_utils import generate_empathetic_no_results_message
        return generate_empathetic_no_results_message(query_text, parsed)
    
    # Success!
    st.session_state.recommended = recs
    st.session_state.page = 0
    
    # Check if we should ask for refinement
    ask_followup, followup_q = should_ask_followup(
        len(recs),
        st.session_state.conversation_context
    )
    
    response = build_conversational_response(parsed, len(recs))
    
    if ask_followup:
        st.session_state.awaiting_info = "refinement"
        st.session_state.conversation_context["asked_refinement"] = True
        response += "\n\n" + followup_q
    
    # Reset for next query
    st.session_state.partial_query = ""
    st.session_state.partial_filters = {}
    
    return response


def handle_recommendation_flow(query):
    """Handle the recommendation request with conversational flow"""
    # Parse the query first
    parsed = parse_query_with_gemini(query)
    
    # Check if query is just adding constraints (budget/level) without new subject
    is_constraint_only = (
        not parsed["keywords"] and 
        (parsed.get("min_price") or parsed.get("max_price") or 
         parsed.get("level") != "all levels" or 
         parsed.get("is_paid") is not None)
    )
    
    # If constraint only and we have a last query, merge with last query
    if is_constraint_only and st.session_state.last_query:
        # User is refining previous search
        base_parsed = st.session_state.last_parsed.copy()
        
        # Apply new constraints
        if parsed.get("level") != "all levels":
            base_parsed["level"] = parsed["level"]
        if parsed.get("is_paid") is not None:
            base_parsed["is_paid"] = parsed["is_paid"]
        if parsed.get("min_price") is not None:
            base_parsed["min_price"] = parsed["min_price"]
        if parsed.get("max_price") is not None:
            base_parsed["max_price"] = parsed["max_price"]
        
        parsed = base_parsed
        
        # Acknowledge the refinement
        acknowledgment = "Got it! "
        if parsed.get("min_price") or parsed.get("max_price"):
            min_p = parsed.get("min_price", 0)
            max_p = parsed.get("max_price", 99999)
            if max_p < 99999:
                acknowledgment += f"Filtering for courses under ₹{max_p}. "
            else:
                acknowledgment += f"Filtering for courses over ₹{min_p}. "
        if parsed.get("level") != "all levels":
            acknowledgment += f"Looking for {parsed['level']}. "
        if parsed.get("is_paid") is False:
            acknowledgment += "Showing only free courses. "
        elif parsed.get("is_paid") is True:
            acknowledgment += "Including paid courses. "
    # Check if we have existing partial context (user is adding more info)
    elif st.session_state.partial_query and not st.session_state.awaiting_info:
        # User is adding more information to previous query
        # Merge the new information
        merged_query = st.session_state.partial_query + " " + query
        parsed_merged = parse_query_with_gemini(merged_query)
        
        # Merge filters - prefer new parsed info for conflicts
        if parsed["keywords"]:
            parsed_merged["keywords"].extend(parsed["keywords"])
        if parsed.get("level") != "all levels":
            parsed_merged["level"] = parsed["level"]
        if parsed.get("is_paid") is not None:
            parsed_merged["is_paid"] = parsed["is_paid"]
        if parsed.get("min_price") is not None:
            parsed_merged["min_price"] = parsed["min_price"]
        if parsed.get("max_price") is not None:
            parsed_merged["max_price"] = parsed["max_price"]
        
        # Update partial query
        st.session_state.partial_query = merged_query
        parsed = parsed_merged
        
        # Acknowledge the addition
        acknowledgment = "Got it! "
        if parsed.get("min_price") or parsed.get("max_price"):
            acknowledgment += "I'll include your budget preference. "
        if parsed.get("level") != "all levels":
            acknowledgment += f"Looking for {parsed['level']}. "
        if parsed.get("is_paid") is False:
            acknowledgment += "Filtering for free courses. "
        elif parsed.get("is_paid") is True:
            acknowledgment += "Including paid courses. "
    else:
        acknowledgment = ""
    
    # Check if we need more information
    needs_info, missing, question = needs_more_info(query, parsed)
    
    if needs_info:
        # Start gathering information
        st.session_state.awaiting_info = missing
        st.session_state.partial_query = query
        return question
    
    # We have enough info - get recommendations
    recs = recommend_with_gemini(query, parsed_override=parsed)
    
    if recs.empty:
        # Clear partial context on failure but keep last query
        st.session_state.partial_query = ""
        # Generate empathetic response using Gemini
        from utils.gemini_utils import generate_empathetic_no_results_message
        return generate_empathetic_no_results_message(query, parsed)
    
    st.session_state.recommended = recs
    st.session_state.page = 0
    
    # Store last successful query and filters for context
    st.session_state.last_query = query
    st.session_state.last_parsed = parsed.copy()
    
    # Check if we should offer refinement
    ask_followup, followup_q = should_ask_followup(
        len(recs),
        st.session_state.conversation_context
    )
    
    response = acknowledgment + build_conversational_response(parsed, len(recs))
    
    if ask_followup:
        st.session_state.awaiting_info = "refinement"
        st.session_state.conversation_context["asked_refinement"] = True
        response += "\n\n" + followup_q
    
    # Clear partial context after successful search (but keep last_query for context)
    st.session_state.partial_query = ""
    
    return response


# =====================================================
# ---------------- CHAT VIEW ---------------------------
# =====================================================
st.title("🎓 AI Course Recommendation Assistant")
st.caption("Chat • Browse • Decide")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
query = st.chat_input("Ask for course recommendations...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        chitchat = handle_chitchat(query)

        if chitchat:
            reply = chitchat
        else:
            # Check if we're in middle of gathering information
            if st.session_state.awaiting_info:
                reply = handle_followup_response(query)
            else:
                # New query - determine intent
                intent = classify_user_intent(query)

                if intent == "recommendation":
                    reply = handle_recommendation_flow(query)
                else:
                    # For non-recommendation queries, preserve context but don't search
                    reply = answer_dataset_question(query)

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# =====================================================
# COURSE CARDS
# =====================================================
if st.session_state.recommended is not None:

    st.markdown("## 🧾 Recommended Courses")

    per_page = 5
    start = st.session_state.page * per_page
    end = start + per_page
    subset = st.session_state.recommended.iloc[start:end]

    cols = st.columns(5)

    for i, (_, rec) in enumerate(subset.iterrows()):
        course = df[df["course_id"] == rec["course_id"]].iloc[0]

        with cols[i]:
            with st.container(height=360, border=True):
                st.subheader(course["course_title"][:45])
                st.caption(course["subject"])
                st.write(f"🎯 {course['level']}")

                if course["price"] == 0:
                    st.success("FREE")
                else:
                    st.write(f"💰 ₹{course['price']}")

                st.write(f"📊 Match: {rec['match_percent']:.1f}%")

                if st.button("View Details", key=f"view_{course['course_id']}"):
                    st.session_state.selected_course_id = course["course_id"]
                    st.session_state.view = "details"
                    st.rerun()

# =====================================================
# PAGINATION
# =====================================================
if st.session_state.recommended is not None:
    total_pages = (len(st.session_state.recommended) - 1) // 5 + 1

    col_prev, col_mid, col_next = st.columns([1, 2, 1])

    with col_prev:
        st.button(
            "⬅ Previous",
            disabled=st.session_state.page == 0,
            on_click=lambda: st.session_state.update(
                {"page": st.session_state.page - 1}
            )
        )

    with col_next:
        st.button(
            "Next ➡",
            disabled=st.session_state.page >= total_pages - 1,
            on_click=lambda: st.session_state.update(
                {"page": st.session_state.page + 1}
            )
        )

    with col_mid:
        st.markdown(
            f"### Page {st.session_state.page + 1} of {total_pages}"
        )
