import os
import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://idm.mercantilandina.com.ar/auth/realms/meran/protocol/openid-connect/token"

payload = {
    "grant_type": "password",
    "client_id": os.getenv("MA_CLIENT_ID"),
    "username": os.getenv("MA_USERNAME"),
    "password": os.getenv("MA_PASSWORD"),
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

print("Intentando login contra Keycloak...")

response = requests.post(URL, data=payload, headers=headers)

print("Status:", response.status_code)

try:
    data = response.json()
except:
    print(response.text)
    raise

if response.status_code != 200:
    print("Login falló:")
    print(data)
else:
    print("\nLogin exitoso\n")

    print("Access token:")
    print(data["access_token"][:80] + "...")

    print("\nRefresh token:")
    print(data["refresh_token"][:80] + "...")

    print("\nExpira en:", data["expires_in"], "segundos")