from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional

from utils.auth import get_current_user, get_supabase_client, get_template_response

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ----- CRUD Operations for Students -----

# READ - List all students
@router.get("/", response_class=HTMLResponse)
async def list_students(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get all students
    result = supabase.table("students").select(
        "id, name, email, created_at"
    ).eq("created_by", user["id"]).execute()
    
    students = result.data
    
    template = get_template_response(templates, "students/list.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "students": students,
            "user": user
        })
    )

# READ - View a specific student
@router.get("/{student_id}", response_class=HTMLResponse)
async def view_student(request: Request, student_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get student
    result = supabase.table("students").select(
        "id, name, email, created_at"
    ).eq("id", student_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = result.data[0]
    
    # Get student's interviews
    interviews_result = supabase.table("interview_responses").select(
        "id, template_id, status, scheduled_at, completed_at, overall_score"
    ).eq("student_id", student_id).execute()
    
    interviews = interviews_result.data
    
    # Get template names
    if interviews:
        template_ids = [interview["template_id"] for interview in interviews]
        templates_result = supabase.table("interview_templates").select(
            "id, title"
        ).in_("id", template_ids).execute()
        
        templates_dict = {template["id"]: template["title"] for template in templates_result.data}
        
        # Add template names to interviews
        for interview in interviews:
            interview["template_name"] = templates_dict.get(interview["template_id"], "Unknown")
    
    # Get student's batches
    batches_result = supabase.table("batch_students").select(
        "batch_id"
    ).eq("student_id", student_id).execute()
    
    batch_ids = [b["batch_id"] for b in batches_result.data]
    
    batches = []
    if batch_ids:
        batches_data = supabase.table("batches").select(
            "id, name"
        ).in_("id", batch_ids).execute()
        
        batches = batches_data.data
    
    template = get_template_response(templates, "students/view.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "student": student,
            "interviews": interviews,
            "batches": batches,
            "user": user
        })
    )

# CREATE - Show form to create a new student
@router.get("/create", response_class=HTMLResponse)
async def create_student_form(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    template = get_template_response(templates, "students/create.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "user": user
        })
    )

# CREATE - Create a new student
@router.post("/create", response_class=HTMLResponse)
async def create_student(
    request: Request,
    name: str = Form(...),
    email: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Create student
    result = supabase.table("students").insert({
        "name": name,
        "email": email,
        "created_by": user["id"]
    }).execute()
    
    if result.data:
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": "/students"}
        )
    else:
        template = get_template_response(templates, "students/create.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Failed to create student",
                "user": user
            })
        )

# UPDATE - Show form to edit a student
@router.get("/{student_id}/edit", response_class=HTMLResponse)
async def edit_student_form(request: Request, student_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get student
    result = supabase.table("students").select(
        "id, name, email"
    ).eq("id", student_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = result.data[0]
    
    template = get_template_response(templates, "students/edit.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "student": student,
            "user": user
        })
    )

# UPDATE - Update a student
@router.post("/{student_id}/edit", response_class=HTMLResponse)
async def update_student(
    request: Request,
    student_id: str,
    name: str = Form(...),
    email: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Update student
    result = supabase.table("students").update({
        "name": name,
        "email": email
    }).eq("id", student_id).eq("created_by", user["id"]).execute()
    
    if result.data:
        return HTMLResponse(
            content="",
            status_code=200,
            headers={"HX-Redirect": f"/students/{student_id}"}
        )
    else:
        template = get_template_response(templates, "students/edit.html")
        return HTMLResponse(
            template.render({
                "request": request,
                "error": "Failed to update student",
                "student": {"id": student_id, "name": name, "email": email},
                "user": user
            })
        )

# DELETE - Delete a student
@router.post("/{student_id}/delete", response_class=JSONResponse)
async def delete_student(request: Request, student_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Check if student has any interviews
    interviews_result = supabase.table("interview_responses").select(
        "id", count="exact"
    ).eq("student_id", student_id).execute()
    
    if interviews_result.count > 0:
        return JSONResponse({
            "success": False,
            "error": "Cannot delete student with existing interviews",
            "interview_count": interviews_result.count
        })
    
    # Delete student from batches first (cascade doesn't work with RLS)
    supabase.table("batch_students").delete().eq("student_id", student_id).execute()
    
    # Delete student
    result = supabase.table("students").delete().eq("id", student_id).eq("created_by", user["id"]).execute()
    
    if result.data:
        return JSONResponse({
            "success": True,
            "message": "Student deleted successfully"
        })
    else:
        return JSONResponse({
            "success": False,
            "error": "Failed to delete student"
        })

# BATCH - Import students from CSV
@router.post("/import", response_class=JSONResponse)
async def import_students(
    request: Request,
    csv_data: str = Form(...)
):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        # Parse CSV data (simple implementation)
        rows = csv_data.strip().split("\n")
        header = rows[0].split(",")
        
        # Check required columns
        if "name" not in header or "email" not in header:
            return JSONResponse({
                "success": False,
                "error": "CSV must include 'name' and 'email' columns"
            })
        
        name_index = header.index("name")
        email_index = header.index("email")
        
        students = []
        for i in range(1, len(rows)):
            values = rows[i].split(",")
            if len(values) >= max(name_index, email_index) + 1:
                students.append({
                    "name": values[name_index].strip(),
                    "email": values[email_index].strip(),
                    "created_by": user["id"]
                })
        
        if not students:
            return JSONResponse({
                "success": False,
                "error": "No valid student records found"
            })
        
        # Insert students
        supabase = get_supabase_client()
        result = supabase.table("students").insert(students).execute()
        
        return JSONResponse({
            "success": True,
            "count": len(result.data),
            "students": result.data
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"Error importing students: {str(e)}"
        })

# Search students
@router.get("/search", response_class=JSONResponse)
async def search_students(
    request: Request,
    query: Optional[str] = None
):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    if not query or len(query) < 2:
        return JSONResponse([])
    
    supabase = get_supabase_client()
    
    # Search students by name or email
    result = supabase.table("students").select(
        "id, name, email"
    ).eq("created_by", user["id"]).or_(
        f"name.ilike.%{query}%,email.ilike.%{query}%"
    ).execute()
    
    return JSONResponse(result.data)