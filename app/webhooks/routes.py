from fastapi import APIRouter, Request, HTTPException, status, Body, Depends
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any
from datetime import datetime
import os
import logging

from utils.auth import get_supabase_client
from utils.blend_ai import evaluate_with_ai
from utils.prompts import extract_responses_from_transcript, generate_summary

router = APIRouter()
logger = logging.getLogger("webhook")

def verify_webhook_token(token: str = Depends(lambda: "")):
    """Simple webhook token verification (optional)"""
    expected_token = os.environ.get("WEBHOOK_TOKEN")
    if expected_token and token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid webhook token"
        )
    return True

@router.post("/interviews/{interview_id}/callback", response_class=JSONResponse)
async def interview_callback(
    interview_id: str,
    data: Dict[str, Any] = Body(...)
):
    """
    Callback endpoint for Blend AI to send interview results
    
    This webhook receives data from Blend AI after an interview is completed,
    including the transcript, recording, and AI-generated evaluation.
    """
    logger.info(f"Received callback for interview {interview_id}")
    
    try:
        supabase = get_supabase_client()
        
        # Verify the interview exists
        interview_result = supabase.table("interview_responses").select(
            "id, student_id, template_id, created_by"
        ).eq("id", interview_id).execute()
        
        if not interview_result.data:
            logger.error(f"Interview {interview_id} not found")
            return JSONResponse(
                {"success": False, "error": "Interview not found"},
                status_code=404
            )
        
        interview = interview_result.data[0]
        
        # Log the full callback data for debugging
        logger.debug(f"Callback data: {json.dumps(data)}")
        
        # Extract relevant data from the callback
        transcript = data.get("transcript", {})
        recording_url = data.get("recording_url", "")
        
        # The evaluation should now come directly from Blend AI's summary
        # since we provided the summary_prompt
        evaluation = data.get("summary", {})
        
        # If the summary isn't structured as expected, we need to parse it
        if isinstance(evaluation, str):
            try:
                # Try to extract JSON if the response contains it
                if "{" in evaluation and "}" in evaluation:
                    json_start = evaluation.find("{")
                    json_end = evaluation.rfind("}") + 1
                    json_str = evaluation[json_start:json_end]
                    evaluation = json.loads(json_str)
                else:
                    # Fallback to a simple evaluation
                    logger.warning(f"Summary not in JSON format: {evaluation}")
                    evaluation = {
                        "overall_score": 5.0,
                        "communication_score": 5.0,
                        "overall_feedback": evaluation[:500] if evaluation else "No evaluation provided",
                        "strengths": [],
                        "areas_for_improvement": [],
                        "question_evaluations": []
                    }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse evaluation JSON: {evaluation}")
                evaluation = {
                    "overall_score": 5.0,
                    "communication_score": 5.0,
                    "overall_feedback": "Unable to parse evaluation results.",
                    "strengths": [],
                    "areas_for_improvement": [],
                    "question_evaluations": []
                }
        
        # Get template with questions 
        template_result = supabase.table("interview_templates").select(
            "questions"
        ).eq("id", interview["template_id"]).execute()
        
        if not template_result.data:
            logger.error(f"Template for interview {interview_id} not found")
            return JSONResponse(
                {"success": False, "error": "Template not found"},
                status_code=404
            )
        
        questions = template_result.data[0]["questions"]
        
        # Extract responses from transcript if needed
        responses = []
        if not data.get("responses"):
            responses = extract_responses_from_transcript(transcript, questions)
        else:
            responses = data.get("responses")
        
        # Generate a summary if not already provided
        summary = data.get("summary_text", "")
        if not summary and isinstance(evaluation, dict):
            summary = generate_summary(evaluation)
        
        # Update the interview with results
        supabase.table("interview_responses").update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "call_recording_url": recording_url,
            "transcript": transcript,
            "responses": responses,
            "overall_score": float(evaluation.get("overall_score", 5.0)) if isinstance(evaluation, dict) else 5.0,
            "communication_score": float(evaluation.get("communication_score", 5.0)) if isinstance(evaluation, dict) else 5.0,
            "scores": evaluation.get("question_evaluations", []) if isinstance(evaluation, dict) else [],
            "feedback": evaluation.get("overall_feedback", "") if isinstance(evaluation, dict) else evaluation if isinstance(evaluation, str) else "",
            "strengths": evaluation.get("strengths", []) if isinstance(evaluation, dict) else [],
            "areas_for_improvement": evaluation.get("areas_for_improvement", []) if isinstance(evaluation, dict) else [],
            "summary": summary
        }).eq("id", interview_id).execute()
        
        logger.info(f"Successfully processed interview {interview_id}")
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        logger.error(f"Error processing interview callback: {str(e)}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@router.get("/interviews/{interview_id}/status")
async def get_interview_status(interview_id: str):
    """Get the current status of an interview"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("interview_responses").select(
            "status, blend_session_id, completed_at"
        ).eq("id", interview_id).execute()
        
        if not result.data:
            return JSONResponse(
                {"success": False, "error": "Interview not found"},
                status_code=404
            )
        
        return JSONResponse({
            "success": True,
            "status": result.data[0]["status"],
            "blend_session_id": result.data[0].get("blend_session_id"),
            "completed_at": result.data[0].get("completed_at")
        })
        
    except Exception as e:
        logger.error(f"Error getting interview status: {str(e)}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )