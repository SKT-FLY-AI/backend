# sk-O-vaqq3fH3RMr2OddqtEKXFH75HSXYNu-Xbyu4jsFHT3BlbkFJVTb5lyCsFD2CcR3cO4HEK2JH2DEjD5bjc90Nws_iwA

from dotenv import load_dotenv
import os
import openai

os.environ

os.environ["OPENAI_API_KEY"] = "sk-O-vaqq3fH3RMr2OddqtEKXFH75HSXYNu-Xbyu4jsFHT3BlbkFJVTb5lyCsFD2CcR3cO4HEK2JH2DEjD5bjc90Nws_iwA"

print(os.environ.get("OPENAI_API_KEY"))

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

openai.api_key= api_key

completion = openai.ChatCompletion.creat(
    model = "gpt-3.5-turbo",
    messages = [
        {"role": "user", "content": "Hello!"}
    ]
)
