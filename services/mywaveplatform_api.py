import asyncio
import base64
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class MeRTApi:
    def __init__(self, base_url=None, username=None, password=None, api_key=None):
        self.base_url = base_url or os.getenv("PARLAY_BASE_URL")
        self.username = username or os.getenv("CYBERMED_USERNAME")
        self.password = password or os.getenv("CYBERMED_PASSWORD")
        self.api_key = api_key or os.getenv("CLINICAL_API_KEY")

    def get_basic_auth_header(self):
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = {"Authorization": f"Basic {encoded_credentials}"}

        if self.api_key:
            auth_header["x-api-key"] = self.api_key

        return auth_header

    async def login(self):
        auth_header = self.get_basic_auth_header()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/auth/api/v1/user",
                headers={**auth_header, "Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    bearer_token = response_data["message"]["IdToken"]
                    return {
                        "Authorization": f"Bearer {bearer_token}",
                        "x-api-key": self.api_key,
                    }
                else:
                    raise Exception("Login failed: " + await response.text())