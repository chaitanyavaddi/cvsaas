from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import httpx
import json
from typing import Dict, Any, List

from utils.auth import get_current_user, get_supabase_client, get_template_response

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ----- CRUD Operations for Interview Results -----

# READ - List all completed interviews with results
@router.get("/", response_class=HTMLResponse)
async def list_results(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get all completed interviews
    result = supabase.table("interview_responses").select(
        "id, student_id, template_id, completed_at, overall_score, communication_score"
    ).eq("created_by", user["id"]).eq("status", "completed").execute()
    
    interviews = result.data
    
    # Get student and template info
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
    
    template = get_template_response(templates, "results/list.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "results": interviews,
            "user": user
        })
    )

# READ - View detailed results for a specific interview
@router.get("/{interview_id}", response_class=HTMLResponse)
async def view_result(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    supabase = get_supabase_client()
    
    # Get interview with full results
    result = supabase.table("interview_responses").select("*").eq("id", interview_id).eq("created_by", user["id"]).eq("status", "completed").execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Interview result not found")
    
    interview = result.data[0]
    
    # Get student
    student_result = supabase.table("students").select("name, email").eq("id", interview["student_id"]).execute()
    student = student_result.data[0] if student_result.data else {"name": "Unknown", "email": "Unknown"}
    
    # Get template
    template_result = supabase.table("interview_templates").select("title, questions").eq("id", interview["template_id"]).execute()
    template = template_result.data[0] if template_result.data else {"title": "Unknown", "questions": []}
    
    # Format question evaluations for display
    question_evaluations = []
    if interview.get("scores") and isinstance(interview["scores"], list):
        for i, eval_item in enumerate(interview["scores"]):
            question_number = eval_item.get("question_number", i+1)
            if question_number <= len(template["questions"]):
                question_evaluations.append({
                    "question": template["questions"][question_number-1]["question"],
                    "score": eval_item.get("score", 0),
                    "feedback": eval_item.get("feedback", ""),
                    "issues": eval_item.get("issues", []),
                    "strengths": eval_item.get("strengths", [])
                })
    
    template = get_template_response(templates, "results/view.html")
    return HTMLResponse(
        template.render({
            "request": request,
            "result": interview,
            "student": student,
            "template_info": template,
            "question_evaluations": question_evaluations,
            "user": user
        })
    )

# READ - Get recording for a specific interview
@router.get("/{interview_id}/recording")
async def get_recording(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Get interview recording URL
    result = supabase.table("interview_responses").select(
        "call_recording_url"
    ).eq("id", interview_id).eq("created_by", user["id"]).execute()
    
    if not result.data or not result.data[0].get("call_recording_url"):
        raise HTTPException(status_code=404, detail="Recording not found")
    
    recording_url = result.data[0]["call_recording_url"]
    
    # Stream the recording from the storage URL
    async def stream_recording():
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", recording_url) as response:
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to retrieve recording")
                
                async for chunk in response.aiter_bytes():
                    yield chunk
    
    # Determine content type based on URL
    content_type = "audio/mpeg"  # Default
    if recording_url.endswith(".wav"):
        content_type = "audio/wav"
    elif recording_url.endswith(".ogg"):
        content_type = "audio/ogg"
    elif recording_url.endswith(".m4a"):
        content_type = "audio/mp4"
    
    return StreamingResponse(
        stream_recording(),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename=interview-{interview_id}.mp3"}
    )

# READ - Get transcript for a specific interview as JSON
@router.get("/{interview_id}/transcript", response_class=JSONResponse)
async def get_transcript(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Get interview transcript
    result = supabase.table("interview_responses").select(
        "transcript"
    ).eq("id", interview_id).eq("created_by", user["id"]).execute()
    
    if not result.data or "transcript" not in result.data[0]:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return JSONResponse(result.data[0]["transcript"])

# READ - Export interview results as JSON
@router.get("/{interview_id}/export", response_class=JSONResponse)
async def export_results(request: Request, interview_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Get full interview data
    result = supabase.table("interview_responses").select("*").eq("id", interview_id).eq("created_by", user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = result.data[0]
    
    # Get student data
    student_result = supabase.table("students").select("name, email").eq("id", interview["student_id"]).execute()
    student = student_result.data[0] if student_result.data else {"name": "Unknown", "email": "Unknown"}
    
    # Get template data
    template_result = supabase.table("interview_templates").select("title, questions").eq("id", interview["template_id"]).execute()
    template = template_result.data[0] if template_result.data else {"title": "Unknown", "questions": []}
    
    # Construct export data
    export_data = {
        "interview_id": interview["id"],
        "student": {
            "id": interview["student_id"],
            "name": student.get("name"),
            "email": student.get("email")
        },
        "template": {
            "id": interview["template_id"],
            "title": template.get("title")
        },
        "completed_at": interview.get("completed_at"),
        "scores": {
            "overall": interview.get("overall_score"),
            "communication": interview.get("communication_score")
        },
        "feedback": interview.get("feedback"),
        "strengths": interview.get("strengths", []),
        "areas_for_improvement": interview.get("areas_for_improvement", []),
        "summary": interview.get("summary", ""),
        "question_evaluations": interview.get("scores", []),
        "responses": interview.get("responses", [])
    }
    
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": f"attachment; filename=interview-results-{interview_id}.json"}
    )

# Statistics and Analytics

@router.get("/stats/overall", response_class=JSONResponse)
async def get_overall_statistics(request: Request):
    """Get overall interview statistics for the admin's account"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Get count of interviews by status
    status_result = supabase.table("interview_responses").select(
        "status", count="exact"
    ).eq("created_by", user["id"]).group_by("status").execute()
    
    status_counts = {row["status"]: row["count"] for row in status_result.data} if status_result.data else {}
    
    # Get average scores for completed interviews
    scores_result = supabase.table("interview_responses").select(
        "overall_score, communication_score"
    ).eq("created_by", user["id"]).eq("status", "completed").execute()
    
    avg_overall = 0
    avg_communication = 0
    if scores_result.data:
        overall_scores = [row.get("overall_score", 0) for row in scores_result.data if row.get("overall_score") is not None]
        communication_scores = [row.get("communication_score", 0) for row in scores_result.data if row.get("communication_score") is not None]
        
        avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        avg_communication = sum(communication_scores) / len(communication_scores) if communication_scores else 0
    
    return JSONResponse({
        "interview_counts": {
            "total": sum(status_counts.values()),
            "completed": status_counts.get("completed", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "scheduled": status_counts.get("scheduled", 0),
            "cancelled": status_counts.get("cancelled", 0)
        },
        "average_scores": {
            "overall": round(avg_overall, 1),
            "communication": round(avg_communication, 1)
        }
    })

@router.get("/stats/student/{student_id}", response_class=JSONResponse)
async def get_student_statistics(request: Request, student_id: str):
    """Get interview statistics for a specific student"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    supabase = get_supabase_client()
    
    # Verify student exists and belongs to admin
    student_result = supabase.table("students").select("name").eq("id", student_id).eq("created_by", user["id"]).execute()
    
    if not student_result.data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all completed interviews for this student
    interviews_result = supabase.table("interview_responses").select(
        "id, template_id, completed_at, overall_score, communication_score, strengths, areas_for_improvement"
    ).eq("student_id", student_id).eq("status", "completed").execute()
    
    if not interviews_result.data:
        return JSONResponse({
            "student_id": student_id,
            "student_name": student_result.data[0]["name"],
            "interviews_count": 0,
            "average_scores": {
                "overall": 0,
                "communication": 0
            },
            "common_strengths": [],
            "common_areas_for_improvement": []
        })
    
    interviews = interviews_result.data
    
    # Calculate average scores
    overall_scores = [i.get("overall_score", 0) for i in interviews if i.get("overall_score") is not None]
    communication_scores = [i.get("communication_score", 0) for i in interviews if i.get("communication_score") is not None]
    
    avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    avg_communication = sum(communication_scores) / len(communication_scores) if communication_scores else 0
    
    # Find common strengths and areas for improvement
    all_strengths = []
    all_areas = []
    
    for interview in interviews:
        all_strengths.extend(interview.get("strengths", []))
        all_areas.extend(interview.get("areas_for_improvement", []))
    
    # Count occurrences
    strength_counts = {}
    area_counts = {}
    
    for s in all_strengths:
        strength_counts[s] = strength_counts.get(s, 0) + 1
    
    for a in all_areas:
        area_counts[a] = area_counts.get(a, 0) + 1
    
    # Sort by frequency
    common_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    common_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return JSONResponse({
        "student_id": student_id,
        "student_name": student_result.data[0]["name"],
        "interviews_count": len(interviews),
        "average_scores": {
            "overall": round(avg_overall, 1),
            "communication": round(avg_communication, 1)
        },
        "common_strengths": [s[0] for s in common_strengths],
        "common_areas_for_improvement": [a[0] for a in common_areas],
        "recent_interviews": sorted(
            [{"id": i["id"], "completed_at": i["completed_at"], "overall_score": i["overall_score"]} 
             for i in interviews if "completed_at" in i],
            key=lambda x: x["completed_at"],
            reverse=True
        )[:5]
    })