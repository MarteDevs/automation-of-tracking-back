import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

try:
    print(f"Testing connectivity with key: {os.environ.get('OPENAI_API_KEY')[:10]}...")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    print("✔ Connection successful!")
    print(f"Response: {resp.choices[0].message.content}")
except Exception as e:
    print(f"✖ Connection failed: {str(e)}")
