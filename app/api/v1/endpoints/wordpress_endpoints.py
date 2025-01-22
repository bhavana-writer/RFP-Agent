from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from app.services.wordpress_service import WordPressService

router = APIRouter()
wordpress_service = WordPressService()

class ArticleCreate(BaseModel):
    title: str
    content: str
    status: str = 'publish'
    excerpt: Optional[str] = None
    categories: Optional[List[int]] = None
    tags: Optional[List[int]] = None
    format: str = 'standard'
    featured_media: Optional[int] = None
    comment_status: str = 'open'
    ping_status: str = 'open'

    class Config:
        schema_extra = {
            "example": {
                "title": "My New Article",
                "content": "This is the content of my article",
                "status": "publish",
                "excerpt": "Article excerpt",
                "categories": [1, 2],
                "tags": [3, 4],
                "format": "standard",
                "comment_status": "open",
                "ping_status": "open"
            }
        }

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    excerpt: Optional[str] = None

@router.post("/articles")
async def create_article(article: ArticleCreate):
    """Create a new WordPress article"""
    try:
        result = await wordpress_service.create_article(
            title=article.title,
            content=article.content,
            status=article.status,
            excerpt=article.excerpt,
            categories=article.categories,
            tags=article.tags
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/{post_id}")
async def get_article(post_id: int):
    """Get a specific article by ID"""
    try:
        return await wordpress_service.get_article(post_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Article not found: {str(e)}")

@router.get("/articles")
async def get_articles(
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None
):
    """Get a list of articles with optional search and pagination"""
    try:
        return await wordpress_service.get_articles(
            page=page,
            per_page=per_page,
            search=search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/articles/{post_id}")
async def update_article(post_id: int, article: ArticleUpdate):
    """Update an existing article"""
    try:
        return await wordpress_service.update_article(
            post_id=post_id,
            title=article.title,
            content=article.content,
            status=article.status,
            excerpt=article.excerpt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 