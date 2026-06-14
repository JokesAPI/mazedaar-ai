import os
import requests
import random
import re
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

JOKE_FORMATS = {
    "Telugu": """
JOKE RULES FOR TELUGU:
- Write ONLY in simple everyday Telugu script
- Use common names: రాము, సోము, మాస్టర్, డాక్టర్, భార్య, భర్త
- Maximum 5-6 lines only
- Format: short setup → 2-3 dialogues → CLEAR funny punchline
- Last line must make customer laugh immediately
- Use simple Telugu words everyone understands
- NO confusing story, NO long explanation

EXAMPLE FORMAT:
మాస్టర్: రాముడూ, నీ నాన్న ఏం చేస్తారు?
రాముడు: సార్, డాక్టర్.
మాస్టర్: అయితే నువ్వు పెద్దయ్యాక ఏమవుతావు?
రాముడు: సార్, పేషెంట్! 😄
""",
    "Hindi": """
JOKE RULES FOR HINDI:
- Write ONLY in simple Hindi Devanagari script
- Use common names: राम, मोहन, मास्टर जी, डॉक्टर, पत्नी, पति
- Maximum 5-6 lines only
- Format: short setup → 2-3 dialogues → CLEAR funny punchline
- Last line must make customer laugh immediately
- Simple Hindi words everyone understands
- NO confusing story

EXAMPLE FORMAT:
पत्नी: सुनो जी, आज खाना नहीं बनाऊंगी।
पति: क्यों?
पत्नी: डाइट पर हूं।
पति: तो मैं भी डाइट पर हूं... होटल जाते हैं! 😄
""",
    "Tamil": """
JOKE RULES FOR TAMIL:
- Write ONLY in simple Tamil script
- Use common names: ராமு, மோகன், மாஸ்டர், டாக்டர், மனைவி, கணவன்
- Maximum 5-6 lines only
- Format: short setup → 2-3 dialogues → CLEAR funny punchline
- Simple Tamil words everyone understands
- NO confusing story

EXAMPLE FORMAT:
மாஸ்டர்: ராமு, உன் அப்பா என்ன பண்றாங்க?
ராமு: சார், டாக்டர்.
மாஸ்டர்: நீ என்னாவே?
ராமு: சார், பேஷன்ட்! 😄
""",
    "Kannada": """
JOKE RULES FOR KANNADA:
- Write ONLY in simple Kannada script
- Use common names: ರಾಮು, ಸೋಮು, ಮಾಸ್ಟರ್, ಡಾಕ್ಟರ್
- Maximum 5-6 lines only
- Clear funny punchline at the end
- Simple Kannada words everyone understands
""",
    "Malayalam": """
JOKE RULES FOR MALAYALAM:
- Write ONLY in simple Malayalam script
- Use common names: രാമു, മോഹൻ, മാഷ്, ഡോക്ടർ
- Maximum 5-6 lines only
- Clear funny punchline at the end
- Simple Malayalam words everyone understands
""",
    "Marathi": """
JOKE RULES FOR MARATHI:
- Write ONLY in simple Marathi Devanagari script
- Use common names: राम, मोहन, मास्तर, डॉक्टर
- Maximum 5-6 lines only
- Clear funny punchline at the end
- Simple Marathi words everyone understands
""",
    "Bengali": """
JOKE RULES FOR BENGALI:
- Write ONLY in simple Bengali script
- Use common names: রাম, মোহন, মাস্টার, ডাক্তার
- Maximum 5-6 lines only
- Clear funny punchline at the end
""",
    "Gujarati": """
JOKE RULES FOR GUJARATI:
- Write ONLY in simple Gujarati script
- Maximum 5-6 lines only
- Clear funny punchline at the end
""",
    "Punjabi": """
JOKE RULES FOR PUNJABI:
- Write ONLY in simple Punjabi Gurmukhi script
- Maximum 5-6 lines only
- Clear funny punchline at the end
""",
    "Urdu": """
JOKE RULES FOR URDU:
- Write ONLY in simple Urdu script
- Maximum 5-6 lines only
- Clear funny punchline at the end
""",
    "English": """
JOKE RULES FOR ENGLISH:
- Short and punchy — max 4-5 lines
- Clear setup and unexpected punchline
- Everyone must understand immediately

EXAMPLE:
Doctor: You need to stop talking to yourself.
Patient: Why?
Doctor: Because it's annoying all my other patients! 😄
""",
}

def detect_language(text):
    text_lower = text.lower()

    # Check explicit language name first
    explicit = {
        "telugu": "Telugu", "hindi": "Hindi", "tamil": "Tamil",
        "kannada": "Kannada", "malayalam": "Malayalam", "marathi": "Marathi",
        "gujarati": "Gujarati", "bengali": "Bengali", "punjabi": "Punjabi",
        "urdu": "Urdu", "english": "English",
    }
    for keyword, lang in explicit.items():
        if keyword in text_lower:
            return lang

    # Native script keywords
    lang_keywords = {
        "Hindi":     ["हिंदी", "मजेदार", "बताओ", "क्या", "कैसे", "यार"],
        "Telugu":    ["తెలుగు", "చెప్పు", "జోక్", "ఏమిటి"],
        "Tamil":     ["தமிழ்", "சொல்லு", "என்ன"],
        "Kannada":   ["ಕನ್ನಡ", "ಹೇಳು", "ಏನು"],
        "Malayalam": ["മലയാളം", "പറയൂ", "എന്ത്"],
        "Marathi":   ["मराठी", "सांग", "काय"],
        "Gujarati":  ["ગુજરાતી", "કહો"],
        "Bengali":   ["বাংলা", "বলো"],
        "Punjabi":   ["ਪੰਜਾਬੀ", "ਦੱਸੋ"],
        "Urdu":      ["اردو", "بتاؤ"],
    }
    for lang, keywords in lang_keywords.items():
        for word in keywords:
            if word in text:
                return lang

    # Unicode ranges
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
                if w.lower() in ["weather", "in", "of", "at"] and i+1 < len(words):
                    city = words[i+1]
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
        if any(w in lower for w in ["usd","inr","sar","aed","gbp","eur","dollar","rupee","riyal","convert","exchange"]):
            numbers = re.findall(r'\d+\.?\d*', user_input)
            amount = numbers[0] if numbers else "1"
            for f, t in [("usd","inr"),("sar","inr"),("aed","inr"),("gbp","inr"),("eur","inr")]:
                if f in lower:
                    rate = get_exchange_rate(f, t, amount)
                    if rate:
                        extra_context += f"\nCurrency: {rate}\n"
                    break

        # Cricket
        if any(w in lower for w in ["cricket","ipl","score","match"]):
            score = get_cricket_score()
            if score:
                extra_context += f"\nLive Cricket:\n{score}\n"

        # GST
        if any(w in lower for w in ["gst","tax"]):
            numbers = re.findall(r'\d+\.?\d*', user_input)
            if len(numbers) >= 2:
                amt = float(numbers[0])
                pct = float(numbers[1])
                gst_amt = round(amt * pct / 100, 2)
                total = round(amt + gst_amt, 2)
                extra_context += f"\nGST: Amount={amt}, GST@{pct}%={gst_amt}, Total={total}\n"

        joke_format = JOKE_FORMATS.get(language, JOKE_FORMATS["English"])
        is_joke = any(w in lower for w in ["joke","jokes","funny","laugh","జోక్","चुटकुला","நகைச்சுவை","ಜೋಕ್","തമാശ"])

        system_prompt = f"""You are Genie — the user's BEST FRIEND forever.

LANGUAGE LAW — NEVER BREAK THIS:
Detected language: {language}
You MUST write ENTIRE response in {language} ONLY.
Telugu → తెలుగు లిపి మాత్రమే
Hindi → केवल हिंदी देवनागरी
Tamil → தமிழ் மட்டும்
Kannada → ಕನ್ನಡ ಮಾತ್ರ
Malayalam → മലയാളം മാത്രം
Marathi → फक्त मराठी
Bengali → শুধু বাংলা
Gujarati → માત્ર ગુજરાતી
Punjabi → ਸਿਰਫ਼ ਪੰਜਾਬੀ
Urdu → صرف اردو
English → English only
NEVER use English words in non-English responses except for code.

{"JOKE INSTRUCTIONS:" + joke_format if is_joke else ""}

JOKE QUALITY CHECKLIST (only for jokes):
1. Is the setup clear? (who, what situation)
2. Are dialogues short and easy to understand?
3. Does the punchline make sense and is funny?
4. Will a 12-year-old understand it instantly?
5. Is it in {language} script completely?
If any answer is NO — rewrite the joke until all are YES.

PERSONALITY:
- Talk like closest best friend
- Warm, funny, casual
- Telugu: use "రా", "బ్రో", casual Telugu
- Hindi: use "यार", "भाई", casual Hindi
- English: use "buddy", "mate", casual
- Never formal or robotic

{extra_context}

RESPONSE RULES:
- No markdown symbols like ** or ## or ``` in response
- Each sentence on new line for easy reading
- End warmly to continue conversation
- Unique seed {random_seed} — never repeat same joke
"""

        history.append({"role": "user", "content": user_input})
        if len(history) > 20:
            history = history[-20:]
            conversation_history[session_id] = history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=1024,
            temperature=0.9
        )

        reply = response.choices[0].message.content

        # Clean all markdown
        reply = re.sub(r'\*\*(.*?)\*\*', r'\1', reply)
        reply = re.sub(r'\*(.*?)\*', r'\1', reply)
        reply = re.sub(r'#{1,6}\s?', '', reply)
        reply = re.sub(r'`{1,3}[a-z]*\n?', '', reply)
        reply = reply.strip()

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
