# from fastapi import APIRouter, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from utils.auth import protected_route

# dashboard_router = APIRouter()
# templates = Jinja2Templates(directory="templates")

# @dashboard_router.get("/", response_class=HTMLResponse)
# @protected_route
# async def dashboard(request: Request, user: dict):
#     return templates.TemplateResponse("/dashboard/dashboard.html", {"request": request, "user": user.user})


# @dashboard_router.get("/profile", response_class=HTMLResponse)
# @protected_route
# async def dashboard_profile(request: Request, user: dict):
#     return templates.TemplateResponse("/dashboard/profile.html", {"request": request, "user": user.user})


# @dashboard_router.get("/billing", response_class=HTMLResponse)
# @protected_route
# async def dashboard_profile(request: Request, user: dict):
#     return templates.TemplateResponse("/dashboard/billing.html", {"request": request, "user": user.user})


from functools import lru_cache
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.auth import protected_route
from typing import Optional
from starlette import status

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Cache template responses
@lru_cache(maxsize=20)
def get_template_response(template_name: str):
    return templates.get_template(template_name)

@dashboard_router.get("/", response_class=HTMLResponse)
@protected_route
async def dashboard(request: Request):
    try:
        template = get_template_response("dashboard/dashboard.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "user": request.state.user.user
            })
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading dashboard"
        )

@dashboard_router.get("/profile", response_class=HTMLResponse)
@protected_route
async def profile(request: Request):
    try:
        template = get_template_response("dashboard/profile.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "user": request.state.user.user
            })
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading profile"
        )

@dashboard_router.get("/billing", response_class=HTMLResponse)
@protected_route
async def billing(request: Request):
    try:
        template = get_template_response("dashboard/billing.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "user": request.state.user.user
            })
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading billing page"
        )