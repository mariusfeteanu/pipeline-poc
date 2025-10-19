import os

import streamlit as st
from openai import OpenAI

model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

st.title("LLM Chat")
prompt = st.text_area("Prompt:", placeholder="Type something...")

if st.button("Run") and prompt.strip():
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    st.write(response.choices[0].message.content)
