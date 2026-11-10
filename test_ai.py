
from ai_service import generate_health_remarks

patient = {
    "age": 28,
    "glucose": 232,
    "haemoglobin": 13.5,
    "cholesterol": 180
}

print("Testing Gemini AI...")

result = generate_health_remarks(patient)

print("\nGemini AI Result:")
print(result)
