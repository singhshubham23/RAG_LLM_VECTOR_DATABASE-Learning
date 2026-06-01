
import os
import re
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

def clean_spaced_text(text: str) -> str:
    """
    Cleans up redundant white spaces while leaving core text structural layouts intact.
    """
    if not text:
        return ""
    # Replaces structural clusters of tabs/multiple spaces with a single clear space
    cleaned = re.sub(r'[ \t]+', ' ', text)
    return cleaned

def load_and_chunk_pdf(file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found : {file_path}")
        return []
    
    try:
        print(f"Loading...document: {file_path}")

        if file_path.lower().endswith('.pdf'):
            # PyMuPDFLoader handles resumes and multi-column text incredibly well natively
            loader = PyMuPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)

        documents = loader.load()

        # If it successfully reads pages, clean them up
        for doc in documents:
            doc.page_content = clean_spaced_text(doc.page_content)

        # Chunks size 400 with 50 character overlap is great for resume matching
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400, 
            chunk_overlap=50, 
            length_function=len
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"Document loaded and split into {len(chunks)} chunks.")

        for i, chunk in enumerate(chunks):
            print(f"---Chunk {i+1}---")
            print(chunk.page_content.strip())
            print(f"Metadata: {chunk.metadata}")
            print("\n") 

        return chunks

    except Exception as e:
        print(f"An error occurred while processing the document: {e}")
        return []
    
if __name__ == "__main__":
    load_and_chunk_pdf("_my_resume_.pdf")