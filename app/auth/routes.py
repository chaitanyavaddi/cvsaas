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
        
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        html_response = HTMLResponse(
            content="",
            status_code=200,
            headers={
                "HX-Redirect": "/dashboard"
            }
        )

        # Set cookie
        html_response.set_cookie(
            key="user_session",
            value=response.session.access_token,
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=3600
        )

        return html_response

    except Exception as e:
        # For errors, return the form with error messages
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

        html_response = HTMLResponse(
            content='', 
            status_code=200, 
            headers={
                "HX-Redirect": "/dashboard"
            }
        )

        html_response.set_cookie(
            key="user_session",
            value=login_response.session.access_token,
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=3600
        )
        
        return html_response
        
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
