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
    difficulty = data.get("difficulty")
    if not difficulty or difficulty == 0:
        difficulty = "all difficulty levels"

    prompt = f"""
Generate {questions_count} high-quality, exam-style questions in {language} based on the following topic/content:

{prompt}

Formatting guidelines:

1. **Mathematics**:
   - Use double dollar signs (`$$`) to enclose equations.
   - Use **double backslashes** for LaTeX formatting (e.g., `$$\\\\frac{{a}}{{b}}$$`).

2. **Code blocks**:
   - Use triple backticks and specify the language (e.g., ```python\\nprint("Hello")\\n```).
   - Use proper newline characters (`\\n`) within code blocks.

3. **Explanations**:
   - If they contain math, format expressions like in the math section above.

Content requirements:

- All questions, options, and explanations must be factually correct and well-researched.
- Ensure the correct option is accurate and unambiguous.
- If `{question_type}` is "mcq", only include **one correct option** (strictly single-select).
- Do not embed answer options within the question text itself — keep them in the `{question_format}` object.

Metadata:

- Type of questions: {question_type}  
- Question format: {question_format}  
- Quiz format: {quiz_format}  
- Difficulty: {difficulty} (on a scale of 1 to 10)

Output format:

Return a **valid JSON** object in the following structure:

{{
  "questions": {question_format},
  "quiz": {quiz_format}
}}

Output rules:

- Do **not** include any additional commentary, explanation, or text outside the JSON.
- Do **not** include English transliterations for content in other languages.
"""

    response = model.generate_content(prompt)

    raw_json = response.text.strip()

    # Remove any leading/trailing backticks (common with code generation)
    if raw_json.startswith("```"):
        raw_json = raw_json[3:].lstrip()
    if raw_json.endswith("```"):
        raw_json = raw_json[:-3].rstrip()
    if raw_json.startswith("json"):
        raw_json = raw_json[4:].lstrip()

    try:
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
                "suggestion": "Check the raw response for JSON syntax errors, especially around LaTeX and code blocks."
            },
            "raw_response": response.text
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
