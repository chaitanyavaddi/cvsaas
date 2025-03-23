# from fastapi import FastAPI, Depends
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from app.auth.routes import auth_router, home_router
# from app.dashboard.routes import dashboard_router
# from app.users.routes import users_router
# from utils.auth import get_current_user
from fastapi.middleware.gzip import GZipMiddleware

# app = FastAPI()

# app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# app.add_middleware(GZipMiddleware, minimum_size=1000)

# # CORS configuration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(home_router, tags=["auth"])
# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])
# app.include_router(users_router, prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import logging

# Import routers
from app.interviews.routes import router as interviews_router
from app.students.routes import router as students_router
from app.batches.routes import router as batches_router
from app.results.routes import router as results_router
from app.webhooks.routes import router as webhook_router

# Import auth routes
from app.auth.routes import auth_router
from app.auth.routes import home_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)


app = FastAPI(title="AI Interview Platform")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")

app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(home_router, tags=["home"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(interviews_router, prefix="/interviews", tags=["interviews"])
app.include_router(students_router, prefix="/students", tags=["students"])
app.include_router(batches_router, prefix="/batches", tags=["batches"])
app.include_router(results_router, prefix="/results", tags=["results"])
app.include_router(webhook_router, prefix="/api", tags=["api"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)