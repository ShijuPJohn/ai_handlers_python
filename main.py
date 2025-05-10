from flask import Flask, request, jsonify
from vertexai.generative_models import GenerativeModel
import vertexai

app = Flask(__name__)
vertexai.init(project="eastern-academy-375008", location="asia-southeast1")
model = GenerativeModel("gemini-1.5-pro")

@app.route("/generate-quiz", methods=["POST"])
def generate_quiz():
    data = request.json
    transcript = data.get("transcript")

    prompt = f"""
    Generate 5 MCQs from the following transcript. Each question must include:
    - question
    - options (A, B, C, D)
    - correct_answer (one letter)
    - explanation
    - difficulty (easy/medium/hard)

    Transcript:
    {transcript}
    """

    response = model.generate_content(prompt)
    return jsonify({"questions": response.text})
