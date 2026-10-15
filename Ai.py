
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemma-4-26b-a4b-it"


def analyze_resume(resume_text, user_goal):
    prompt = f"""
You are an expert resume analyzer and career coach.

Target job role: {user_goal}

Resume:
{resume_text}

Return a valid JSON object with exactly these keys:
- skills: list of skills found in the resume
- missing_skills: relevant skills not demonstrated in the resume
- roadmap: step-by-step learning recommendations
- interview_questions: relevant interview questions

Be accurate and concise. Do not invent resume details.
Return JSON only, without Markdown fences.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        return json.loads(response.text)

    except Exception as error:
        print("Gemma analysis error:", error)
        return {"error": str(error)}
