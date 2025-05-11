import json

import vertexai
from flask import Flask, request, jsonify
from vertexai.generative_models import GenerativeModel

app = Flask(__name__)
vertexai.init(project="eastern-academy-375008", location="us-central1")
model = GenerativeModel("gemini-2.0-flash-001")


@app.route("/quiz", methods=["POST"])
def generate_quiz():
    data = request.json
    prompt = data.get("prompt")
    questions_count = data.get("n_of_q")
    language = data.get("language")
    question_format = data.get("question_format")
    quiz_format = data.get("quiz_format")
    prompt = f"""
    Generate {questions_count} exam-style questions in {language} based on this: {prompt}.

    Ensure all questions, options, and explanations are factually accurate and well-researched.

    Return a JSON with:
    {{
      "questions": {question_format},
      "quiz": {quiz_format}
    }}

    Only return JSON. Use <pre> for code blocks. Question types: "m-choice" (single answer) or "m-select" (multiple answers). Explanations must be correct and reasonably detailed.
    """
    response = model.generate_content(prompt)
    try:
        # Remove markdown code blocks and whitespace
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]  # Remove ```json
        if json_str.startswith("```"):
            json_str = json_str[3:]  # Remove ```
        if json_str.endswith("```"):
            json_str = json_str[:-3]  # Remove ```

        # Parse the cleaned JSON
        questions = json.loads(json_str)

    except json.JSONDecodeError as e:
        return jsonify({
            "error": "Failed to parse model response",
            "raw_response": response.text,
            "exception": str(e)
        }), 500

    return jsonify({"questions": questions})


if __name__ == "__main__":
    app.run(debug=True)
