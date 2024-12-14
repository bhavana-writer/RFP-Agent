from fastapi import APIRouter, HTTPException
from app.services.google_trends_service import GoogleTrendsService

router = APIRouter()

@router.get("/interest-over-time")
async def get_interest_over_time(query: str, date_range: str = "today 12-m", geo: str = ""):
    """
    Fetch interest over time for a query.
    """
    try:
        data = GoogleTrendsService.interest_over_time(query, date_range, geo)
        return {"interest_over_time": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/related-topics")
async def get_related_topics(query: str, date_range: str = "today 12-m", geo: str = ""):
    """
    Fetch related topics for a query.
    """
    try:
        data = GoogleTrendsService.related_topics(query, date_range, geo)
        return {"related_topics": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/related-queries")
async def get_related_queries(query: str, date_range: str = "today 12-m", geo: str = ""):
    """
    Fetch related queries for a query.
    """
    try:
        data = GoogleTrendsService.related_queries(query, date_range, geo)
        return {"related_queries": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
