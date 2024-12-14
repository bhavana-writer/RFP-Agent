from tavily import TavilyClient
from app.config import settings
import logging

# Initialize logger
logger = logging.getLogger(__name__)

def search_latest_news(account_name: str) -> str:
    """
    Search for the latest news about a company using Tavily API.

    :param account_name: Name of the company to search for.
    :return: A formatted string of relevant news articles or related information.
    """
    try:
        if not settings.TAVILY_API_KEY:
            raise ValueError("Tavily API key not found in environment variables or configuration.")

        tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        query = f"Find all the latest news related to Generative AI strategy for {account_name}"
        response = tavily_client.search(query)

        # Check if response has results
        if not response or "results" not in response or not response["results"]:
            return "No relevant news found."

        # Extract and format relevant information
        formatted_results = []
        for result in response["results"]:
            title = result.get("title", "No Title")
            url = result.get("url", "No URL")
            content = result.get("content", "No Content")
            score = result.get("score", "No Score")

            # Format each result
            formatted_results.append(
                f"Title: {title}\nURL: {url}\nContent: {content}\nScore: {score}\n"
            )

        # Combine all formatted results into a single string
        return "\n---\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error in Tavily search: {e}")
        return f"Error occurred while searching for news: {str(e)}"
