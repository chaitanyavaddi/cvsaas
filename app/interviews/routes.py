from fastapi import APIRouter, Request, Form, HTTPException, status, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import os
from datetime import datetime
from typing import Dict, Any, List

from utils.auth import get_current_user, get_supabase_client, get_template_response
from utils.blend_ai import create_blend_session
from utils.prompts import create_interview_prompt, create_evaluation_prompt

router = APIRouter()
templates = Jinja2Templates(directory="templates")
API_CALLBACK_URL = os.environ.get("API_CALLBACK_URL", "http://localhost:8000/api")

# ----- CRUD Operations for Interviews -----

# READ - List all interviews
@router.get("/", response_class=HTMLResponse)
async def list_interviews(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get all interviews with additional data
    result = supabase.table("interview_responses").select(
        "id, student_id, template_id, status, scheduled_at, completed_at, overall_score"
    ).eq("created_by", user["id"]).execute()
    
    interviews = result.data
    
    # Get student names and template names
    if interviews:
        student_ids = [interview["student_id"] for interview in interviews]
        template_ids = [interview["template_id"] for interview in interviews]
        
        students_result = supabase.table("students").select("id, name").in_("id", student_ids).execute()
        templates_result = supabase.table("interview_templates").select("id, title").in_("id", template_ids).execute()
        
        students = {student["id"]: student["name"] for student in students_result.data}
        templates_dict = {template["id"]: template["title"] for template in templates_result.data}
        
        # Add student and template names to interviews
        for interview in interviews:
            interview["student_name"] = students.get(interview["student_id"], "Unknown")
            interview["template_name"] = templates_dict.get(interview["template_id"], "Unknown")
    
    template = get_template_response(templates, "interviews/list.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "interviews": interviews,
            "user": user
        })
    )

# READ - Get specific interview
@router.get("/{interview_id}", response_class=HTMLResponse)
async def view_interview(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get interview
    result = supabase.table("interview_responses").select("*").eq("id", interview_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = result.data[0]
    
    # Get student
    student_result = supabase.table("students").select("name, email").eq("id", interview["student_id"]).execute()
    student = student_result.data[0] if student_result.data else {"name": "Unknown", "email": "Unknown"}
    
    # Get template
    template_result = supabase.table("interview_templates").select("title, description, questions, duration_minutes").eq("id", interview["template_id"]).execute()
    template = template_result.data[0] if template_result.data else {"title": "Unknown", "description": "", "questions": [], "duration_minutes": 0}
    
    template_view = get_template_response(templates, "interviews/view.html")
    return HTMLResponse(
        template_view.render({
            "request": request,
            "interview": interview,
            "student": student,
            "template": template,
            "user": user
        })
    )

# CREATE - Show form to create a new interview
@router.get("/create", response_class=HTMLResponse)
async def create_interview_form(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get all students
    students_result = supabase.table("students").select("id, name").eq("created_by", user["id"]).execute()
    students = students_result.data
    
    # Get all templates
    templates_result = supabase.table("interview_templates").select("id, title").eq("created_by", user["id"]).execute()
    interview_templates = templates_result.data
    
    # Get all batches
    batches_result = supabase.table("batches").select("id, name").eq("created_by", user["id"]).execute()
    batches = batches_result.data
    
    template = get_template_response(templates, "interviews/create.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "students": students,
            "templates": interview_templates,
            "batches": batches,
            "user": user
        })
    )

# CREATE - Create a new interview
@router.post("/create", response_class=HTMLResponse)
async def create_interview(
    request: Request,
    student_id: str = Form(...),
    template_id: str = Form(...),
    trainer_name: str = Form(...),
    scheduled_at: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Create interview
    result = supabase.table("interview_responses").insert({
        "student_id": student_id,
        "template_id": template_id,
        "trainer_name": trainer_name,
        "scheduled_at": scheduled_at,
        "status": "scheduled",
        "created_by": user["id"]
    }).execute()
    
    if result.data:
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": "/interviews"}
        )
    else:
        template = get_template_response(templates, "interviews/create.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Failed to create interview",
                "user": user
            })
        )

# UPDATE - Update interview details
@router.post("/{interview_id}/update", response_class=HTMLResponse)
async def update_interview(
    request: Request,
    interview_id: str,
    trainer_name: str = Form(...),
    scheduled_at: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Check if interview exists and is owned by user
    check_result = supabase.table("interview_responses").select("id").eq("id", interview_id).eq("created_by", user["id"]).execute()
    
    if not check_result.data:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Only allow updates if interview is in scheduled status
    result = supabase.table("interview_responses").update({
        "trainer_name": trainer_name,
        "scheduled_at": scheduled_at
    }).eq("id", interview_id).eq("created_by", user["id"]).eq("status", "scheduled").execute()
    
    if result.data:
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/interviews/{interview_id}"}
        )
    else:
        template = get_template_response(templates, "interviews/edit.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Failed to update interview or interview is already in progress",
                "user": user
            })
        )

# DELETE - Cancel an interview
@router.post("/{interview_id}/cancel", response_class=JSONResponse)
async def cancel_interview(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Only allow cancellation if interview is in scheduled status
    result = supabase.table("interview_responses").update({
        "status": "cancelled"
    }).eq("id", interview_id).eq("created_by", user["id"]).eq("status", "scheduled").execute()
    
    if result.data:
        return JSONResponse({
            "success": True,
            "message": "Interview cancelled successfully"
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "Failed to cancel interview or interview is already in progress"
        })

# ACTION - Start interview with Blend AI
@router.post("/{interview_id}/start", response_class=JSONResponse)
async def start_interview(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Get interview
    interview_result = supabase.table("interview_responses").select("*").eq("id", interview_id).eq("created_by", user["id"]).execute()
    
    if not interview_result.data:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = interview_result.data[0]
    
    # Check if interview is already in progress or completed
    if interview["status"] in ["in_progress", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview is already {interview['status']}"
        )
    
    # Get student
    student_result = supabase.table("students").select("name, email").eq("id", interview["student_id"]).execute()
    student = student_result.data[0] if student_result.data else {"name": "Unknown", "email": "Unknown"}
    
    # Get template with questions
    template_result = supabase.table("interview_templates").select("*").eq("id", interview["template_id"]).execute()
    
    if not template_result.data:
        raise HTTPException(status_code=404, detail="Interview template not found")
    
    template = template_result.data[0]
    
    # Create main interview prompt for Blend AI
    interview_prompt = create_interview_prompt(
        student_name=student["name"],
        trainer_name=interview["trainer_name"],
        duration=template["duration_minutes"],
        questions=template["questions"]
    )
    
    # Create evaluation prompt for summary after the call
    # We'll create a placeholder for responses since we don't have them yet
    placeholder_responses = [{"question": q["question"], "answer": ""} for q in template["questions"]]
    
    evaluation_prompt = create_evaluation_prompt(
        student_name=student["name"],
        questions=template["questions"],
        responses=placeholder_responses
    )
    
    # Create callback URL
    callback_url = f"{API_CALLBACK_URL}/interviews/{interview_id}/callback"
    
    try:
        # Create Blend AI session with both prompts
        blend_response = await create_blend_session(
            prompt=interview_prompt,
            summary_prompt=evaluation_prompt,  # Pass the evaluation prompt for post-call processing
            duration_seconds=template["duration_minutes"] * 60,
            callback_url=callback_url
        )
        
        # Update interview with Blend session ID
        supabase.table("interview_responses").update({
            "blend_session_id": blend_response["id"],
            "status": "in_progress"
        }).eq("id", interview_id).execute()
        
        return JSONResponse({
            "success": True,
            "join_url": blend_response["join_url"]
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )

# BATCH - Create interviews for all students in a batch
@router.post("/batch-create", response_class=JSONResponse)
async def batch_create_interviews(
    request: Request,
    batch_id: str = Form(...),
    template_id: str = Form(...),
    trainer_name: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Get all students in batch
    students_result = supabase.table("batch_students").select(
        "student_id"
    ).eq("batch_id", batch_id).execute()
    
    if not students_result.data:
        return JSONResponse({
            "success": False,
            "error": "No students found in batch"
        })
    
    student_ids = [s["student_id"] for s in students_result.data]
    
    # Create interviews for each student
    interviews = []
    for student_id in student_ids:
        interview_data = {
            "student_id": student_id,
            "template_id": template_id,
            "trainer_name": trainer_name,
            "scheduled_at": datetime.now().isoformat(),
            "status": "scheduled",
            "created_by": user["id"]
        }
        
        interviews.append(interview_data)
    
    # Bulk insert
    result = supabase.table("interview_responses").insert(interviews).execute()
    
    if result.data:
        return JSONResponse({
            "success": True,
            "count": len(result.data),
            "interviews": result.data
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "Failed to create interviews"
        })