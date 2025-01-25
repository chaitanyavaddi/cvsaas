from fastapi import FastAPI, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize FastAPI app
app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Authentication Dependency
async def get_current_user(request: Request):
    """Check if user is authenticated"""
    session_token = request.cookies.get("user_session")
    
    if not session_token:
        return None
    
    try:
        # Verify the session with Supabase
        user = supabase.auth.get_user(session_token)
        return user
    except Exception:
        return None

def protected_route(func):
   async def wrapper(request: Request, user: dict = Depends(get_current_user)):
       if not user:
           return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
       return await func(request, user)
   return wrapper

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render the signup page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...)
):
    """Handle user login"""
    try:
        # Attempt to sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # If login successful, redirect to dashboard
        redirect = RedirectResponse(
            url="/dashboard", 
            status_code=status.HTTP_303_SEE_OTHER
        )
        # Set session cookie 
        redirect.set_cookie(
            key="user_session", 
            value=response.session.access_token,
            httponly=True,
            secure=True,
            samesite='lax'
        )
        return redirect
    
    except Exception as e:
        # Handle login errors
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid credentials"
        })

@app.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle user signup with auto-login"""
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request, 
            "error": "Passwords do not match"
        })
    
    try:
        # Create user in Supabase
        signup_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # Immediately sign in the user
        login_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Redirect to dashboard with session token
        redirect = RedirectResponse(
            url="/dashboard", 
            status_code=status.HTTP_303_SEE_OTHER
        )
        redirect.set_cookie(
            key="user_session", 
            value=login_response.session.access_token,
            httponly=True,
            secure=True,
            samesite='lax'
        )
        return redirect
    
    except Exception as e:
        return templates.TemplateResponse("signup.html", {
            "request": request, 
            "error": str(e)
        })

@app.get("/dashboard", response_class=HTMLResponse)
@protected_route
async def dashboard(request: Request, user: dict):
   """Render the dashboard page"""
   return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/logout")
async def logout():
    """Handle user logout"""
    # Redirect to login and clear session
    response = RedirectResponse(url="/")
    response.delete_cookie("user_session")
    return response

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)