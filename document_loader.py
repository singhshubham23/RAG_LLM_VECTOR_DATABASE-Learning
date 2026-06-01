import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def load_and_chunk_document(file_path: str):
    # Check for file existance
    if not os.path.exists(file_path):
        print(file_error := f"File not found: {file_path}")
        return []

    # loading the document
    try:
        print(f"Loading document: {file_path}")
        loader = TextLoader(file_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=150, chunk_overlap=20, length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Document loaded and split into {len(chunks)} chunks.")

        print(f"Successfuly split into chunks")

        for i, chunk in enumerate(chunks):
            print(f"---Chunk {i+1}---")
            print(chunk.page_content)
            print("\n")

        return chunks
    except Exception as e:
        print(f"An error occured while processing the : {e}")
        return []

if __name__ == "__main__":
    sample_file = "my_learning_notes.txt"
    with open(sample_file, "w") as f:
        f.write(
                "LangChain is a framework designed to simplify the creation of applications using large language models. "
                "Document loaders are the first step in the RAG (Retrieval-Augmented Generation) pipeline. "
                "They bring data from various sources like PDFs, TXT files, and websites into your application. "
                "Once loaded, text splitters break the content down so it fits nicely into the model's context window."
        )

    load_and_chunk_document(sample_file)

    if os.path.exists(sample_file):
         os.remove(sample_file)
         print("🧹 Temporary test file cleaned up.")



