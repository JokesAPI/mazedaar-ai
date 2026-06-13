import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history = {}

def detect_language(text):
    text_lower = text.lower()

    lang_keywords = {
        "Hindi":     ["hindi", "हिंदी", "हिन्दी", "मजेदार", "बताओ", "क्या", "कैसे"],
        "Telugu":    ["telugu", "తెలుగు", "చెప్పు", "జోక్", "ఏమిటి"],
        "Tamil":     ["tamil", "தமிழ்", "சொல்லு", "என்ன", "எப்படி"],
        "Kannada":   ["kannada", "ಕನ್ನಡ", "ಹೇಳು", "ಏನು", "ಹೇಗೆ"],
        "Malayalam": ["malayalam", "മലയാളം", "പറയൂ", "എന്ത്", "എങ്ങനെ"],
        "Marathi":   ["marathi", "मराठी", "सांग", "काय", "कसे"],
        "Gujarati":  ["gujarati", "ગુજરાતી", "કહો", "શું", "કેવી"],
        "Bengali":   ["bengali", "বাংলা", "বলো", "কী", "কেমন"],
        "Punjabi":   ["punjabi", "ਪੰਜਾਬੀ", "ਦੱਸੋ", "ਕੀ", "ਕਿਵੇਂ"],
        "Urdu":      ["urdu", "اردو", "بتاؤ", "کیا", "کیسے"],
    }

    unicode_ranges = {
        "Hindi":     ('\u0900', '\u097F'),
        "Tamil":     ('\u0B80', '\u0BFF'),
        "Telugu":    ('\u0C00', '\u0C7F'),
        "Kannada":   ('\u0C80', '\u0CFF'),
        "Malayalam": ('\u0D00', '\u0D7F'),
        "Marathi":   ('\u0900', '\u097F'),
        "Gujarati":  ('\u0A80', '\u0AFF'),
        "Bengali":   ('\u0980', '\u09FF'),
        "Punjabi":   ('\u0A00', '\u0A7F'),
        "Urdu":      ('\u0600', '\u06FF'),
    }

    for lang, keywords in lang_keywords.items():
        for word in keywords:
            if word in text_lower or word in text:
                return lang

    for lang, (start, end) in unicode_ranges.items():
        for char in text:
            if start <= char <= end:
                return lang

    return "English"


def get_news(topic="India"):
    try:
        url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("status") == "ok" and data.get("articles"):
            articles = data["articles"][:5]
            news_text = ""
            for i, a in enumerate(articles, 1):
                news_text += f"{i}. {a['title']} — {a['source']['name']}\n"
            return news_text
        return None
    except:
        return None


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

        # Check for news request
        news_context = ""
        news_keywords = ["news", "latest", "today", "current", "headlines", "breaking",
                        "समाचार", "खबर", "వార్తలు", "செய்தி", "ಸುದ್ದಿ", "വാർത്ത"]
        is_news_request = any(word in user_input.lower() for word in news_keywords)

        if is_news_request and NEWS_API_KEY:
            topic = "India"
            for word in ["cricket", "politics", "technology", "business", "sports", "bollywood"]:
                if word in user_input.lower():
                    topic = word
                    break
            news = get_news(topic)
            if news:
                news_context = f"\n\nLatest news headlines about {topic}:\n{news}\nUse these headlines to answer the user's news question."

        system_prompt = f"""You are Mazedaar AI (also called Genie) — a fun, smart, and friendly assistant for Indian users.

LANGUAGE RULE (MOST IMPORTANT):
- Detected language: {language}
- Reply ONLY in {language}.
- Hindi/Marathi → Devanagari script
- Telugu → Telugu script
- Tamil → Tamil script
- Kannada → Kannada script
- Malayalam → Malayalam script
- Gujarati → Gujarati script
- Bengali → Bengali script
- Punjabi → Gurmukhi script
- Urdu → Urdu script
- English → English
- NEVER mix languages.

CODING RULE:
- If user asks about C, C++, Python, Java → explain with simple examples.
- Code always in English, explanation in {language}.

JOKE RULE:
- Jokes must be funny, clean, family-friendly, in {language}, 2-4 lines only.

NEWS RULE:
- If news headlines are provided below, summarize them in {language}.
- Present news in a friendly, clear way.

GENERAL RULES:
- Answer any question helpfully.
- Be warm, engaging, concise.
- If asked who made you: "I am Mazedaar AI (Genie), your friendly assistant!"
{news_context}
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
