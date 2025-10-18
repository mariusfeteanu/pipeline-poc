import urllib

import streamlit as st
from openai import OpenAI
from weaviate import ConnectionParams, ProtocolParams, WeaviateClient

WEAVIATE_HTTP = {"host": "weaviate", "port": 8080, "secure": False}
WEAVIATE_GRPC = {"host": "weaviate", "port": 50051, "secure": False}
CLASS_NAME = "DocumentChunk"
EMBED_MODEL = "text-embedding-3-small"

st.title("Mini RAG Playground")
query = st.text_area("Ask a question:", placeholder="Type your question here...")
top_k = st.slider("Number of results", 1, 10, 3)

if st.button("Search") and query.strip():
    st.write("Searching...")

    client_openai = OpenAI()
    query_embedding = (
        client_openai.embeddings.create(model=EMBED_MODEL, input=query)
        .data[0]
        .embedding
    )

    with WeaviateClient(
        connection_params=ConnectionParams(
            http=ProtocolParams(**WEAVIATE_HTTP),
            grpc=ProtocolParams(**WEAVIATE_GRPC),
        )
    ) as wclient:
        collection = wclient.collections.get(CLASS_NAME)
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=top_k,
            return_properties=[
                "text",
                "embedding_model",
                "embedding_dim",
                "bucket",
                "key",
                "file_type",
                "metadata_title",
                "metadata_author",
                "metadata_subject",
            ],
        )

    st.subheader("Top matches:")
    for i, obj in enumerate(results.objects):
        props = obj.properties

        bucket = props.get("bucket")
        key = props.get("key")
        file_type = props.get("file_type")
        title = props.get("metadata_title")
        author = props.get("metadata_author")
        subject = props.get("metadata_subject")
        link = (
            f"http://localhost:9090/browser/{bucket}/{urllib.parse.quote(key, safe='')}"
        )
        st.markdown(
            f"**{i+1}. [{title or key.split('/')[-1] if key else '???'}]({link})**"
        )
        if author:
            st.markdown(f"*Author:* {author}")
        if subject:
            st.markdown(f"*Subject:* {subject}")
        if file_type:
            st.markdown(f"*File type:* {file_type}")
        st.write(props.get("text", "[no text]"))
        st.divider()
