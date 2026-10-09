import json
import re

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)

MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(
    page_title="StyleSnap AI",
    page_icon="👗",
    layout="centered",
)


# -------------------- Secrets --------------------

def secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except (FileNotFoundError, KeyError):
        return default


GEMINI_API_KEY = secret("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = secret("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = secret("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = secret(
    "TWILIO_WHATSAPP_FROM",
    "whatsapp:+17372508034",
)
TWILIO_CONTENT_SID = secret("TWILIO_CONTENT_SID")


@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_twilio_client(account_sid, auth_token):
    return TwilioClient(account_sid, auth_token)


# -------------------- CSS --------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #fff8fb !important;
        color: #33232d !important;
    }

    .stApp h1, .stApp h2, .stApp h3 {
        color: #51283f !important;
    }

    .stApp p, .stApp label,
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stWidgetLabel"] p {
        color: #33232d !important;
    }

    .hero {
        padding: 1.2rem 1.3rem;
        border-radius: 18px;
        background: #f6e8ef;
        border: 1px solid #ead3df;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0;
        color: #51283f !important;
    }

    .hero p {
        margin-bottom: 0;
        color: #69475b !important;
    }

    /* Text fields */
    .stApp [data-testid="stTextInput"] [data-baseweb="input"] {
        background: #ffffff !important;
        border: 1px solid #d7c4cf !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }

    .stApp [data-testid="stTextInput"] input {
        background: #ffffff !important;
        color: #29232a !important;
        -webkit-text-fill-color: #29232a !important;
        caret-color: #29232a !important;
        opacity: 1 !important;
        color-scheme: light !important;
    }

    .stApp [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
        border-color: #b87598 !important;
        box-shadow: 0 0 0 1px #b87598 !important;
    }

    /* Browser autofill */
    .stApp input:-webkit-autofill,
    .stApp input:-webkit-autofill:hover,
    .stApp input:-webkit-autofill:focus {
        -webkit-text-fill-color: #29232a !important;
        -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
        box-shadow: 0 0 0 1000px #ffffff inset !important;
        color-scheme: light !important;
    }

    /* Selectbox */
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"],
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] [role="combobox"] {
        background: #ffffff !important;
        background-color: #ffffff !important;
        border-color: #d7c4cf !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        color: #29232a !important;
        -webkit-text-fill-color: #29232a !important;
    }

    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] [role="combobox"] * {
        background-color: transparent !important;
        color: #29232a !important;
        -webkit-text-fill-color: #29232a !important;
    }

    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] svg {
        color: #29232a !important;
        fill: #29232a !important;
    }

    .stApp [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
        border-color: #b87598 !important;
        box-shadow: 0 0 0 1px #b87598 !important;
    }

    /* Chat */
    .stApp [data-testid="stChatMessage"] p,
    .stApp [data-testid="stChatMessage"] li {
        color: #33232d !important;
    }

    .stApp [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #29232a !important;
        -webkit-text-fill-color: #29232a !important;
        caret-color: #29232a !important;
    }

    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button {
        background: #6c3b59 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: 1px solid #6c3b59 !important;
        border-radius: 10px !important;
        min-height: 42px !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    .stButton > button *,
    .stFormSubmitButton > button * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: #512b43 !important;
        border-color: #512b43 !important;
    }

    .stForm {
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------- Check API key --------------------

if not GEMINI_API_KEY:
    st.markdown(
        '<div class="hero"><h1>👗 StyleSnap AI</h1>'
        "<p>Your personal AI outfit and color-matching assistant.</p></div>",
        unsafe_allow_html=True,
    )
    st.error(
        "Gemini API key is missing. Add GEMINI_API_KEY to "
        ".streamlit/secrets.toml, then restart the app."
    )
    st.stop()

gemini_client = get_gemini_client(GEMINI_API_KEY)


# -------------------- Session state --------------------

if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if "messages" not in st.session_state:
    st.session_state.messages = []


# -------------------- Chat helpers --------------------

def ask_gemini(parts):
    """Send a request to Gemini and show a useful message if it fails."""
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text or "I couldn't create a response. Please try again."
    except Exception as error:
        error_text = str(error)
        if "503" in error_text or "UNAVAILABLE" in error_text:
            st.warning(
                "Gemini is temporarily busy. Please wait a little and try again."
            )
        elif "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            st.warning(
                "Gemini's request quota has been reached. Check your API quota "
                "or try again after it resets."
            )
        else:
            st.error(
                "Gemini request failed. Check your API key, model access, "
                "and internet connection."
            )
        return None


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.markdown(message["content"])
        elif message["kind"] == "image":
            st.image(
                message["content"],
                caption="Your outfit photo",
                use_container_width=True,
            )


def add_message(role, kind, content):
    message = {"role": role, "kind": kind, "content": content}
    st.session_state.messages.append(message)
    render_message(message)


# -------------------- WhatsApp helpers --------------------

def clean_whatsapp_text(value):
    if not value:
        return "No style summary is available yet."
    value = " ".join(value.split())
    return value[:1400] + "..." if len(value) > 1400 else value


def build_conversation_summary():
    """Build a WhatsApp summary from existing replies without another Gemini call."""
    assistant_replies = [
        message["content"].strip()
        for message in st.session_state.messages
        if message.get("role") == "assistant"
        and message.get("kind") == "text"
        and message.get("content", "").strip()
    ]

    # Use the latest styling advice first, rather than sending the entire chat.
    if assistant_replies:
        selected_replies = assistant_replies[-3:]
        return "StyleSnap AI style summary: " + " ".join(selected_replies)

    user_messages = [
        message["content"].strip()
        for message in st.session_state.messages
        if message.get("role") == "user"
        and message.get("kind") == "text"
        and message.get("content", "").strip()
    ]
    if user_messages:
        return "Your styling request: " + " ".join(user_messages[-3:])
    return "Start chatting with StyleSnap AI to build your style summary."


def send_whatsapp(to_number, user_name, summary):
    """Send the AI style summary using the Twilio WhatsApp Content Template."""
    if not all(
        [
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_WHATSAPP_FROM,
            TWILIO_CONTENT_SID,
        ]
    ):
        return False, (
            "Twilio settings are missing. Check TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, and "
            "TWILIO_CONTENT_SID in .streamlit/secrets.toml."
        )

    to_number = to_number.strip()
    if not re.fullmatch(r"\+[1-9]\d{7,14}", to_number):
        return False, (
            "Enter a valid international number, such as +919876543210."
        )

    try:
        client = get_twilio_client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
        )

        content_variables = json.dumps(
            {
                "1": user_name,
                "2": clean_whatsapp_text(summary),
            },
            ensure_ascii=False,
        )

        message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )
        return True, message.sid

    except Exception as error:
        return False, str(error)


# -------------------- Onboarding --------------------

if not st.session_state.onboarded:
    st.markdown(
        '<div class="hero"><h1>👗 StyleSnap AI</h1>'
        "<p>Your personal AI outfit and color-matching assistant.</p></div>",
        unsafe_allow_html=True,
    )
    st.write(
        "Upload an outfit photo or describe what you plan to wear. "
        "Get practical styling ideas and send a summary to WhatsApp."
    )

    with st.form("onboarding_form"):
        name = st.text_input("Your name", max_chars=80)
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="Use a number that has joined your Twilio Sandbox.",
        )
        occasion = st.selectbox(
            "What do you usually want style help with?",
            [
                "Everyday casual",
                "College / work",
                "Party / event",
                "Traditional wear",
                "General styling",
            ],
        )
        submitted = st.form_submit_button(
            "Find my style ✨",
            use_container_width=True,
        )

    if submitted:
        if not name.strip():
            st.warning("Please enter your name.")
        elif not re.fullmatch(r"\+[1-9]\d{7,14}", whatsapp_number.strip()):
            st.warning(
                "Enter a valid international number, "
                "for example +919876543210."
            )
        else:
            try:
                chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            SYSTEM_PROMPT
                            + "\nThe user's preferred styling context is: "
                            + occasion
                            + "."
                        )
                    ),
                )
                st.session_state.name = name.strip()
                st.session_state.whatsapp_number = whatsapp_number.strip()
                st.session_state.occasion = occasion
                st.session_state.chat = chat
                st.session_state.messages = []
                st.session_state.onboarded = True
                st.rerun()
            except Exception as error:
                st.error(
                    "Could not start the chat. Check your Gemini API key "
                    "and model access."
                )
                st.exception(error)

    st.stop()


# -------------------- Main chat page --------------------

left, right = st.columns([5, 2], vertical_alignment="center")

with left:
    st.markdown(
        '<div class="hero"><h1>👗 StyleSnap AI</h1>'
        "<p>Style ideas that fit your vibe.</p></div>",
        unsafe_allow_html=True,
    )

with right:
    if st.button(
        "📋 Create style summary",
        disabled=len(st.session_state.messages) < 2,
        use_container_width=True,
    ):
        st.session_state.style_summary = build_conversation_summary()

if st.session_state.get("style_summary"):
    st.markdown("### Your StyleSnap summary")
    st.caption("Copy the summary below and paste it into WhatsApp whenever you're ready.")
    st.text_area(
        "Style summary (select and copy)",
        value=st.session_state.style_summary,
        height=180,
        key="style_summary_display",
    )
    st.button(
        "📲 Open WhatsApp",
        on_click=lambda: st.session_state.update({"open_whatsapp_hint": True}),
    )
    if st.session_state.get("open_whatsapp_hint"):
        st.info("Open WhatsApp on your device, choose the chat, and paste the copied summary. This free version does not send messages through Twilio.")

st.caption(
    f"Hi {st.session_state.name} · "
    f"Styling preference: {st.session_state.occasion}"
)


# -------------------- Conversation history --------------------

if not st.session_state.messages:
    welcome = WELCOME_MESSAGE_TEMPLATE.format(
        name=st.session_state.name
    )
    add_message("assistant", "text", welcome)
else:
    for message in st.session_state.messages:
        render_message(message)


# -------------------- Quick prompts --------------------

with st.expander("Quick prompts", expanded=False):
    quick_prompt = st.selectbox(
        "Choose a prompt",
        [
            "Suggest three colors that go with blue jeans.",
            "Help me style a white shirt for college.",
            "Suggest accessories for a simple black outfit.",
            "What should I wear to a casual birthday party?",
            "How can I style a kurta for a family event?",
        ],
    )
    if st.button("Ask this"):
        st.session_state.pending_prompt = quick_prompt
        st.rerun()


# -------------------- Text and photo input --------------------

user_input = st.chat_input(
    "Describe an outfit or attach a photo",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
)

pending_prompt = st.session_state.pop("pending_prompt", None)

if user_input or pending_prompt:
    photo = (
        user_input.files[0]
        if user_input and user_input.files
        else None
    )
    text = (
        user_input.text.strip()
        if user_input and user_input.text
        else ""
    )

    if pending_prompt:
        text = pending_prompt

    parts = []

    if photo:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type or "image/jpeg",
            )
        )

    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo:
        parts.append(
            "Describe the visible outfit, colors, and clothing items. "
            "Suggest practical ways to style it, including matching "
            "colors and accessories. Do not identify the person or "
            "infer sensitive personal attributes."
        )

    if parts:
        with st.spinner("Putting together your style ideas..."):
            answer = ask_gemini(parts)
        if answer:
            add_message("assistant", "text", answer)


# -------------------- Footer --------------------

st.caption(
    "Style suggestions are subjective. Avoid sharing photos "
    "containing private or sensitive information."
)
