import os
from dotenv import load_dotenv
import psycopg2
from groq import Groq
from sentence_transformers import SentenceTransformer

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DB_URL = os.getenv("SUPABASE_DB_URL")

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    db_conn = psycopg2.connect(DB_URL)
except Exception as e:
    print(f"Error initializing resources: {e}")
    exit(1)


def get_semantic_response(user_query):
    embedding = model.encode(user_query).tolist()
    query_vec_str = "[" + ",".join(map(str, embedding)) + "]"

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT prompt, response, similarity FROM match_cache(%s, 0.90, 1)",
            (query_vec_str,),
        )
        cache_result = cur.fetchone()

        if cache_result:
            prompt, response, similarity = cache_result
            print(f"Cache hit with similarity {similarity:.2f}")
            return response
        print("Cache miss, querying Groq LLM...")

        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": user_query}],
            )
            llm_response = response.choices[0].message.content

            cur.execute(
                """
                INSERT INTO llm_cache(prompt, response, embedding)
                VALUES (%s, %s, %s::vector)
                """,
                (user_query, llm_response, query_vec_str),
            )
            db_conn.commit()

            return f"LLM Response: {llm_response}"

        except Exception as e:
            print(f"Error during LLM query: {e}")
            return "Sorry, something went wrong while processing your request."


if __name__ == "__main__":
    user_query = "Tell me the benefits of the Groq chip design."

    # Run twice to test cache logic
    print("--- First Call ---")
    print(get_semantic_response(user_query))

    print("\n--- Second Call (Should hit cache) ---")
    print(get_semantic_response(user_query))
