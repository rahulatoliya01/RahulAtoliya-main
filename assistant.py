import os
import re

import streamlit as st
from dotenv import load_dotenv
from google import genai

try:
    from google.genai import types
    _HAS_GOOGLE_SEARCH = hasattr(types, "Tool") and hasattr(types, "GoogleSearch")
except (ImportError, AttributeError):
    types = None  # type: ignore[misc, assignment]
    _HAS_GOOGLE_SEARCH = False

from db_utils import load_knowledge


# Load environment variables from a local .env file
load_dotenv()

# Prefer Streamlit secrets in production, fall back to env var locally.
try:
    api_key = st.secrets["GOOGLE_API_KEY"]  # type: ignore[index]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None

# Stopwords for relevance filtering
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "when", "where",
    "who", "which", "how", "why", "can", "could", "would", "should", "do",
    "does", "did", "i", "me", "my", "we", "our", "you", "your", "it", "its",
}

SEARCH_WEB_MARKER = "[NEED_WEB_SEARCH]"

DB_ONLY_PROMPT = (
    "You are SVU-MCA Assistant for MCA students of Samrat Vikramaditya University, Ujjain. "
    "Answer ONLY using the university data provided below. "
    "Be friendly, professional, and student-focused.\n\n"
    "If the question CANNOT be answered from the provided data, respond with exactly: "
    f"{SEARCH_WEB_MARKER}\n\n"
    "--- University data ---\n"
)

WEB_FALLBACK_PROMPT = (
    "You are SVU-MCA Assistant for MCA students. "
    "Search the web for current information to answer this question. "
    "Be helpful, cite sources when possible, and stay relevant to the university/education context."
)


def _extract_keywords(question: str) -> set:
    """Extract meaningful keywords from question for relevance matching."""
    words = re.findall(r"\b\w{2,}\b", question.lower())
    return {w for w in words if w not in STOPWORDS}


def get_relevant_knowledge(question: str) -> list[dict]:
    """
    Retrieve documents/notifications from DB relevant to the question.
    Uses keyword overlap. Returns all knowledge if no keywords match.
    """
    knowledge = load_knowledge()
    keywords = _extract_keywords(question)
    if not keywords:
        return knowledge

    relevant = []
    for k in knowledge:
        text = (k["title"] + " " + k["description"]).lower()
        if any(kw in text for kw in keywords):
            relevant.append(k)

    return relevant if relevant else knowledge


def _answer_from_db(question: str, knowledge_text: str, recent_context: str) -> str:
    """Try to answer using only DB knowledge."""
    full_prompt = (
        DB_ONLY_PROMPT
        + knowledge_text
        + ("\n\nRecent chat:\n" + recent_context if recent_context else "")
        + "\n\n---\n\nQuestion: "
        + question
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )
    return response.text


def _answer_with_web_search(question: str) -> str:
    """Answer using Google Search when DB doesn't have the info."""
    if not _HAS_GOOGLE_SEARCH:
        return (
            "This information is not in our university database. "
            "Web search is not available in this setup. Please check the official university website or contact the administration."
        )
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=WEB_FALLBACK_PROMPT + "\n\nQuestion: " + question,
        config=config,
    )
    return response.text


@st.cache_data(ttl=300)
def ask_ai(question, recent_context: str = "") -> str:
    """
    Answer using DB (college_data) first. If info is not in DB, retrieve from internet.
    """
    if client is None:
        return (
            "⚠️ Google Gemini API key is not configured.\n"
            "Set `GOOGLE_API_KEY` in Streamlit secrets or as an environment variable."
        )

    # 1. Retrieve related info from DB
    relevant = get_relevant_knowledge(question)
    knowledge_text = "\n".join(
        k["title"] + ": " + k["description"] for k in relevant
    )

    try:
        # 2. Try answering from DB only
        answer = _answer_from_db(question, knowledge_text, recent_context)

        # 3. If DB doesn't have the info, fallback to web search
        if SEARCH_WEB_MARKER in answer:
            answer = _answer_with_web_search(question)

        return answer.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}\nYou may have exceeded your API quota or there was a network issue."
