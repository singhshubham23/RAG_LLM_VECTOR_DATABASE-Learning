import chromadb
chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(name="my_collection")

documents = [
    {"id": "doc1", "text": "This is the first document."},
    {"id": "doc2", "text": "This is the second document."},
    {"id": "doc3", "text": "This is the third document."}
]

for doc in documents:
    collection.add( ids=[doc["id"]], documents=[doc["text"]] )

query_text= "What is the content of the first document?"

results = collection.query(
    query_texts=[query_text],
    n_results=3,
)

#for better readability, we can print the results in a more structured way
for i in range(len(results['ids'][0])):
    print(f"ID: {results['ids'][0][i]}")
    print(f"Distance: {results['distances'][0][i]:.4f}")
    print(f"Document: {results['documents'][0][i]}")
    print("-" * 20)

