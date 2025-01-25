from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.auth import protected_route
from .services import get_user_data

users_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@users_router.get("/profile", response_class=HTMLResponse)
@protected_route
async def user_profile(request: Request, user: dict):
    user_data = await get_user_data(user)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data})