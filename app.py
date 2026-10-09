import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(
    page_title="StyleSnap AI",
    page_icon="👗",
    layout="centered",
)


# -------------------- Secrets --------------------

def get_secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except (FileNotFoundError, KeyError):
        return default


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")


# -------------------- Styling --------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #fff8fb;
        color: #33232d;
    }

    h1, h2, h3 {
        color: #51283f;
    }

    .hero {
        padding: 1.2rem;
        border-radius: 18px;
        background: #f6e8ef;
        border: 1px solid #ead3df;
        margin-bottom: 1rem;
    }

    .stButton > button {
        background: #6c3b59;
        color: white;
        border-radius: 10px;
        min-height: 42px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------- API setup --------------------

if not GEMINI_API_KEY:
    st.title("👗 StyleSnap AI")
    st.error(
        "Gemini API key is missing. Add GEMINI_API_KEY "
        "to your Streamlit Secrets settings."
    )
    st.stop()


@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)


gemini_client = get_gemini_client(GEMINI_API_KEY)


# -------------------- Session state --------------------

defaults = {
    "onboarded": False,
    "messages": [],
    "style_summary": "",
    "pending_prompt": None,
    "occasion": "Everyday casual",
    "name": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------- Gemini helper --------------------

def ask_gemini(parts):
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text or "Please try another styling question."

    except Exception as error:
        error_text = str(error)

        if "503" in error_text or "UNAVAILABLE" in error_text:
            st.warning(
                "Gemini is temporarily busy. Please try again shortly."
            )
        elif "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            st.warning(
                "Gemini quota has been reached. Check your API quota "
                "or try again after it resets."
            )
        else:
            st.error("Gemini request failed. Check your API settings.")

        return None


# -------------------- Message helpers --------------------

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
    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )
    render_message(st.session_state.messages[-1])


# -------------------- Summary helper --------------------

def build_conversation_summary():
    """Build a fresh summary from the latest conversation."""

    user_messages = [
        message["content"]
        for message in st.session_state.messages
        if message["role"] == "user"
        and message["kind"] == "text"
        and message["content"].strip()
    ]

    assistant_messages = [
        message["content"]
        for message in st.session_state.messages
        if message["role"] == "assistant"
        and message["kind"] == "text"
        and message["content"].strip()
    ]

    if not user_messages and not assistant_messages:
        return "Ask StyleSnap AI a question to create your summary."

    recent_user_messages = user_messages[-5:]
    recent_answers = assistant_messages[-5:]

    summary = [
        "👗 StyleSnap AI — Your Style Summary",
        "",
        f"Styling preference: {st.session_state.occasion}",
        "",
        "Your recent questions:",
    ]

    for question in recent_user_messages:
        summary.append(f"• {question}")

    summary.extend(["", "Styling recommendations:"])

    for answer in recent_answers:
        summary.append(f"• {answer}")

    return "\n".join(summary)


# -------------------- Onboarding --------------------

if not st.session_state.onboarded:
    st.markdown(
        """
        <div class="hero">
            <h1>👗 StyleSnap AI</h1>
            <p>Your personal AI outfit and color-matching assistant.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        "Describe an outfit or upload a photo to receive personalized "
        "styling ideas, matching colors, and accessory recommendations."
    )

    with st.form("onboarding_form"):
        name = st.text_input("Your name", max_chars=80)

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
                st.session_state.occasion = occasion
                st.session_state.chat = chat
                st.session_state.messages = []
                st.session_state.style_summary = ""
                st.session_state.onboarded = True
                st.rerun()

            except Exception as error:
                st.error("Could not start the chat. Check model access.")
                st.exception(error)

    st.stop()


# -------------------- Main page --------------------

left, right = st.columns([5, 2], vertical_alignment="center")

with left:
    st.markdown(
        """
        <div class="hero">
            <h1>👗 StyleSnap AI</h1>
            <p>Style ideas that fit your vibe.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    if st.button("📋 Create style summary", use_container_width=True):
        st.session_state.style_summary = build_conversation_summary()

st.caption(
    f"Hi {st.session_state.name} · "
    f"Styling preference: {st.session_state.occasion}"
)


# -------------------- Show summary --------------------

if st.session_state.style_summary:
    st.markdown("### Your StyleSnap Summary")

    st.caption(
        "Your summary refreshes from the latest conversation "
        "each time you click the button."
    )

    st.text_area(
        "Copy your summary",
        value=st.session_state.style_summary,
        height=250,
        key=f"summary_display_{len(st.session_state.messages)}",
    )

    st.info(
        "To share this summary, copy it and paste it into WhatsApp. "
        "This version does not send WhatsApp messages automatically."
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

            # Clear the displayed summary so the next click
            # creates a fresh one from the updated conversation.
            st.session_state.style_summary = ""

        st.rerun()


# -------------------- Footer --------------------

st.caption(
    "Style suggestions are subjective. Avoid sharing photos "
    "containing private or sensitive information."
)
