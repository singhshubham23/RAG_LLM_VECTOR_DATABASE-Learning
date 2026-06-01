import chromadb
import os
chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(name="file_search")


def similarity_search(file_path, query_text):

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks)

    results = collection.query(query_texts=[query_text], n_results=2)

    print(f"Searching for: {query_text}")
    for i in range(len(results['ids'][0])):
        print(f"ID: {results['ids'][0][i]}")
        print(f"Distance: {results['distances'][0][i]:.4f}")
        print(f"Document: {results['documents'][0][i]}")
        print("-" * 30)


similarity_search('example.txt', 'What is the village name?')