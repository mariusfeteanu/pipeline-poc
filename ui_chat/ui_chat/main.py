import io
import os

import boto3
import streamlit as st
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from PyPDF2 import PdfReader
from weaviate import WeaviateClient
from weaviate.collections import Collection
from weaviate.connect import ConnectionParams, ProtocolParams

model: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()

OBJECT_STORAGE_URL: str = os.environ["OBJECT_STORAGE_URL"]
OBJECT_STORAGE_USER: str = os.environ["OBJECT_STORAGE_USER"]
OBJECT_STORAGE_PASSWORD: str = os.environ["OBJECT_STORAGE_PASSWORD"]


def get_weaviate_collection() -> Collection:
    wclient = WeaviateClient(
        connection_params=ConnectionParams(
            http=ProtocolParams(host="weaviate", port=8080, secure=False),
            grpc=ProtocolParams(host="weaviate", port=50051, secure=False),
        )
    )
    return wclient.collections.get("DocumentChunk")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=OBJECT_STORAGE_URL,
        aws_access_key_id=OBJECT_STORAGE_USER,
        aws_secret_access_key=OBJECT_STORAGE_PASSWORD,
    )


def get_query_embedding(query: str) -> list[float]:
    return (
        client.embeddings.create(model="text-embedding-3-small", input=query)
        .data[0]
        .embedding
    )


def retrieve_chunks(
    collection: Collection, query_embedding: list[float], top_k: int
) -> list[str]:
    results = collection.query.near_vector(near_vector=query_embedding, limit=top_k)
    return [str(obj.properties["text"]) for obj in results.objects if obj]


def retrieve_documents(
    collection: Collection, query_embedding: list[float], top_k: int, s3_client
) -> list[str]:
    results = collection.query.near_vector(near_vector=query_embedding, limit=top_k)
    docs: dict[tuple[str, str], str] = {}
    for obj in results.objects:
        props = obj.properties
        bucket, key, ftype = props["bucket"], props["key"], props["file_type"]
        assert isinstance(bucket, str)
        assert isinstance(key, str)
        assert isinstance(ftype, str)
        if (bucket, key) not in docs:
            file = s3_client.get_object(Bucket=bucket, Key=key)
            body = file["Body"].read()
            if ftype == "pdf":
                reader = PdfReader(io.BytesIO(body))
                text = " ".join(page.extract_text() or "" for page in reader.pages)
                docs[(bucket, key)] = text
    return list(docs.values())


def build_context(mode: str, query: str, top_k: int) -> str:
    if mode == "none":
        return ""
    collection = get_weaviate_collection()
    embedding = get_query_embedding(query)
    if mode == "chunks":
        return "\n".join(retrieve_chunks(collection, embedding, top_k))
    if mode == "documents":
        s3_client = get_s3_client()
        return "\n".join(retrieve_documents(collection, embedding, top_k, s3_client))
    return ""


def chat(prompt: str, context: str) -> str:
    messages: list[
        ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionSystemMessageParam
    ] = []
    if context:
        messages.append(
            ChatCompletionSystemMessageParam(
                role="system", content=f"Context:\n{context}"
            )
        )
    messages += st.session_state.messages  # type: ignore
    response = client.chat.completions.create(model=model, messages=messages)
    content = response.choices[0].message.content
    return content or "<<No Response>>"


def main() -> None:
    st.title("LLM Chat with Retrieval")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    with st.sidebar:
        use_retrieval = st.checkbox("Use Retrieval", value=True)
        retrieval_mode = st.selectbox("Retrieval Mode", ["chunks", "documents", "none"])
        relevancy_k = st.slider("Top K", 1, 10, 3)

    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_area("Message:", placeholder="Type here...")
        submitted = st.form_submit_button("Send (Ctrl+Enter)")

    if submitted and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        context = build_context(
            retrieval_mode if use_retrieval else "none", prompt, relevancy_k
        )
        reply = chat(prompt, context)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)


if __name__ == "__main__":
    main()
