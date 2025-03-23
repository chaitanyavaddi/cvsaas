from typing import List, Dict, Any


def create_interview_prompt(student_name: str, trainer_name: str, duration: int, questions: List[Dict[str, Any]]) -> str:
    """
    Create a prompt for the Blend AI interview
    """
    prompt = f"""
You are an AI interviewer conducting a {duration} minute interview with {student_name}. 
The trainer overseeing this interview is {trainer_name}.

Your task is to:
1. Ask the following questions one by one
2. Listen to the candidate's responses
3. Provide natural follow-up questions if needed
4. Maintain a conversational tone
5. Keep track of time

After the interview, you will evaluate the candidate on:
- Overall interview performance (score out of 10)
- Communication skills (score out of 10)
- Clarity of answers (score out of 10)
- Specific strengths demonstrated
- Areas for improvement
- Any notable issues with their answers

Here are the questions to ask:
"""

    for i, q in enumerate(questions):
        prompt += f"\n{i+1}. {q['question']}"

    has_sample_answers = any("sample_answer" in q for q in questions)
    if has_sample_answers:
        prompt += "\n\nSample answers or key points to look for:\n"

        for i, q in enumerate(questions):
            if "sample_answer" in q and q["sample_answer"]:
                prompt += f"\n{i+1}. {q['sample_answer']}"

    prompt += "\n\nPlease conduct the interview professionally and provide comprehensive feedback afterward."

    return prompt


def create_evaluation_prompt(student_name: str, questions: List[Dict[str, Any]], responses: List[Dict[str, Any]]) -> str:
    """
    Create a prompt for AI to evaluate interview responses
    """
    prompt = f"""
You are an AI evaluator reviewing an interview with {student_name}.

Please analyze the following interview responses and provide:
1. An overall score out of 10
2. A communication score out of 10
3. Detailed feedback for each answer
4. A list of strengths demonstrated
5. A list of areas for improvement
6. Any problematic or concerning answers

Your evaluation should be fair, consistent, and focus on both the content and delivery of answers.

Here is the interview transcript:
"""

    for i, (question, response) in enumerate(zip(questions, responses)):
        prompt += f"\nQuestion {i+1}: {question['question']}\n"
        prompt += f"Response: {response['answer']}\n"
        if "sample_answer" in question and question["sample_answer"]:
            prompt += f"Sample Answer: {question['sample_answer']}\n"

    prompt += """
Please provide your structured evaluation in JSON format with the following keys:
{
  "overall_score": number,
  "communication_score": number,
  "question_evaluations": [
    {
      "question_number": number,
      "score": number,
      "feedback": string,
      "issues": [string],
      "strengths": [string]
    }
  ],
  "overall_feedback": string,
  "strengths": [string],
  "areas_for_improvement": [string],
  "problematic_answers": [string]
}
"""

    return prompt


def extract_responses_from_transcript(transcript: Dict[str, Any], questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract question/answer pairs from transcript
    """
    responses = []
    for i, question in enumerate(questions):
        question_text = question["question"]

        # Try to find the answer in the transcript
        answer = None

        # Check if transcript has structured Q&A format
        question_key = f"question_{i+1}"
        answer_key = f"answer_{i+1}"

        if isinstance(transcript, dict):
            if question_key in transcript and answer_key in transcript:
                answer = transcript[answer_key]
            elif "messages" in transcript:
                # Look for question in messages
                messages = transcript["messages"]
                for j, msg in enumerate(messages):
                    if question_text in msg.get("content", ""):
                        # Try to get the next message as the answer
                        if j + 1 < len(messages) and messages[j+1].get("role") == "user":
                            answer = messages[j+1].get("content", "")
                            break

        # If we couldn't find the answer, use a placeholder
        if not answer:
            answer = "No response found in transcript"

        responses.append({
            "question": question_text,
            "answer": answer
        })

    return responses


def generate_summary(evaluation: Dict[str, Any]) -> str:
    """
    Generate a summary from the evaluation
    """
    overall_score = evaluation.get("overall_score", 0)
    communication_score = evaluation.get("communication_score", 0)
    strengths = evaluation.get("strengths", [])
    areas_for_improvement = evaluation.get("areas_for_improvement", [])

    strength_list = "\n".join([f"- {s}" for s in strengths[:3]])
    improvement_list = "\n".join([f"- {a}" for a in areas_for_improvement[:3]])

    summary = f"""
Interview Score: {overall_score}/10
Communication Score: {communication_score}/10

Top Strengths:
{strength_list}

Areas for Improvement:
{improvement_list}

{evaluation.get("overall_feedback", "")}
"""

    return summary.strip()
