import io
import os
from typing import Tuple

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
) -> tuple[list[str], list[tuple[str, str]]]:
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
    return list(docs.values()), list(docs.keys())


def build_context(
    use_chunks: bool, use_documents: bool, query: str, top_k: int
) -> tuple[str, int, int, list[tuple[str, str]]]:
    if not (use_chunks or use_documents):
        return "", 0, 0, []
    embedding = get_query_embedding(query)
    texts: list[str] = []
    doc_refs: list[tuple[str, str]] = []
    with WeaviateClient(
        connection_params=ConnectionParams(
            http=ProtocolParams(host="weaviate", port=8080, secure=False),
            grpc=ProtocolParams(host="weaviate", port=50051, secure=False),
        )
    ) as wclient:
        collection = wclient.collections.get("DocumentChunk")
        if use_chunks:
            chunks = retrieve_chunks(collection, embedding, top_k)
            texts.extend(chunks)
        else:
            chunks = []
        if use_documents:
            s3_client = get_s3_client()
            docs, doc_refs = retrieve_documents(collection, embedding, top_k, s3_client)
            texts.extend(docs)
        else:
            docs = []
    return "\n".join(texts), len(chunks), len(docs), doc_refs


def chat(prompt: str, context: str) -> str:
    messages: list[
        ChatCompletionUserMessageParam
        | ChatCompletionAssistantMessageParam
        | ChatCompletionSystemMessageParam
    ] = []
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    messages += st.session_state.messages  # type: ignore
    response = client.chat.completions.create(model=model, messages=messages)
    content = response.choices[0].message.content
    return content or "<<No Response>>"


def render_sidebar() -> Tuple[bool, bool, int]:
    with st.sidebar:
        st.markdown("### Retrieval Options")
        use_chunks = st.checkbox("Use Chunks", value=False)
        use_documents = st.checkbox("Use Documents", value=False)
        relevancy_k = st.slider("Top K", 1, 10, 3) if use_chunks else 3
    return use_chunks, use_documents, relevancy_k


def render_logs() -> None:
    with st.sidebar:
        st.divider()
        st.markdown("### Logs")
        if "log_info" in st.session_state:
            log = st.session_state["log_info"]
            st.write(f"Chunks used: {log.get('chunks', 0)}")
            st.write(f"Documents used: {log.get('documents', 0)}")
            st.write(f"Past messages: {log.get('messages', 0)}")
            log_links = log.get("links", [])
            if log_links:
                st.write("Documents:")
                for url in log_links:
                    st.markdown(f"- [{url}]({url})")
    return None


def main() -> None:
    st.title("LLM Chat with Retrieval")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    forget = st.button("Forget Conversation")
    if forget:
        st.session_state.messages = []
        st.rerun()

    use_chunks, use_documents, relevancy_k = render_sidebar()

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    with st.form("chat_form", clear_on_submit=True):
        prompt = st.text_area("Message:", placeholder="Type here...")
        submitted = st.form_submit_button("Send (Ctrl+Enter)")

    if submitted and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        context, n_chunks, n_docs, doc_refs = build_context(
            use_chunks, use_documents, prompt, relevancy_k
        )

        generated_links: list[str] = []
        if doc_refs:
            s3_client = get_s3_client()
            for bucket, key in doc_refs:
                link = (
                    s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": str(bucket), "Key": str(key)},
                        ExpiresIn=3600,
                    )
                    if bucket and key
                    else "#"
                ).replace("minio:9000", "localhost:9000")
                generated_links.append(link)

        reply = chat(prompt, context)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

        st.session_state["log_info"] = {
            "chunks": n_chunks,
            "documents": n_docs,
            "messages": len(st.session_state.messages),
            "links": generated_links,
        }

        st.rerun()

    render_logs()
    return None


if __name__ == "__main__":
    main()
