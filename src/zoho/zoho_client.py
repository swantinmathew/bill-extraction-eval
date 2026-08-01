import os
import time
import requests

_token_cache = {"access_token": None, "expires_at": 0}

def get_access_token():

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    res = requests.post("https://accounts.zoho.in/oauth/v2/token", data={
        "grant_type": "refresh_token",
        "client_id": os.getenv("ZOHO_CLIENT_ID"),
        "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
        "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN"),
    })
    res.raise_for_status()
    data = res.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 60  # refresh 1 min early
    return _token_cache["access_token"]

def get_expense_accounts():
    token = get_access_token()
    org_id = os.getenv("ZOHO_ORG_ID")
    res = requests.get(
        f"https://www.zohoapis.in/books/v3/chartofaccounts?organization_id={org_id}",
        headers={"Authorization": f"Zoho-oauthtoken {token}"}
    )
    return res.json()

def create_expense(bill_data: dict, account_id: str):
    token = get_access_token()
    org_id = os.getenv("ZOHO_ORG_ID")

    url = f"https://www.zohoapis.in/books/v3/expenses?organization_id={org_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    payload = {
        "account_id": account_id,
        "date": bill_data.get("date") or "2026-01-01",
        "amount": bill_data.get("amount") or 0,
        "vendor_name": bill_data.get("vendor"),
        "reference_number": bill_data.get("invoice_number"),
        "currency_code": bill_data.get("currency") or "INR",
    }

    res = requests.post(url, headers=headers, json=payload)
    return res.json()