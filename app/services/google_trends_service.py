from serpapi import GoogleSearch
from app.config import settings
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GoogleTrendsService:
    """
    Service to interact with SerpAPI's Google Trends API.
    Provides functionalities to fetch interest over time, related topics, and related queries.
    """

    BASE_PARAMS = {
        "engine": "google_trends",
        "api_key": settings.SERP_API_KEY
    }

    @staticmethod
    def interest_over_time(query: str, date_range: str = "today 12-m", geo: str = "") -> Dict:
        """
        Fetches the interest over time for a query.

        :param query: The keyword or topic to search (e.g., 'coffee').
        :param date_range: Time range for the data (e.g., 'today 12-m' for the past 12 months).
        :param geo: Geographical location (e.g., 'US' for the United States). Default is Worldwide.
        :return: Dictionary containing interest over time data.
        """
        params = {
            **GoogleTrendsService.BASE_PARAMS,
            "q": query,
            "data_type": "TIMESERIES",
            "date": date_range,
            "geo": geo
        }
        logger.info(f"Fetching interest over time for query: {query}, date_range: {date_range}, geo: {geo}")
        search = GoogleSearch(params)
        return search.get_dict().get("interest_over_time", {})

    @staticmethod
    def related_topics(query: str, date_range: str = "today 12-m", geo: str = "") -> Dict:
        """
        Fetches related topics for a query.

        :param query: The keyword or topic to search (e.g., 'coffee').
        :param date_range: Time range for the data (e.g., 'today 12-m' for the past 12 months).
        :param geo: Geographical location (e.g., 'US' for the United States). Default is Worldwide.
        :return: Dictionary containing related topics data.
        """
        params = {
            **GoogleTrendsService.BASE_PARAMS,
            "q": query,
            "data_type": "RELATED_TOPICS",
            "date": date_range,
            "geo": geo
        }
        logger.info(f"Fetching related topics for query: {query}, date_range: {date_range}, geo: {geo}")
        search = GoogleSearch(params)
        return search.get_dict().get("related_topics", {})

    @staticmethod
    def related_queries(query: str, date_range: str = "today 12-m", geo: str = "") -> Dict:
        """
        Fetches related queries for a query.

        :param query: The keyword or topic to search (e.g., 'coffee').
        :param date_range: Time range for the data (e.g., 'today 12-m' for the past 12 months).
        :param geo: Geographical location (e.g., 'US' for the United States). Default is Worldwide.
        :return: Dictionary containing related queries data.
        """
        params = {
            **GoogleTrendsService.BASE_PARAMS,
            "q": query,
            "data_type": "RELATED_QUERIES",
            "date": date_range,
            "geo": geo
        }
        logger.info(f"Fetching related queries for query: {query}, date_range: {date_range}, geo: {geo}")
        search = GoogleSearch(params)
        return search.get_dict().get("related_queries", {})
