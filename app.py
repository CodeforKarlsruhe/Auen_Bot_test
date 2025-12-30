import streamlit as st

from src.data_loader import KnowledgeBase
from src.bot import AuenBot
import streamlit as st
import hmac

st.set_page_config(page_title="AuenBot", page_icon="🌿")

@st.cache_resource
def load_bot():
    kb = KnowledgeBase.load()
    bot = AuenBot(kb)
    return bot



def check_password() -> bool:
    """Simple password gate using st.secrets['APP_PASSWORD']."""
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if st.session_state.auth:
        return True

    st.title("🔒 AuenBot Login")

    pwd = st.text_input("Passwort", type="password")

    if st.button("Login"):
        # Konstantzeit-Vergleich
        if "APP_PASSWORD" in st.secrets and hmac.compare_digest(pwd, st.secrets["APP_PASSWORD"]):
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")

    return False

if not check_password():
    st.stop()

bot = load_bot()

if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

st.title("🌿 AuenBot")
st.caption("Frage mich zu Tieren & Pflanzen – z.B. „Habitat der Blauschwarzen Holzbiene“.")

# Chat-Verlauf
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ich bin KarlA 🙂 Was möchtest du über Tiere oder Pflanzen wissen?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Schreib deine Frage hier …")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = bot.answer(prompt)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
