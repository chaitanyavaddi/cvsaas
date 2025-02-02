# from fastapi import Depends, Request, HTTPException, status
# from fastapi.responses import RedirectResponse
# from supabase import Client, create_client
# from dotenv import load_dotenv
# import os

# # Load environment variables
# load_dotenv()

# # Initialize Supabase client
# supabase_url = os.getenv('SUPABASE_URL')
# supabase_key = os.getenv('SUPABASE_KEY')
# supabase: Client = create_client(supabase_url, supabase_key)

# async def get_current_user(request: Request):
#     session_token = request.cookies.get("user_session")
#     if not session_token:
#         return None
#     try:
#         user = supabase.auth.get_user(session_token)
#         return user
#     except Exception:
#         return None

# def protected_route(func):
#     async def wrapper(request: Request, user: dict = Depends(get_current_user)):
#         if not user:
#             return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
#         return await func(request, user)
#     return wrapper

from functools import lru_cache
from fastapi import Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from supabase import Client, create_client
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

@lru_cache()
def get_supabase_client() -> Client:
    """Cached Supabase client initialization"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    return create_client(supabase_url, supabase_key)

# Cache user data for 5 minutes
USER_CACHE = {}
CACHE_TTL = 300  # seconds

async def get_current_user(request: Request) -> Optional[dict]:
    session_token = request.cookies.get("user_session")
    if not session_token:
        return None
        
    # Check cache first
    cached_user = USER_CACHE.get(session_token)
    if cached_user:
        return cached_user
        
    try:
        supabase = get_supabase_client()
        user = supabase.auth.get_user(session_token)
        # Cache the result
        USER_CACHE[session_token] = user
        return user
    except Exception:
        return None

def protected_route(func):
    """Optimized protected route decorator"""
    async def wrapper(
        request: Request,
        user: Optional[dict] = Depends(get_current_user)
    ):
        if not user:
            return RedirectResponse(
                url="/auth/login",
                status_code=status.HTTP_303_SEE_OTHER
            )
        request.state.user = user  # Store user in request state
        return await func(request)
    return wrapper