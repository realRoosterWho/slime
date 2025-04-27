from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-4o",
    input="讲一个关于独角兽的三句话中文睡前故事。"
)

print(response.output[0].content[0].text)