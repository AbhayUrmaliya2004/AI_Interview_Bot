# mock_interview_frontend.py
import streamlit as st
from langchain_core.messages import HumanMessage
from mock_interview_backend import get_chatbot
from dotenv import load_dotenv
import speech_recognition as sr

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
recognizer.pause_threshold = 4 # 5 seconds pause may be there while speaking

mic_list = sr.Microphone.list_microphone_names()
if not mic_list:
    st.error("⚠️ No microphone detected. Connect one and refresh.")
    st.stop()

mic_device_index = mic_list.index(
    st.sidebar.selectbox("Select Microphone:", mic_list, index=0)
)


def capture_speech():
    try:
        with sr.Microphone(device_index=mic_device_index) as source:
            st.info("🎤 Listening... Speak now (you have 5 seconds)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            # Limit listening so user knows it will stop
            try:
                audio = recognizer.listen(source, timeout=7)
                st.info("⏳ Processing your answer...")
            except sr.WaitTimeoutError:
                st.warning("No speech detected within 3 seconds.")
                return None

        try:
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I couldn't understand what you said.")
        except sr.RequestError:
            st.error("API unavailable or network error.")
    except Exception as e:
        st.error(f"Microphone error: {e}")
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

    # 🔄 Generate next question automatically and if not satisfied give user the hint to the answer or
    # try asking the new question to work on this 

# -------------------- UI BUTTONS --------------------
if st.button("🎙️ Answer with Voice"):
    speech_text = capture_speech()
    if speech_text:
        handle_input(speech_text)
        st.rerun()  # 🔄 This will refresh UI with correct order
