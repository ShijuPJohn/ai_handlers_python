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
    if not difficulty or difficulty==0:
        difficulty="all difficulty levels"
    prompt = f"""
        Generate {questions_count} exam-style questions in {language} based on this: {prompt}.

        For mathematics within questions, enclose equations within double dollar signs for LaTeX (e.g., $$\\frac{{a}}{{b}}$$).

        For code blocks, use triple backticks with the language specified (e.g., ```python\\nprint("Hello")\\n```). Ensure proper newline characters (\\n) within the code.

        When providing explanations, if there are any mathematical expressions, ensure they are also enclosed within double dollar signs for LaTeX (e.g., The probability is $$\frac{{1}}{{6}}$$).

        Ensure all questions, options (if applicable based on question_format), and explanations are factually accurate and well-researched.

        Type of questions: {question_type} 
        Question format: {question_format}
        Quiz format: {quiz_format}
        Difficulty:{difficulty} on a scale from 1 to 10

        Return a JSON object with the following structure:
        {{
          "questions": {question_format},
          "quiz": {quiz_format}
        }}

        Strictly adhere to valid JSON format. Do not include any extra text or explanations outside the JSON.
        Do not include the English transliteration for other languages.
        Do not include options directly in the question statement (they should be part of the {question_format}).
        If the Type of questions is mcq, be strictly single select. dont include more than one correct answer.
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
