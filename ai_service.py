
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = (
    genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(
                attempts=1
            )
        )
    )
    if api_key else None
)


def generate_health_remarks(patient):
    if not client:
        return "AI remarks unavailable. API key not configured."

    prompt = f"""
    Review these patient health readings:
    Age: {patient.get('age', 'Not provided')}
    Glucose: {patient.get('glucose')}
    Haemoglobin: {patient.get('haemoglobin')}
    Cholesterol: {patient.get('cholesterol')}

    Give a short, simple observation.
    Do not diagnose any disease.
    Recommend professional medical interpretation.
    """

    try:
        response = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )
        return response.output_text

    except Exception as error:
        print("Gemini AI Error:", repr(error))
        return "AI remarks temporarily unavailable. Please try again later."
