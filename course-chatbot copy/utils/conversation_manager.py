"""
Conversation Manager for handling multi-turn dialogues
"""

VALID_LEVELS = {
    "all levels",
    "beginner level",
    "intermediate level",
    "expert level"
}


def extract_level_from_text(text):
    """Extract level from user's text response"""
    text = text.lower().strip()
    
    if "beginner" in text or "basic" in text or "new" in text or "starting" in text:
        return "beginner level"
    elif "intermediate" in text or "medium" in text or "mid" in text:
        return "intermediate level"
    elif "expert" in text or "advanced" in text or "master" in text or "professional" in text:
        return "expert level"
    elif "all" in text or "any" in text or "don't" in text or "doesn" in text:
        return "all levels"
    
    return None


def extract_paid_preference(text):
    """Extract paid/free preference from user's text"""
    text = text.lower().strip()
    
    if "free" in text or "no cost" in text or "0" in text or "zero" in text:
        return False
    elif "paid" in text or "premium" in text or "buy" in text or "purchase" in text:
        return True
    elif "both" in text or "any" in text or "either" in text or "don't" in text or "doesn" in text:
        return None
    
    return None


def extract_price_range(text):
    """Extract price range from user's text"""
    import re
    
    text = text.lower().strip()
    
    # Look for patterns like "100 to 500", "between 100 and 500", "under 200", "less than 300"
    
    # Pattern: X to Y or X and Y
    range_match = re.search(r'(\d+)\s*(?:to|-|and)\s*(\d+)', text)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))
    
    # Pattern: under/less than X
    under_match = re.search(r'(?:under|less than|below|max|maximum)\s*(\d+)', text)
    if under_match:
        return 0, int(under_match.group(1))
    
    # Pattern: over/more than X
    over_match = re.search(r'(?:over|more than|above|min|minimum)\s*(\d+)', text)
    if over_match:
        return int(over_match.group(1)), 99999
    
    # Single number might mean max price
    single_num = re.search(r'(\d+)', text)
    if single_num:
        return 0, int(single_num.group(1))
    
    return None, None


def needs_more_info(query_text, parsed_filters=None):
    """
    Determine if we need to ask clarifying questions
    Returns: (needs_info: bool, missing_aspect: str, question: str)
    """
    text = query_text.lower().strip()
    
    # Very generic queries need more info
    generic_phrases = [
        "recommend course",
        "suggest course",
        "find course",
        "looking for course",
        "want to learn",
        "help me find",
        "show me course"
    ]
    
    is_generic = any(phrase in text for phrase in generic_phrases)
    
    # Check if query has specific subject/topic
    has_subject = False
    if parsed_filters and parsed_filters.get("keywords"):
        has_subject = True
    
    # Short queries without specific terms
    if len(text.split()) <= 3 and not has_subject:
        return True, "subject", "What subject or topic are you interested in learning? (e.g., Python, Web Development, Marketing, etc.)"
    
    # Generic query without clear subject
    if is_generic and not has_subject:
        return True, "subject", "I'd love to help you find a course! What topic or skill are you interested in?"
    
    # Has subject but might benefit from level clarification
    if has_subject and parsed_filters:
        if parsed_filters.get("level") == "all levels":
            # Could ask about level, but make it optional
            return False, None, None  # Don't force level question
    
    return False, None, None


def build_conversational_response(parsed_filters, num_results):
    """Build a friendly conversational response based on filters applied"""
    parts = []
    
    if parsed_filters.get("keywords"):
        keywords = " ".join(parsed_filters["keywords"])
        parts.append(f"courses on **{keywords}**")
    else:
        parts.append("courses")
    
    if parsed_filters.get("level") != "all levels":
        parts.append(f"at **{parsed_filters['level']}**")
    
    if parsed_filters.get("is_paid") is False:
        parts.append("that are **free**")
    elif parsed_filters.get("is_paid") is True:
        parts.append("that are **paid**")
    
    if parsed_filters.get("min_price") or parsed_filters.get("max_price"):
        min_p = parsed_filters.get("min_price", 0)
        max_p = parsed_filters.get("max_price", 99999)
        if max_p < 99999:
            parts.append(f"under **₹{max_p}**")
        elif min_p > 0:
            parts.append(f"over **₹{min_p}**")
    
    response = "I found " + " ".join(parts)
    
    if num_results == 0:
        return "I couldn't find any " + " ".join(parts) + ". Would you like to try different criteria?"
    elif num_results == 1:
        return response.replace("I found", "I found 1")
    else:
        return f"{response}. Here are the top {min(num_results, 10)} recommendations:"


def generate_followup_question(conversation_context):
    """Generate intelligent follow-up questions based on conversation history"""
    
    if not conversation_context.get("has_subject"):
        return "What subject or topic would you like to learn about?"
    
    if conversation_context.get("asked_level", 0) < 1:
        return "What's your current skill level? (beginner, intermediate, or advanced)"
    
    if conversation_context.get("asked_budget", 0) < 1:
        return "Do you prefer free courses, or are you open to paid options?"
    
    return None


def should_ask_followup(num_results, conversation_context):
    """Decide if we should ask follow-up questions to refine results"""
    
    # If we have 0 results, offer to adjust criteria
    if num_results == 0:
        return True, "I couldn't find courses matching those criteria. Would you like to try:\n- A different subject?\n- Different difficulty level?\n- Adjust your budget?"
    
    # If we have too many results and haven't asked for refinement
    if num_results > 50 and not conversation_context.get("asked_refinement"):
        return True, f"I found {num_results} courses. Would you like me to help narrow this down by skill level or budget?"
    
    # If we have good results, we're done
    return False, None


def is_adding_context(text):
    """Check if the message is adding information to existing context"""
    text = text.lower().strip()
    
    # Keywords that indicate adding information
    addition_phrases = [
        "budget", "price", "cost", "under", "maximum", "minimum",
        "also", "and", "plus", "additionally", "moreover",
        "free", "paid", "between", "range",
        "beginner", "intermediate", "advanced", "expert",
        "my level", "skill level"
    ]
    
    return any(phrase in text for phrase in addition_phrases)
