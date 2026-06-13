import os
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history = {}

def detect_language(text):
    text_lower = text.lower()
    hindi_words = ["hindi", "हिंदी", "हिन्दी", "मजेदार", "चुटकुला", "बताओ", "क्या", "कैसे"]
    telugu_words = ["telugu", "తెలుగు", "చెప్పు", "జోక్", "నవ్వు", "ఏమిటి"]
    for word in hindi_words:
        if word in text_lower or word in text:
            return "Hindi"
    for word in telugu_words:
        if word in text_lower or word in text:
            return "Telugu"
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return "Hindi"
        if '\u0C00' <= char <= '\u0C7F':
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

        language = detect_language(user_input)

        if session_id not in conversation_history:
            conversation_history[session_id] = []
        history = conversation_history[session_id]

        system_prompt = f"""You are Mazedaar AI — a fun, smart, and friendly assistant created for Indian users, especially students learning programming.

LANGUAGE RULE:
- Detected language: {language}
- Reply ONLY in {language} always.
- Hindi → Devanagari script, Telugu → Telugu script, English → English.

CODING RULE:
- If user asks about C, C++, Python, Java, or any programming topic → explain clearly with simple examples.
- Always show code examples in English (code is always in English).
- Explain the code in {language}.
- Keep explanations simple and beginner-friendly.

JOKE RULE:
- If user asks for a joke → tell funny, clean, family-friendly joke in {language}.

GENERAL RULES:
- Answer any question helpfully and clearly.
- Be warm and engaging.
- If asked who made you, say "I am Mazedaar AI, your friendly assistant!"
"""

        history.append({"role": "user", "content": user_input})
        if len(history) > 20:
            history = history[-20:]
            conversation_history[session_id] = history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=1024,
            temperature=0.8
        )

        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        conversation_history[session_id] = history

        return jsonify({"response": reply, "language_detected": language})

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
    app.run(host="0.0.0.0", port=5000, debug=True)
