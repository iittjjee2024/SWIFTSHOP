from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = "http://localhost:8000/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def auth_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    return {
        "email": user_info["email"],
        "name": user_info["name"]
    }