from fastapi import Depends, Request, HTTPException, status
from supabase import Client, create_client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

async def get_current_user(request: Request):
    session_token = request.cookies.get("user_session")
    if not session_token:
        return None
    try:
        user = supabase.auth.get_user(session_token)
        return user
    except Exception:
        return None

def protected_route(func):
    async def wrapper(request: Request, user: dict = Depends(get_current_user)):
        if not user:
            return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
        return await func(request, user)
    return wrapper