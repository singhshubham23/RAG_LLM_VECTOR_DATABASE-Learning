import os
import chromadb
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Setup Environment
load_dotenv() 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model_name="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY)

client = chromadb.Client()

embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="my_docs",metadata={"hnsw:space": "cosine"})

def hybrid_query(user_query):
    # 2. Get LLM response
    query_vector = embedding_function.embed_query(user_query)
    vector_results = collection.query(query_embeddings=[query_vector], n_results=5)

    context_docs = vector_results['documents'][0]  if vector_results['documents'] else []
    context_str = "\n".join(context_docs)
    prompt = f"""
    Answer the question based ONLY on the context provided.
    Context: {context_str}
    Question: {user_query}
    """
    return llm.invoke(prompt)

if __name__ == "__main__":
    if collection.count() == 0:
        collection.add(
            documents=["Groq achieves low latency using a Deterministic Tensor Streaming architecture.", 
                       "ChromaDB is an open-source vector database for AI applications."],
            ids=["id1", "id2"]
        )
    response = hybrid_query("How does Groq achieve low latency?")
    print(response.content)    

