# mock_interview_frontend.py
import streamlit as st
from langchain_core.messages import HumanMessage
from mock_interview_backend import get_chatbot
from dotenv import load_dotenv
import speech_recognition as sr
import os
import tempfile

load_dotenv()
st.set_page_config(page_title="AI Interview BOT", layout="centered")
st.title("🎙️ AI Mock Interview BOT")

# -------------------- INITIALIZE --------------------
if "chatbot" not in st.session_state:
    st.session_state.chatbot, st.session_state.checkpointer = get_chatbot()

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

# -------------------- ROLE / DOMAIN / LEVEL SELECTION --------------------
with st.sidebar:
    st.header("Candidate Profile")
    st.session_state["role"] = st.selectbox("Select Role", [
        "Software Engineer", "Web Developer", "Frontend Developer",
        "Backend Developer", "AI/ML Engineer", "Data Scientist"
    ])
    st.session_state["domain"] = st.selectbox("Select Domain", [
        "SDE", "Web Development", "Frontend",
        "Backend", "AI/ML", "Data Science"
    ])
    st.session_state["level"] = st.selectbox("Select Level", [
        "Entry Level", "Mid Level", "Senior Level"
    ])

# -------------------- MICROPHONE DROPDOWN --------------------
recognizer = sr.Recognizer()
recognizer.pause_threshold = 4  # 5 seconds pause may be there while speaking

# mic_list and device selection are skipped for cloud deployment
# These lines are retained only for local reference (won't affect cloud)
mic_list = ["Browser Microphone"]
mic_device_index = 0

# -------------------- CAPTURE SPEECH --------------------

def capture_speech():
    """Capture speech both locally (with Microphone) and on cloud (browser input)"""
    
    # Cloud version: use browser mic
    try:
        audio_data = st.audio_input("🎤 Speak your answer here (record from browser)")
        if not audio_data:
            st.warning("Please record your voice to continue.")
            return None

        st.info("⏳ Processing your answer...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data.read())
            tmp_path = tmp_file.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        st.success(f"You said: {text}")
        return text

    except Exception as e:
        st.error(f"Cloud audio processing error: {e}")
        return None


# -------------------- DISPLAY CHAT HISTORY --------------------
for msg in st.session_state["message_history"]:
    with st.chat_message(msg["role"]):
        st.text(msg["content"])

# -------------------- HANDLE INPUT --------------------
def handle_input(user_input):
    """Send input to chatbot and update history."""
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    config = {"configurable": {"thread_id": "1"}}
    with st.chat_message("assistant"):
        response = st.write_stream(
            message_chunk.content for message_chunk, metadata in st.session_state['chatbot'].stream(
                {
                    "role": st.session_state["role"],
                    "domain": st.session_state["domain"],
                    "level": st.session_state["level"],
                    "messages": [HumanMessage(content=user_input)]
                },
                config=config,
                stream_mode="messages"
            )
        )
        st.session_state["message_history"].append({"role": "assistant", "content": response})

# -------------------- UI BUTTONS --------------------
if st.button("🎙️ Answer with Voice"):
    speech_text = capture_speech()
    if speech_text:
        handle_input(speech_text)
        st.rerun()  # 🔄 Refresh UI with updated chat history
