import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()






def main():
    #Test OpenAI
    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        print("Sending request to Groq...")
        response = llm.invoke("Say 'Setup complete, I am ready to learn!'")
        
        print(f"\nAI Response: {response.content}")
        print("\n✅ Success! You are running high-end LLMs for $0.00.")
        
    except Exception as e:
        print(f"Error testing ChatGroq: {e}")
        return


    print("Setup complete!")


if __name__ == "__main__":
    main()
