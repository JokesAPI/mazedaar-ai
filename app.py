import os
import requests
import random
from datetime import datetime
import pytz
from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history = {}

JOKE_STYLES = {
    "Telugu": "Jandhyala style Telugu comedy — sharp wit, family drama, unexpected punchlines. Write ENTIRELY in Telugu script.",
    "Hindi": "Raju Srivastava and Jaspal Bhatti style — social comedy, common man humor. Write ENTIRELY in Hindi Devanagari script.",
    "Tamil": "Vadivelu and Vivek style — exaggerated reactions, wordplay. Write ENTIRELY in Tamil script.",
    "Kannada": "Ramesh Aravind style — smart wordplay, family situations. Write ENTIRELY in Kannada script.",
    "Malayalam": "Innocent and Sreenivasan style — subtle intelligent humor. Write ENTIRELY in Malayalam script.",
    "Marathi": "Pu La Deshpande style — witty observations. Write ENTIRELY in Marathi (Devanagari script).",
    "Bengali": "Classic Bangla humor — clever wordplay. Write ENTIRELY in Bengali script.",
    "Gujarati": "Classic Gujarati humor. Write ENTIRELY in Gujarati script.",
    "Punjabi": "Classic Punjabi humor — energetic fun. Write ENTIRELY in Punjabi Gurmukhi script.",
    "Urdu": "Classic Urdu wit — poetic humor. Write ENTIRELY in Urdu script.",
    "English": "Classic English dry wit — unexpected punchlines.",
}

# Language detection — checks for language name keywords first
def detect_language(text):
    text_lower = text.lower()

    # Check explicit language name mentions FIRST
    explicit = {
        "telugu": "Telugu",
        "hindi": "Hindi",
        "tamil": "Tamil",
        "kannada": "Kannada",
        "malayalam": "Malayalam",
        "marathi": "Marathi",
        "gujarati": "Gujarati",
        "bengali": "Bengali",
        "punjabi": "Punjabi",
        "urdu": "Urdu",
        "english": "English",
    }
    for keyword, lang in explicit.items():
        if keyword in text_lower:
            return lang

    # Check native script keywords
    lang_keywords = {
        "Hindi":     ["हिंदी", "हिन्दी", "मजेदार", "बताओ", "क्या", "कैसे", "यार"],
        "Telugu":    ["తెలుగు", "చెప్పు", "జోక్", "ఏమిటి", "నీకు"],
        "Tamil":     ["தமிழ்", "சொல்லு", "என்ன", "எப்படி"],
        "Kannada":   ["ಕನ್ನಡ", "ಹೇಳು", "ಏನು", "ಹೇಗೆ"],
        "Malayalam": ["മലയാളം", "പറയൂ", "എന്ത്", "എങ്ങനെ"],
        "Marathi":   ["मराठी", "सांग", "काय", "कसे"],
        "Gujarati":  ["ગુજરાતી", "કહો", "શું"],
        "Bengali":   ["বাংলা", "বলো", "কী"],
        "Punjabi":   ["ਪੰਜਾਬੀ", "ਦੱਸੋ", "ਕੀ"],
        "Urdu":      ["اردو", "بتاؤ", "کیا"],
    }
    for lang, keywords in lang_keywords.items():
        for word in keywords:
            if word in text:
                return lang

    # Check Unicode script ranges
    unicode_ranges = {
        "Tamil":     ('\u0B80', '\u0BFF'),
        "Telugu":    ('\u0C00', '\u0C7F'),
        "Kannada":   ('\u0C80', '\u0CFF'),
        "Malayalam": ('\u0D00', '\u0D7F'),
        "Gujarati":  ('\u0A80', '\u0AFF'),
        "Bengali":   ('\u0980', '\u09FF'),
        "Punjabi":   ('\u0A00', '\u0A7F'),
        "Urdu":      ('\u0600', '\u06FF'),
        "Hindi":     ('\u0900', '\u097F'),
    }
    for lang, (start, end) in unicode_ranges.items():
        for char in text:
            if start <= char <= end:
                return lang

    return "English"


def get_news(topic="India"):
    try:
        if not NEWS_API_KEY:
            return None
        url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("status") == "ok" and data.get("articles"):
            news_text = ""
            for i, a in enumerate(data["articles"][:5], 1):
                news_text += f"{i}. {a['title']} — {a['source']['name']}\n"
            return news_text
    except:
        pass
    return None


def get_weather(city):
    try:
        if not WEATHER_API_KEY:
            return None
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("main"):
            temp = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            desc = data["weather"][0]["description"].capitalize()
            wind = data["wind"]["speed"]
            return f"Weather in {city}: {desc}, Temp: {temp}°C (Feels {feels}°C), Humidity: {humidity}%, Wind: {wind} m/s"
    except:
        pass
    return None


def get_cricket_score():
    try:
        url = "https://api.cricapi.com/v1/currentMatches?apikey=free&offset=0"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("data"):
            scores = ""
            for match in data["data"][:3]:
                scores += f"{match.get('name','Match')}: {match.get('status','In Progress')}\n"
            return scores if scores else None
    except:
        pass
    return None


def get_exchange_rate(from_cur, to_cur, amount):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_cur.upper()}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("rates") and to_cur.upper() in data["rates"]:
            rate = data["rates"][to_cur.upper()]
            converted = round(float(amount) * rate, 2)
            return f"{amount} {from_cur.upper()} = {converted} {to_cur.upper()} (Rate: {rate})"
    except:
        pass
    return None


def get_world_time(timezone_name):
    try:
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        return now.strftime("%A, %d %B %Y — %I:%M %p %Z")
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
        timezone = data.get("timezone", None)

        if not user_input:
            return jsonify({"error": "Message is empty"}), 400

        language = detect_language(user_input)
        lower = user_input.lower()

        if session_id not in conversation_history:
            conversation_history[session_id] = []
        history = conversation_history[session_id]

        extra_context = ""
        random_seed = random.randint(1, 99999)

        # Weather
        if any(w in lower for w in ["weather", "temperature", "rain", "humidity", "climate"]):
            words = user_input.split()
            city = "Hyderabad"
            for i, w in enumerate(words):
                if w.lower() in ["weather", "in", "of", "at"] and i + 1 < len(words):
                    city = words[i + 1]
            weather = get_weather(city)
            if weather:
                extra_context += f"\nWeather data: {weather}\n"

        # News
        if any(w in lower for w in ["news", "latest", "headlines", "breaking", "today"]):
            topic = "India"
            for word in ["cricket", "politics", "technology", "business", "sports", "bollywood", "ipl"]:
                if word in lower:
                    topic = word
                    break
            news = get_news(topic)
            if news:
                extra_context += f"\nLatest {topic} news:\n{news}\n"

        # Time
        if any(w in lower for w in ["time", "date", "day", "clock"]):
            if timezone:
                t = get_world_time(timezone)
                if t:
                    extra_context += f"\nCurrent time: {t}\n"
            else:
                ist = get_world_time("Asia/Kolkata")
                extra_context += f"\nIST: {ist}\n"

        # Currency
        if any(w in lower for w in ["usd", "inr", "sar", "aed", "gbp", "eur", "dollar", "rupee", "riyal", "convert"]):
            import re
            numbers = re.findall(r'\d+\.?\d*', user_input)
            amount = numbers[0] if numbers else "1"
            pairs = [("usd","inr"),("sar","inr"),("aed","inr"),("gbp","inr"),("eur","inr")]
            for f, t in pairs:
                if f in lower:
                    rate = get_exchange_rate(f, t, amount)
                    if rate:
                        extra_context += f"\nCurrency: {rate}\n"
                    break

        # Cricket
        if any(w in lower for w in ["cricket", "ipl", "score", "match"]):
            score = get_cricket_score()
            if score:
                extra_context += f"\nLive Cricket:\n{score}\n"

        # GST
        if any(w in lower for w in ["gst", "tax"]):
            import re
            numbers = re.findall(r'\d+\.?\d*', user_input)
            if len(numbers) >= 2:
                amt = float(numbers[0])
                pct = float(numbers[1])
                gst_amt = round(amt * pct / 100, 2)
                total = round(amt + gst_amt, 2)
                extra_context += f"\nGST: Amount={amt}, GST@{pct}%={gst_amt}, Total={total}\n"

        joke_style = JOKE_STYLES.get(language, JOKE_STYLES["English"])

        system_prompt = f"""You are Genie — the user's BEST FRIEND forever.

⚠️ MOST CRITICAL RULE — LANGUAGE:
The user's language is: {language}
You MUST write your ENTIRE response in {language} ONLY.
- Telugu → write ONLY in Telugu script (తెలుగు లిపి మాత్రమే)
- Hindi → write ONLY in Hindi Devanagari (केवल हिंदी में)
- Tamil → write ONLY in Tamil script (தமிழ் மட்டும்)
- Kannada → write ONLY in Kannada script (ಕನ್ನಡ ಮಾತ್ರ)
- Malayalam → write ONLY in Malayalam script
- Marathi → write ONLY in Marathi Devanagari
- Bengali → write ONLY in Bengali script
- Gujarati → write ONLY in Gujarati script
- Punjabi → write ONLY in Punjabi Gurmukhi script
- Urdu → write ONLY in Urdu script
- English → write ONLY in English
NEVER write in English if language is not English.
NEVER mix languages.
Code examples are the ONLY exception — code stays in English.

⚠️ JOKE RULE:
Unique seed: {random_seed} — generate completely UNIQUE joke every time
Style: {joke_style}
- Setup → unexpected twist → brilliant punchline
- NEVER repeat jokes
- NEVER write jokes in English if language is Telugu/Hindi/Tamil etc
- Write joke label and everything in {language} script

PERSONALITY:
- Talk like a close best friend, not a formal assistant
- Casual, warm, funny, caring
- Telugu friend: "ra", "bro", casual Telugu slang
- Hindi friend: "yaar", "bhai", casual Hindi
- English friend: "buddy", "mate", casual
- Make them feel they are talking to their best friend

{extra_context}

GENERAL:
- Keep conversation warm and engaging
- End with something friendly to continue chat
- Remove all markdown symbols like ** from responses
"""

        history.append({"role": "user", "content": user_input})
        if len(history) > 20:
            history = history[-20:]
            conversation_history[session_id] = history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=1024,
            temperature=0.95
        )

        reply = response.choices[0].message.content
        # Clean markdown
        import re
        reply = re.sub(r'\*\*(.*?)\*\*', r'\1', reply)
        reply = re.sub(r'\*(.*?)\*', r'\1', reply)
        reply = re.sub(r'#{1,6}\s', '', reply)
        reply = re.sub(r'`{1,3}', '', reply)

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
