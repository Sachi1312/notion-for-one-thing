from flask import Flask, request, jsonify, render_template
from supabase import create_client
from groq import Groq
from dotenv import load_dotenv
import os
import json

# ── Load secret keys from .env file ──────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ── Connect to services ───────────────────────────────
app      = Flask(__name__)
client   = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Route 1: Show the main page ───────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── Route 2: Save a note + AI processing ─────────────
@app.route("/save", methods=["POST"])
def save_note():
    data    = request.get_json()
    content = data["content"]

    # Ask AI to generate tags and summary
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analyse this note and respond ONLY with valid JSON in this exact format:
{{
  "summary": "one sentence summary of the note",
  "tags": "tag1, tag2, tag3"
}}

Note: {content}"""
        }]
    )

    # Parse the AI's JSON response
    ai_text = response.choices[0].message.content
    ai_text = ai_text.strip()
    if ai_text.startswith("```"):
        ai_text = ai_text.split("```")[1]
        if ai_text.startswith("json"):
            ai_text = ai_text[4:]
    ai_data = json.loads(ai_text)

    summary = ai_data["summary"]
    tags    = ai_data["tags"]

    # Save everything to Supabase
    supabase.table("notes").insert({
        "content": content,
        "summary": summary,
        "tags":    tags
    }).execute()

    return jsonify({"success": True, "summary": summary, "tags": tags})

# ── Route 3: Get all notes ────────────────────────────
@app.route("/notes", methods=["GET"])
def get_notes():
    result = supabase.table("notes") \
                     .select("*") \
                     .order("created_at", desc=True) \
                     .execute()
    return jsonify(result.data)

# ── Start the server ──────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)