import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class RAG:

    def __init__(self):

        self.client = Groq(api_key=GROQ_API_KEY)
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db");
        self.collection = self.chroma_client.get_or_create_collection(name="rag_collection")

    def add_document(self, texts):
        embeddings = self.embed_model.encode(texts).tolist()
        ids = [str(i) for i in range(len(texts))]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts)
        print(f"Successfully added {len(texts)} documents to the vector store.")

    def query(self, user_question):
        """Given a user question, retrieve relevant documents and generate an answer using Groq."""

        query_embedding = self.embed_model.encode([user_question]).tolist()
        results = self.collection.query(query_embeddings=query_embedding, n_results=2)

        context = "".join(results['documents'][0])

        system_prompt = f"You are a helpful assistant. Use the following context to answer the question."
        user_prompt = f"Context: {context}\n\nQuestion: {user_question}\n\nAnswer:"

        completion = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.2
        )

        return completion.choices[0].message.content.strip()

if __name__ == "__main__":
    rag = RAG()
    if rag.collection.count() == 0:
        my_data = [
            "The project 'Aether' launch date is set for October 12, 2026.",
            "Team members for Aether include Sarah (Lead), Mike (Dev), and Elena (Design).",
            "The budget for the project is $50,000."
        ]
        rag.add_document(my_data)

    question = "Who is Sarah?"
    answer = rag.query(question)

    print(f"\nQuestion: {question}")
    print(f"AI Response: {answer}")

