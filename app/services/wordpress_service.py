import requests
from typing import Optional, Dict, Any, List
from base64 import b64encode
from app.config import settings

class WordPressService:
    def __init__(self):
        print("Initializing WordPress Service")
        print(f"API URL: {settings.WORDPRESS_API_URL}")
        print(f"Username: {settings.WORDPRESS_USERNAME}")
        print(f"Password length: {len(settings.WORDPRESS_APP_PASSWORD)}")
        
        self.base_url = str(settings.WORDPRESS_API_URL)
        self.auth_header = self._get_auth_header()
        # Test the authentication and set working_auth_header
        self._test_and_set_auth()

    def _get_auth_header(self) -> Dict[str, str]:
        """Create the authentication header for WordPress API"""
        # Remove any quotes from the app password and join with no spaces
        app_password = settings.WORDPRESS_APP_PASSWORD.replace("'", "").replace('"', "").replace(" ", "")
        credentials = f'{settings.WORDPRESS_USERNAME}:{app_password}'
        token = b64encode(credentials.encode()).decode('ascii')
        
        print(f"Generated Authorization token: Basic {token}")
        
        return {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _test_and_set_auth(self):
        """Test different authentication methods and set the working one"""
        # Try Basic Auth first
        test_response = requests.get(
            f"{self.base_url}/posts",
            headers=self.auth_header,
            verify=True
        )
        print(f"Testing Basic Auth - Status: {test_response.status_code}")
        print(f"Response: {test_response.text[:200]}")  # Print first 200 chars of response

        if test_response.status_code == 200:
            self.working_auth_header = self.auth_header
            return

        # Try Bearer token if Basic Auth fails
        app_password = settings.WORDPRESS_APP_PASSWORD.replace("'", "").replace('"', "").replace(" ", "")
        bearer_header = {
            'Authorization': f'Bearer {app_password}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        test_response = requests.get(
            f"{self.base_url}/posts",
            headers=bearer_header,
            verify=True
        )
        print(f"Testing Bearer Auth - Status: {test_response.status_code}")
        print(f"Response: {test_response.text[:200]}")

        if test_response.status_code == 200:
            self.working_auth_header = bearer_header
            return

        # If both fail, try application password without spaces
        app_pass_header = {
            'Authorization': f'Basic {b64encode(f"{settings.WORDPRESS_USERNAME}:{app_password}".encode()).decode()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        test_response = requests.get(
            f"{self.base_url}/posts",
            headers=app_pass_header,
            verify=True
        )
        print(f"Testing App Password Auth - Status: {test_response.status_code}")
        print(f"Response: {test_response.text[:200]}")

        if test_response.status_code == 200:
            self.working_auth_header = app_pass_header
            return

        raise Exception("Could not establish working authentication method")

    async def create_article(
        self,
        title: str,
        content: str,
        status: str = 'publish',
        excerpt: Optional[str] = None,
        categories: Optional[List[int]] = None,
        tags: Optional[List[int]] = None,
        format: str = 'standard',
        featured_media: Optional[int] = None,
        comment_status: str = 'open',
        ping_status: str = 'open',
    ) -> Dict[str, Any]:
        """
        Create a new WordPress article using the REST API
        """
        payload = {
            'title': title,
            'content': content,
            'status': status,
            'format': format,
            'comment_status': comment_status,
            'ping_status': ping_status,
            'content_filtered': content
        }
        
        if excerpt:
            payload['excerpt'] = excerpt
        if categories:
            payload['categories'] = categories
        if tags:
            payload['tags'] = tags
        if featured_media:
            payload['featured_media'] = featured_media

        print(f"\nMaking POST request to: {self.base_url}/posts")
        print(f"Headers: {self.working_auth_header}")
        print(f"Payload: {payload}")

        response = requests.post(
            f"{self.base_url}/posts",
            json=payload,
            headers=self.working_auth_header,
            verify=True
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        try:
            response_data = response.json()
            print(f"Response body: {response_data}")
        except:
            print(f"Response text: {response.text}")

        response.raise_for_status()
        return response.json()

    async def get_article(self, post_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific article by ID
        """
        response = requests.get(
            f"{self.base_url}/posts/{post_id}",
            headers=self.auth_header
        )
        response.raise_for_status()
        return response.json()

    async def get_articles(
        self,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve a list of articles with optional search and pagination
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        if search:
            params['search'] = search

        response = requests.get(
            f"{self.base_url}/posts",
            params=params,
            headers=self.auth_header
        )
        response.raise_for_status()
        return response.json()

    async def update_article(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        status: Optional[str] = None,
        excerpt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing article
        """
        payload = {}
        if title:
            payload['title'] = title
        if content:
            payload['content'] = content
        if status:
            payload['status'] = status
        if excerpt:
            payload['excerpt'] = excerpt

        response = requests.post(
            f"{self.base_url}/posts/{post_id}",
            json=payload,
            headers=self.auth_header
        )
        response.raise_for_status()
        return response.json() 