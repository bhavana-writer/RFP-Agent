from fastapi import APIRouter, HTTPException
from app.services.tavily_service import search_latest_news

router = APIRouter()

@router.get("/search-news/{account_name}")
async def get_latest_news(account_name: str):
    """
    Endpoint to fetch the latest news about a company using Tavily API.
    """
    try:
        print(f"Searching news for account: {account_name}")
        results = search_latest_news(account_name)

        if not results or results == "No relevant news found.":
            raise HTTPException(status_code=404, detail=f"No news found for account: {account_name}")

        return {"account_name": account_name, "news_results": results}
    except Exception as e:
        print(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")
