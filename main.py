import json
import re

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
    question_type = data.get("question_type")
    prompt = f"""
        Generate {questions_count} exam-style questions in {language} based on this: {prompt}.
        Mathematics: Use LaTeX syntax.
        Code Blocks: like this: \\n\\n```python\\nprint(2 ** 3 ** 2)\\n```
        Ensure all questions, options, and explanations are factually accurate and well-researched.
        type of questionse: {question_type}
        Return a JSON with:
        {{
          "questions": {question_format},
          "quiz": {quiz_format}
        }}

        Only return JSON. Use ``` for code blocks. Question types: "m-choice" (single answer) or "m-select" (multiple answers). Explanations must be correct and reasonably detailed. don't include the english transliteration for other languages
        """
    response = model.generate_content(prompt)

    try:

        raw_json = response.text.strip()

        if raw_json.startswith("```json"):
            raw_json = raw_json[7:].strip()
        if raw_json.startswith("```"):
            raw_json = raw_json[3:].strip()

        if raw_json.endswith("```"):
            raw_json = raw_json[:-3].strip()

        data = json.loads(raw_json)

        return jsonify({"questions": data})

    except json.JSONDecodeError as e:
        error_context = raw_json[max(0, e.pos - 20):min(len(raw_json), e.pos + 20)]

        return jsonify({
            "error": "Failed to parse model response",
            "details": {
                "exception": str(e),
                "position": e.pos,
                "context": error_context,
                "suggestion": "Check for unescaped backslashes (LaTeX) or invalid JSON syntax."
            },
            "raw_response": response.text  # Original response for debugging
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
