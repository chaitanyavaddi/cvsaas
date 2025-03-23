import httpx
import os
import json
from fastapi import HTTPException, status

BLEND_API_KEY = os.environ.get("BLEND_API_KEY")
BLEND_API_URL = os.environ.get("BLEND_API_URL", "https://api.blend.ai")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

async def create_blend_session(prompt: str, summary_prompt: str, duration_seconds: int, callback_url: str):
    """
    Create a new session with Blend AI
    
    Args:
        prompt: The main interview prompt
        summary_prompt: The prompt to be used for post-call evaluation/summary
        duration_seconds: Call duration in seconds
        callback_url: Webhook URL for callback after the call
        
    Returns:
        Dictionary with session details including join_url
    """
    if not BLEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blend AI API key not set"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BLEND_API_URL}/sessions",
            headers={
                "Authorization": f"Bearer {BLEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": prompt,
                "summary_prompt": summary_prompt,  # Add the evaluation prompt for post-call summary
                "duration": duration_seconds,
                "callback_url": callback_url
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Blend AI session: {response.text}"
            )
            
        return response.json()

async def evaluate_with_ai(prompt: str):
    """
    Evaluate interview responses using AI
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not set"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are an expert interview evaluator."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            },
            timeout=60.0
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get AI evaluation: {response.text}"
            )
            
        result = response.json()
        return result["choices"][0]["message"]["content"]