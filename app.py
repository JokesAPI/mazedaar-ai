import os
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ✅ PASTE YOUR OPENAI API KEY HERE
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Conversation memory
conversation_history = {}

def detect_language(text):
    text_lower = text.lower()

    hindi_words = ["hindi", "हिंदी", "हिन्दी", "मजेदार", "चुटकुला", "बताओ", "क्या", "कैसे", "joke सुनाओ"]
    telugu_words = ["telugu", "తెలుగు", "చెప్పు", "జోక్", "నవ్వు", "మీకు", "ఏమిటి"]

    for word in hindi_words:
        if word in text_lower or word in text:
            return "Hindi"

    for word in telugu_words:
        if word in text_lower or word in text:
            return "Telugu"

    # Check Unicode script ranges
    for char in text:
        if '\u0900' <= char <= '\u097F':  # Devanagari (Hindi)
            return "Hindi"
        if '\u0C00' <= char <= '\u0C7F':  # Telugu
            return "Telugu"

    return "English"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        user_input = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not user_input:
            return jsonify({"error": "Message is empty"}), 400

        # Auto-detect language
        language = detect_language(user_input)

        # Initialize session
        if session_id not in conversation_history:
            conversation_history[session_id] = []

        history = conversation_history[session_id]

        # System prompt
        system_prompt = f"""You are Mazedaar AI — a fun, smart, and friendly assistant created for Indian users.

LANGUAGE RULE (MOST IMPORTANT):
- The user's detected language is: {language}
- You MUST reply ONLY in {language}.
- If language is Hindi → reply fully in Hindi (Devanagari script).
- If language is Telugu → reply fully in Telugu script.
- If language is English → reply in English.
- NEVER mix languages unless the user explicitly asks.

JOKE RULE:
- If the user asks for a joke, tell a funny, clean, family-friendly joke.
- Jokes must be in {language} only.
- Keep jokes short (2-4 lines max).

GENERAL RULES:
- Be warm, friendly, and engaging.
- Keep responses concise and clear.
- Remember the conversation history.
- If asked who made you, say "I am Mazedaar AI, your friendly assistant!"
"""

        # Add user message to history
        history.append({"role": "user", "content": user_input})

        # Keep last 20 messages only
        if len(history) > 20:
            history = history[-20:]
            conversation_history[session_id] = history

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=1024,
            temperature=0.8
        )

        reply = response.choices[0].message.content

        # Save reply to history
        history.append({"role": "assistant", "content": reply})
        conversation_history[session_id] = history

        return jsonify({
            "response": reply,
            "language_detected": language
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/clear", methods=["POST"])
def clear_history():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    if session_id in conversation_history:
        del conversation_history[session_id]
    return jsonify({"message": "Conversation cleared."})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Mazedaar AI is running OK"})


if __name__ == "__main__":
    print("Mazedaar AI server starting...")
    print("Running at http://localhost:5000")
    print("Send POST to /chat with JSON: {message, session_id}")
    app.run(host="0.0.0.0", port=5000, debug=True)
