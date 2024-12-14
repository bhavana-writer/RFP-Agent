from fastapi import APIRouter, HTTPException
from app.services.salesforce_service import SalesforceService

router = APIRouter()
salesforce_service = SalesforceService()

@router.get("/account/{account_id}")
async def get_account_information(account_id: str):
    """
    Fetch all associated data for an account by ID.
    """
    try:
        account_data = salesforce_service.get_account_data(account_id)
        if not account_data:
            raise HTTPException(status_code=404, detail=f"No data found for account ID {account_id}")
        return {"account_id": account_id, "account_data": account_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/accounts")
async def search_accounts(search_term: str):
    """
    Search for accounts in Salesforce based on a search term.
    """
    try:
        accounts = salesforce_service.search_accounts(search_term)
        if not accounts:
            raise HTTPException(status_code=404, detail="No accounts found for the given search term.")
        return {"search_term": search_term, "accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/contacts")
async def get_contacts(account_id: str):
    """
    Fetch all contacts related to a specific account.
    """
    try:
        contacts = salesforce_service.get_contacts_by_account(account_id)
        if not contacts:
            raise HTTPException(status_code=404, detail=f"No contacts found for account ID {account_id}")
        return {"account_id": account_id, "contacts": contacts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/opportunities")
async def get_opportunities(account_id: str):
    """
    Fetch all opportunities related to a specific account.
    """
    try:
        opportunities = salesforce_service.get_opportunities_by_account(account_id)
        if not opportunities:
            raise HTTPException(status_code=404, detail=f"No opportunities found for account ID {account_id}")
        return {"account_id": account_id, "opportunities": opportunities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/cases")
async def get_cases(account_id: str):
    """
    Fetch all cases related to a specific account.
    """
    try:
        cases = salesforce_service.get_cases_by_account(account_id)
        if not cases:
            raise HTTPException(status_code=404, detail=f"No cases found for account ID {account_id}")
        return {"account_id": account_id, "cases": cases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/{account_id}/tasks")
async def get_tasks(account_id: str):
    """
    Fetch all tasks related to a specific account.
    """
    try:
        tasks = salesforce_service.get_tasks_by_account(account_id)
        if not tasks:
            raise HTTPException(status_code=404, detail=f"No tasks found for account ID {account_id}")
        return {"account_id": account_id, "tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
