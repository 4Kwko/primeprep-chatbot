import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

response = requests.get(
    "https://graph.instagram.com/v26.0/me",
    params={
        "fields": "user_id,username",
        "access_token": token
    },
    timeout=20
)

print(response.status_code)
print(response.text)