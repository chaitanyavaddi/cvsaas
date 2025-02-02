# from fastapi import APIRouter, Request, Form, HTTPException, status
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
# from utils.auth import get_current_user, protected_route
# from utils.auth import supabase

# auth_router = APIRouter()
# home_router = APIRouter()
# templates = Jinja2Templates(directory="templates")

# @home_router.get("/", response_class=HTMLResponse)
# async def home_page(request: Request):
#     return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

# @auth_router.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request):
#     user = await get_current_user(request)
#     if user:
#         return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
#     return templates.TemplateResponse("login.html", {"request": request})

# @auth_router.post("/login", response_class=HTMLResponse)
# async def login(request: Request, email: str = Form(...), password: str = Form(...)):
#     try:
#         response = supabase.auth.sign_in_with_password({"email": email, "password": password})
#         redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
#         redirect.set_cookie("user_session", response.session.access_token, httponly=True, secure=True, samesite='lax')
        
#         return redirect
#     except Exception as e:
#         return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

# @auth_router.get("/signup", response_class=HTMLResponse)
# async def signup_page(request: Request):
#     user = await get_current_user(request)
#     if user:
#         return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
#     return templates.TemplateResponse("signup.html", {"request": request})

# @auth_router.post("/signup", response_class=HTMLResponse)
# async def signup(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
#     if password != confirm_password:
#         return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match"})
#     try:
#         signup_response = supabase.auth.sign_up({"email": email, "password": password})
#         login_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
#         redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
#         redirect.set_cookie("user_session", login_response.session.access_token, httponly=True, secure=True, samesite='lax')
#         return redirect
#     except Exception as e:
#         return templates.TemplateResponse("signup.html", {"request": request, "error": str(e)})

# @auth_router.get("/logout")
# async def logout():
#     response = RedirectResponse(url="/")
#     response.delete_cookie("user_session")
#     return response

from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from functools import lru_cache
from utils.auth import get_current_user, get_supabase_client

auth_router = APIRouter()
home_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Cache template responses
@lru_cache(maxsize=20)
def get_template_response(template_name: str):
    return templates.get_template(template_name)

@home_router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_303_SEE_OTHER
    )

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(
            url="/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    template = get_template_response("login.html")
    return HTMLResponse(
        template.render({"request": request})
    )

@auth_router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    supabase = get_supabase_client()
    try:
        # Attempt login
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Create redirect response
        redirect = RedirectResponse(
            url="/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
        # Set secure cookie
        redirect.set_cookie(
            key="user_session",
            value=response.session.access_token,
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=3600  # 1 hour
        )
        
        return redirect
        
    except Exception as e:
        template = get_template_response("login.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Invalid credentials"
            })
        )

@auth_router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(
            url="/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    template = get_template_response("signup.html")
    return HTMLResponse(
        template.render({"request": request})
    )

@auth_router.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    # Validate passwords match
    if password != confirm_password:
        template = get_template_response("signup.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Passwords do not match"
            })
        )

    supabase = get_supabase_client()
    try:
        # Create user
        signup_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # Auto login after signup
        login_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Create redirect
        redirect = RedirectResponse(
            url="/dashboard",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
        # Set secure cookie
        redirect.set_cookie(
            key="user_session",
            value=login_response.session.access_token,
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=3600  # 1 hour
        )
        
        return redirect
        
    except Exception as e:
        template = get_template_response("signup.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": str(e)
            })
        )

@auth_router.get("/logout")
async def logout():
    response = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie("user_session")
    return response