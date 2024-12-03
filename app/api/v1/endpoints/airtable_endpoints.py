from fastapi import APIRouter, HTTPException
from app.services.airtable_service import AirtableService

router = APIRouter()
airtable_service = AirtableService()

@router.get("/records")
async def get_records():
    try:
        records = airtable_service.get_records()
        return {"records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/records")
async def create_record(data: dict):
    try:
        record = airtable_service.create_record(data)
        return {"record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
