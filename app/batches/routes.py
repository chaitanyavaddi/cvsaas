from fastapi import APIRouter, Request, Form, Body, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional

from utils.auth import get_current_user, get_supabase_client, get_template_response

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ----- CRUD Operations for Batches -----

# READ - List all batches
@router.get("/", response_class=HTMLResponse)
async def list_batches(request: Request):
    # user = await get_current_user(request)
    # if not user:
    #     return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # supabase = get_supabase_client()
    
    # Get all batches
    # result = supabase.table("batches").select(
    #     "id, name, created_at"
    # ).eq("created_by", user["id"]).execute()
    
    # batches = result.data
    
    # # Get student count for each batch
    # for batch in batches:
    #     count_result = supabase.table("batch_students").select(
    #         "student_id", count="exact"
    #     ).eq("batch_id", batch["id"]).execute()
        
    #     batch["student_count"] = count_result.count
    
    template = get_template_response("dashboard/new-student.html")
    return HTMLResponse(
        template.render({
            "request": request,
            # "batches": batches,
            # "user": user
        })
    )

# READ - View a specific batch
@router.get("/{batch_id}", response_class=HTMLResponse)
async def view_batch(request: Request, batch_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get batch
    result = supabase.table("batches").select(
        "id, name, created_at"
    ).eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch = result.data[0]
    
    # Get students in batch
    students_result = supabase.table("batch_students").select(
        "student_id"
    ).eq("batch_id", batch_id).execute()
    
    student_ids = [s["student_id"] for s in students_result.data]
    
    students = []
    if student_ids:
        students_data = supabase.table("students").select(
            "id, name, email"
        ).in_("id", student_ids).execute()
        
        students = students_data.data
    
    # Get students not in batch (for adding)
    all_students = supabase.table("students").select(
        "id, name, email"
    ).eq("created_by", user["id"]).execute()
    
    available_students = [s for s in all_students.data if s["id"] not in student_ids]
    
    template = get_template_response(templates, "batches/view.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "batch": batch,
            "students": students,
            "available_students": available_students,
            "user": user
        })
    )

# CREATE - Show form to create a new batch
@router.get("/create", response_class=HTMLResponse)
async def create_batch_form(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    template = get_template_response(templates, "batches/create.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "user": user
        })
    )

# CREATE - Create a new batch
@router.post("/create", response_class=HTMLResponse)
async def create_batch(
    request: Request,
    name: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Create batch
    result = supabase.table("batches").insert({
        "name": name,
        "created_by": user["id"]
    }).execute()
    
    if result.data:
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": "/batches"}
        )
    else:
        template = get_template_response(templates, "batches/create.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Failed to create batch",
                "user": user
            })
        )

# UPDATE - Show form to edit a batch
@router.get("/{batch_id}/edit", response_class=HTMLResponse)
async def edit_batch_form(request: Request, batch_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get batch
    result = supabase.table("batches").select(
        "id, name"
    ).eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch = result.data[0]
    
    template = get_template_response(templates, "batches/edit.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "batch": batch,
            "user": user
        })
    )

# UPDATE - Update a batch
@router.post("/{batch_id}/edit", response_class=HTMLResponse)
async def update_batch(
    request: Request,
    batch_id: str,
    name: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Update batch
    result = supabase.table("batches").update({
        "name": name
    }).eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if result.data:
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/batches/{batch_id}"}
        )
    else:
        template = get_template_response(templates, "batches/edit.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Failed to update batch",
                "batch": {"id": batch_id, "name": name},
                "user": user
            })
        )

# DELETE - Delete a batch
@router.post("/{batch_id}/delete", response_class=JSONResponse)
async def delete_batch(request: Request, batch_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Delete batch-student associations first (cascade doesn't work with RLS)
    supabase.table("batch_students").delete().eq("batch_id", batch_id).execute()
    
    # Delete batch
    result = supabase.table("batches").delete().eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if result.data:
        return JSONResponse({
            "success": True,
            "message": "Batch deleted successfully"
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "Failed to delete batch"
        })

# ACTIONS - Add students to batch
@router.post("/{batch_id}/add-students", response_class=JSONResponse)
async def add_students_to_batch(
    request: Request,
    batch_id: str,
    student_ids: List[str] = Body(...)
):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Verify batch ownership
    batch_result = supabase.table("batches").select(
        "id"
    ).eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if not batch_result.data:
        return JSONResponse({
            "success": False,
            "error": "Batch not found"
        })
    
    # Verify student ownership
    if student_ids:
        students_result = supabase.table("students").select(
            "id"
        ).in_("id", student_ids).eq("created_by", user["id"]).execute()
        
        if len(students_result.data) != len(student_ids):
            return JSONResponse({
                "success": False,
                "error": "Some students not found or not owned by user"
            })
    
    # Get existing student-batch associations to avoid duplicates
    existing_result = supabase.table("batch_students").select(
        "student_id"
    ).eq("batch_id", batch_id).in_("student_id", student_ids).execute()
    
    existing_student_ids = [s["student_id"] for s in existing_result.data]
    new_student_ids = [sid for sid in student_ids if sid not in existing_student_ids]
    
    if not new_student_ids:
        return JSONResponse({
            "success": True,
            "message": "No new students to add",
            "added_count": 0
        })
    
    # Create batch-student associations
    batch_students = [{"batch_id": batch_id, "student_id": student_id} for student_id in new_student_ids]
    result = supabase.table("batch_students").insert(batch_students).execute()
    
    if result.data:
        return JSONResponse({
            "success": True,
            "message": f"Added {len(result.data)} students to batch",
            "added_count": len(result.data)
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "Failed to add students to batch"
        })

# ACTIONS - Remove student from batch
@router.post("/{batch_id}/remove-student/{student_id}", response_class=JSONResponse)
async def remove_student_from_batch(request: Request, batch_id: str, student_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Verify batch ownership
    batch_result = supabase.table("batches").select(
        "id"
    ).eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if not batch_result.data:
        return JSONResponse({
            "success": False,
            "error": "Batch not found"
        })
    
    # Delete association
    result = supabase.table("batch_students").delete().eq("batch_id", batch_id).eq("student_id", student_id).execute()
    
    if result.data:
        return JSONResponse({
            "success": True,
            "message": "Student removed from batch"
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "Failed to remove student from batch"
        })

# ACTIONS - Schedule interviews for all students in a batch
@router.get("/{batch_id}/schedule", response_class=HTMLResponse)
async def schedule_batch_interviews_form(request: Request, batch_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get batch
    result = supabase.table("batches").select(
        "id, name"
    ).eq("id", batch_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch = result.data[0]
    
    # Get student count
    students_count = supabase.table("batch_students").select(
        "student_id", count="exact"
    ).eq("batch_id", batch_id).execute().count
    
    # Get all templates
    templates_result = supabase.table("interview_templates").select(
        "id, title, duration_minutes"
    ).eq("created_by", user["id"]).execute()
    
    template = get_template_response(templates, "batches/schedule.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "batch": batch,
            "students_count": students_count,
            "templates": templates_result.data,
            "user": user
        })
    )