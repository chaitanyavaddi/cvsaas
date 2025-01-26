from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.auth import protected_route

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@dashboard_router.get("/", response_class=HTMLResponse)
@protected_route
async def dashboard(request: Request, user: dict):
    return templates.TemplateResponse("/dashboard/dashboard.html", {"request": request, "user": user.user})


@dashboard_router.get("/profile", response_class=HTMLResponse)
@protected_route
async def dashboard_profile(request: Request, user: dict):
    return templates.TemplateResponse("/dashboard/profile.html", {"request": request, "user": user.user})

