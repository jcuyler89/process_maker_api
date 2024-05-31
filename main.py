from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from typing import Union, List, Dict
import os
import logging
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def fetch_token():
    auth_url = os.getenv("AUTH_URL")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    async with AsyncClient() as client:
        response = await client.post(
            auth_url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
        token = response.json()["access_token"]
        return token


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/cases")
async def root():
    url = os.getenv("CASES_URL")
    token = await fetch_token()
    headers = {"Authorization": f"Bearer {token}"}
    amr_approvers = os.getenv("AMR_APPROVERS").split(",")

    async with AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Error occured: {str(e)}")
            return {"error": "An error occured while processing your request."} 
        data = response.json()
        logging.info(f"Data: {data}")
        filtered_data = [
            item for item in data
            if item["usr_uid"] in amr_approvers and item["app_status"] == "TO_DO"
        ]

        necessary_data = [
            {
                "case_number": item["app_number"],
                "case_status": item["app_status"],
                "user_uid": item["usr_uid"],
                "task_due_date": item["del_task_due_date"],
                "case_type": item["app_pro_title"],
                "approver_firstname": item["usr_firstname"],
                "approver_lastname": item["usr_lastname"],
            }
            for item in filtered_data
        ]

        return necessary_data
    
@app.get("/users")
async def get_users():
    url = os.getenv("USERS_URL")
    token = await fetch_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Error occured: {str(e)}")
            return {"error": "An error occured while processing your request."} 
        data = response.json()
        logging.info(f"Data: {data}")

        refined_data = [
            {
                "user_uid": item["usr_uid"],
                "username": item["usr_username"],
                "first_name": item["usr_firstname"],
                "last_name": item["usr_lastname"],
            }
            for item in data
        ]

        names_to_check = [
            ("Serene", "Wachli"),
            ("Tom", "Wachli"),
            ("Hany", "Louis"),
            ("Zoran", "Falkenstein"),
            ("Nick", "Johnson"),
            ("Leilani", "Rukhman"),
            ("John", "Brustad"),
            ("Nabil", "Hilal")
        ]

        group_presidents = [
            item for item in refined_data
            if (item["first_name"], item["last_name"]) in names_to_check 
        ]
      
        return group_presidents
    

@app.get("/users_with_cases")
async def get_users_with_cases():
    users = await get_users()
    cases = await root()

    for user in users:
        user_cases = [case for case in cases if case["user_uid"] == user["user_uid"]]
        user["cases"] = user_cases

    return users
