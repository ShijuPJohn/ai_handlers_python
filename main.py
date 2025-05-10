import json
import re

from flask import Flask, request, jsonify
from vertexai.generative_models import GenerativeModel
import vertexai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

app = Flask(__name__)
vertexai.init(project="eastern-academy-375008", location="us-central1")
model = GenerativeModel("gemini-2.0-flash-001")


def get_youtube_transcript(youtube_url: str) -> str:
    # Extract video ID using regex
    video_id_match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', youtube_url)
    if not video_id_match:
        raise ValueError("Invalid YouTube URL")
    video_id = video_id_match.group(1)
    print(f"Extracted Video ID: {video_id}")
    try:
        # Try to get English transcript first
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            transcript_text = " ".join([item['text'] for item in transcript])
            print(f"Successfully fetched English transcript (length: {len(transcript_text)} chars)")
            return transcript_text
        except (TranscriptsDisabled, NoTranscriptFound):
            # If no English transcript, try any available language
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([item['text'] for item in transcript])
                print(f"Successfully fetched transcript in another language (length: {len(transcript_text)} chars)")
                return transcript_text
            except Exception as e:
                raise Exception(f"No transcripts available for video {video_id}") from e

    except Exception as e:
        raise Exception(f"Failed to get transcript: {str(e)}")


@app.route("/quiz", methods=["POST"])
def generate_quiz():
    data = request.json
    yt_url = data.get("url")
    number_of_questions = data.get("n_of_q")
    question_format = data.get("question_format")
    quiz_format = data.get("quiz_format")
    try:
        transcript = get_youtube_transcript(yt_url)
    except Exception as e:
        return jsonify({
            "error": "Failed to get transcript",
            "exception": str(e)
        }), 500

    prompt = f"""
    You are an expert exam creator. Based on the following transcript, generate {number_of_questions} high-quality questions and quiz data.

    Output a JSON object with the structure:
    {{
      "questions": {question_format},
      "quiz": {quiz_format}
    }}

    Only return the JSON object. Do not include any explanation or markdown formatting. make sure the explanation is correct and elaborate.

    Transcript:
    \"\"\"
    {transcript}
    \"\"\"
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
