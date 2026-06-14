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

# Famous joke authors/styles per language
JOKE_STYLES = {
    "Telugu": "Jandhyala style — sharp wit, family drama, double meaning clean humor, unexpected punchlines like in Jandhyala movies. Characters like innocent people getting confused, teacher-student, husband-wife classic Telugu comedy.",
    "Hindi": "Jaspal Bhatti and Raju Srivastava style — sharp social comedy, common man problems, political satire kept clean, everyday Indian life humor with unexpected twist.",
    "Tamil": "Vadivelu and Vivek style — exaggerated reactions, wordplay, social commentary, unexpected logical twists.",
    "Kannada": "Ramesh Aravind style — smart wordplay, family situations, clever observations about Kannada culture.",
    "Malayalam": "Innocent and Sreenivasan style — subtle humor, intelligent wordplay, everyday Kerala life situations.",
    "Marathi": "Pu La Deshpande style — witty observations, cultural references, intelligent humor.",
    "Bengali": "classic Bangla humor — wordplay, everyday situations, clever observations.",
    "English": "classic English wit — dry humor, unexpected punchlines, clever wordplay like British comedy."
}

def detect_language(text):
    text_lower = text.lower()
    lang_keywords = {
        "Hindi":     ["hindi", "हिंदी", "हिन्दी", "मजेदार", "बताओ", "क्या", "कैसे", "यार", "दोस्त"],
        "Telugu":    ["telugu", "తెలుగు", "చెప్పు", "జోక్", "ఏమిటి", "నీకు", "మనం"],
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
            return f"Weather in {city}: {desc}, Temperature: {temp}°C (Feels like {feels}°C), Humidity: {humidity}%, Wind: {wind} m/s"
    except:
        pass
    return None


def get_cricket_score():
    try:
        # Using cricapi free tier
        url = "https://api.cricapi.com/v1/currentMatches?apikey=free&offset=0"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("data"):
            scores = ""
            for match in data["data"][:3]:
                scores += f"{match.get('name', 'Match')}: {match.get('status', 'In Progress')}\n"
            return scores if scores else None
    except:
        pass
    return None


def get_exchange_rate(from_currency, to_currency, amount):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("rates") and to_currency.upper() in data["rates"]:
            rate = data["rates"][to_currency.upper()]
            converted = round(float(amount) * rate, 2)
            return f"{amount} {from_currency.upper()} = {converted} {to_currency.upper()} (Rate: {rate})"
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

        # Extra context from APIs
        extra_context = ""
        random_joke_seed = random.randint(1, 9999)

        # Weather
        weather_keywords = ["weather", "temperature", "rain", "humidity", "climate", "వాతావరణం", "मौसम", "காலநிலை"]
        if any(w in lower for w in weather_keywords):
            words = user_input.split()
            city = "Hyderabad"
            for i, w in enumerate(words):
                if w.lower() in ["weather", "in", "of", "at"]:
                    if i + 1 < len(words):
                        city = words[i + 1]
            weather = get_weather(city)
            if weather:
                extra_context += f"\nWeather data: {weather}\n"

        # News
        news_keywords = ["news", "latest", "today", "headlines", "breaking", "current", "समाचार", "వార్తలు", "செய்தி"]
        if any(w in lower for w in news_keywords):
            topic = "India"
            for word in ["cricket", "politics", "technology", "business", "sports", "bollywood", "modi", "ipl"]:
                if word in lower:
                    topic = word
                    break
            news = get_news(topic)
            if news:
                extra_context += f"\nLatest news about {topic}:\n{news}\n"

        # Time
        time_keywords = ["time", "date", "day", "clock", "समय", "సమయం", "நேரம்"]
        if any(w in lower for w in time_keywords):
            if timezone:
                t = get_world_time(timezone)
                if t:
                    extra_context += f"\nCurrent time in selected timezone: {t}\n"
            else:
                ist = get_world_time("Asia/Kolkata")
                extra_context += f"\nCurrent IST: {ist}\n"

        # Currency
        currency_keywords = ["usd", "inr", "sar", "aed", "gbp", "eur", "dollar", "rupee", "riyal", "convert", "exchange"]
        if any(w in lower for w in currency_keywords):
            import re
            numbers = re.findall(r'\d+\.?\d*', user_input)
            amount = numbers[0] if numbers else "1"
            if "usd" in lower or "dollar" in lower:
                rate = get_exchange_rate("USD", "INR", amount)
            elif "sar" in lower or "riyal" in lower:
                rate = get_exchange_rate("SAR", "INR", amount)
            elif "aed" in lower or "dirham" in lower:
                rate = get_exchange_rate("AED", "INR", amount)
            elif "gbp" in lower or "pound" in lower:
                rate = get_exchange_rate("GBP", "INR", amount)
            elif "eur" in lower or "euro" in lower:
                rate = get_exchange_rate("EUR", "INR", amount)
            else:
                rate = get_exchange_rate("USD", "INR", "1")
            if rate:
                extra_context += f"\nCurrency: {rate}\n"

        # Cricket
        cricket_keywords = ["cricket", "ipl", "score", "match", "test match", "క్రికెట్", "क्रिकेट"]
        if any(w in lower for w in cricket_keywords):
            score = get_cricket_score()
            if score:
                extra_context += f"\nLive Cricket:\n{score}\n"

        # GST Calculator
        gst_keywords = ["gst", "tax", "జిఎస్టి", "टैक्स"]
        if any(w in lower for w in gst_keywords):
            import re
            numbers = re.findall(r'\d+\.?\d*', user_input)
            if len(numbers) >= 2:
                amount = float(numbers[0])
                rate_pct = float(numbers[1])
                gst_amount = round(amount * rate_pct / 100, 2)
                total = round(amount + gst_amount, 2)
                extra_context += f"\nGST Calculation: Amount={amount}, GST@{rate_pct}%={gst_amount}, Total={total}\n"

        # Joke style
        joke_style = JOKE_STYLES.get(language, JOKE_STYLES["English"])
        is_joke_request = any(w in lower for w in ["joke", "jokes", "funny", "laugh", "జోక్", "చుటకుల", "चुटकुला", "हंसाओ", "நகைச்சுவை"])

        system_prompt = f"""You are Genie — not just an AI, but the user's BEST FRIEND forever (BFF). 

PERSONALITY (MOST IMPORTANT):
- Talk like a close best friend, not a formal assistant
- Use casual friendly language — like texting a best friend
- Add warmth, humor, care in every reply
- Remember things they said and refer back naturally
- Use their language's casual slang and friendly expressions
- Make them feel heard, understood, and valued
- Be funny, witty, supportive like a real best friend
- Never sound robotic or formal

FRIENDSHIP STYLE PER LANGUAGE:
- Telugu: "yaar", "ra", "bro", use casual Telugu friend talk
- Hindi: "yaar", "bhai", "dost", casual Hindi friend style  
- English: "buddy", "mate", "bro/sis", casual friendly English
- Other languages: use that language's casual friend expressions

LANGUAGE RULE:
- Detected: {language} — reply ONLY in {language}
- Keep code examples in English always
- Never mix languages

JOKE RULE (VERY IMPORTANT):
- Joke seed today: {random_joke_seed} — use this to generate a UNIQUE joke every time
- Style: {joke_style}
- NEVER repeat the same joke twice
- Every joke must have: setup → unexpected twist → brilliant punchline
- Jokes must feel FAMOUS quality — like the best jokes from that culture
- After joke, add a fun reaction like "😂 Kaisa laga?" or "😄 Naalo joke cheppagalanu!" etc in their language

RIDDLE RULE:
- Every riddle must be DIFFERENT and UNIQUE
- Give answer only if user asks
- Make riddles clever and fun

FEATURE RULES:
- Weather: present weather data in friendly fun way
- News: summarize news like telling a friend what happened
- Time: tell time casually like "Abhi Saudi mein raat ke 11 baj rahe hain yaar!"
- Currency: give rate with fun comment
- Cricket: react like a cricket fan friend
- GST: calculate and explain simply
- Math: solve step by step like explaining to a friend
- Coding: explain like a senior friend teaching junior

{extra_context}

GENERAL:
- Keep responses natural, warm, conversational
- End with something that keeps conversation going — a question, a joke offer, or a friendly comment
- Make every interaction feel special and memorable
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
