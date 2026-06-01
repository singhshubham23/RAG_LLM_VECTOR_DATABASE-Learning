import os
from dotenv import load_dotenv
from groq import Groq

# 1. Load environment variables
load_dotenv()

# 2. Grab the API key
api_key = os.getenv("GROQ_API_KEY")

# 3. Simple safety check
if not api_key:
    raise ValueError(
        "GROQ_API_KEY is missing! Make sure your .env file is saved and the first line is a comment (#)."
    )

# 4. Initialize the Native Groq Client
client = Groq(api_key=api_key)

# 5. Create the completion (Your way)
try:
    conversation = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of Bulgaria?"},
        ],
    )

    # 6. Print the result
    print(f"Assistant: {conversation.choices[0].message.content}")

except Exception as e:
    print(f"An error occurred: {e}")
