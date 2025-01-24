import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()



class FireflyService:
    """
    Service for interacting with Firefly APIs.
    """

    def __init__(self):
        """
        Initialize the Firefly API client using the client ID and secret from the environment variables.
        """
        self.client_id = os.getenv('FIREFLY_CLIENT_ID')
        self.client_secret = os.getenv('FIREFLY_CLIENT_SECRET')
        self.base_url = "https://api.firefly.adobe.com"  # Example base URL, adjust as needed

    def call_firefly_api(self, endpoint: str, payload: Dict[str, Any]) -> Dict:
        """
        Call the Firefly API with the specified endpoint and payload.

        :param endpoint: The API endpoint to call.
        :param payload: The payload to send in the request.
        :return: The response from the Firefly API or an error message.
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = {
                "Authorization": f"Bearer {self._get_access_token()}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _get_access_token(self) -> str:
        """
        Obtain an access token for the Firefly API.

        :return: The access token.
        """
        token_url = 'https://ims-na1.adobelogin.com/ims/token/v3'
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'openid,AdobeID,session,additional_info,read_organizations,firefly_api,ff_apis'
        }

        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        print("Access Token Retrieved")
        return token_data['access_token']

    def generate_image(self, prompt: str) -> Dict:
        """
        Generate an image from a text prompt using the Firefly API.

        :param prompt: The text prompt to generate an image.
        :return: The response from the Firefly API or an error message.
        """
        try:
            access_token = self._get_access_token()
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-api-key': self.client_id,
                'Authorization': f'Bearer {access_token}'
            }

            data = {
                'prompt': prompt
            }

            response = requests.post(
                'https://firefly-api.adobe.io/v3/images/generate',
                headers=headers,
                json=data
            )
            response.raise_for_status()
            job_response = response.json()
            print("Generate Image Response:", job_response)
            return job_response
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Test the generate_image function
    firefly_service = FireflyService()
    prompt = "a realistic illustration of a cat coding"
    result = firefly_service.generate_image(prompt)
    print("Test Result:", result)
