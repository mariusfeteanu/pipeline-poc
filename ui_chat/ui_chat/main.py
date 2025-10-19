import os
import streamlit as st
from openai import OpenAI

model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

st.title("LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

with st.form("chat_form", clear_on_submit=True):
    prompt = st.text_area("Message:", placeholder="Type here...")
    submitted = st.form_submit_button("Send (Ctrl+Enter)")

if submitted and prompt.strip():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = client.chat.completions.create(
        model=model,
        messages=st.session_state.messages,
    )

    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)
