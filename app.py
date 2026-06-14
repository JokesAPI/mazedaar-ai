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
CRICAPI_KEY = os.getenv("CRICAPI_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # get free from rapidapi.com

client = OpenAI(api_key=OPENAI_API_KEY)
conversation_history = {}

# Track used AI jokes per session to avoid repeats
used_jokes_store = {}

def detect_language(text):
    text_lower = text.lower()
    explicit = {
        "telugu":"Telugu","hindi":"Hindi","tamil":"Tamil","kannada":"Kannada",
        "malayalam":"Malayalam","marathi":"Marathi","gujarati":"Gujarati",
        "bengali":"Bengali","punjabi":"Punjabi","urdu":"Urdu","english":"English",
    }
    for keyword, lang in explicit.items():
        if keyword in text_lower:
            return lang
    lang_keywords = {
        "Hindi":["हिंदी","मजेदार","बताओ","क्या","कैसे"],
        "Telugu":["తెలుగు","చెప్పు","జోక్","ఏమిటి"],
        "Tamil":["தமிழ்","சொல்லு","என்ன"],
        "Kannada":["ಕನ್ನಡ","ಹೇಳು","ಏನు"],
        "Malayalam":["മലയാളം","പറയൂ","എന്ത്"],
        "Marathi":["मराठी","सांग","काय"],
        "Gujarati":["ગુજરાતી","કહો"],
        "Bengali":["বাংলা","বলো"],
        "Punjabi":["ਪੰਜਾਬੀ","ਦੱਸੋ"],
        "Urdu":["اردو","بتاؤ"],
    }
    for lang, keywords in lang_keywords.items():
        for word in keywords:
            if word in text:
                return lang
    unicode_ranges = {
        "Tamil":('\u0B80','\u0BFF'),"Telugu":('\u0C00','\u0C7F'),
        "Kannada":('\u0C80','\u0CFF'),"Malayalam":('\u0D00','\u0D7F'),
        "Gujarati":('\u0A80','\u0AFF'),"Bengali":('\u0980','\u09FF'),
        "Punjabi":('\u0A00','\u0A7F'),"Urdu":('\u0600','\u06FF'),
        "Hindi":('\u0900','\u097F'),
    }
    for lang,(start,end) in unicode_ranges.items():
        for char in text:
            if start <= char <= end:
                return lang
    return "English"


def get_english_joke():
    """Fetch fresh joke from JokeAPI - completely free, no key needed"""
    try:
        url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,racist,sexist,explicit&type=twopart"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("setup") and data.get("delivery"):
            return f"{data['setup']}\n{data['delivery']} 😄"
    except: pass
    try:
        url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,racist,sexist,explicit&type=single"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("joke"):
            return data["joke"] + " 😄"
    except: pass
    return None


def get_ai_joke(language, session_id):
    """Generate fresh unique joke using AI for Indian languages"""
    used_key = f"{session_id}_{language}_jokes"
    used = used_jokes_store.get(used_key, [])

    # Joke topics to rotate
    topics = [
        "teacher and student in school",
        "husband and wife at home",
        "doctor and patient in hospital",
        "father and son",
        "neighbor conversation",
        "shop owner and customer",
        "mother and child",
        "boss and employee",
        "friends talking",
        "old man and youngster"
    ]

    # Pick topic not recently used
    available_topics = [t for t in topics if t not in used[-5:]]
    if not available_topics:
        available_topics = topics
    topic = random.choice(available_topics)

    used_jokes_store[used_key] = used + [topic]

    language_instructions = {
        "Telugu": "Write ONLY in Telugu script (తెలుగు). Use simple everyday Telugu words. Characters: use names like రాము, సోము, వెంకటేశ్వరరావు, సుబ్బారావు.",
        "Hindi": "Write ONLY in Hindi Devanagari script. Use simple everyday Hindi. Characters: use names like राम, मोहन, पप्पू, सुरेश.",
        "Tamil": "Write ONLY in Tamil script (தமிழ்). Use simple everyday Tamil. Characters: use names like ராமு, மோகன், கண்ணன்.",
        "Kannada": "Write ONLY in Kannada script (ಕನ್ನಡ). Use simple everyday Kannada. Characters: use names like ರಾಮು, ಮೋಹನ್.",
        "Malayalam": "Write ONLY in Malayalam script (മലയാളം). Use simple everyday Malayalam. Characters: use names like രാമു, മോഹൻ.",
        "Marathi": "Write ONLY in Marathi Devanagari script. Use simple everyday Marathi.",
        "Bengali": "Write ONLY in Bengali script (বাংলা). Use simple everyday Bengali.",
        "Gujarati": "Write ONLY in Gujarati script (ગુજરાતી). Use simple everyday Gujarati.",
        "Punjabi": "Write ONLY in Punjabi Gurmukhi script (ਪੰਜਾਬੀ). Use simple everyday Punjabi.",
        "Urdu": "Write ONLY in Urdu script (اردو). Use simple everyday Urdu.",
    }

    lang_instruction = language_instructions.get(language, "Write in English.")

    prompt = f"""Create ONE short funny joke about: {topic}

Rules:
1. {lang_instruction}
2. Maximum 5-6 lines only
3. Format: short situation setup (1-2 lines) → character A says something → character B gives UNEXPECTED funny reply
4. The last line must be the punchline — funny and surprising
5. Use simple words — a 10 year old must understand
6. Use respectful language — no slang
7. Do NOT add any title or label like "Joke:" — just write the joke directly
8. Make it genuinely funny with a clever twist

Write ONLY the joke, nothing else."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=1.0
    )
    return response.choices[0].message.content.strip()


def get_train_info(train_number):
    """Get train schedule using irctc1.p.rapidapi.com"""
    try:
        if RAPIDAPI_KEY:
            url = "https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus"
            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "irctc1.p.rapidapi.com"
            }
            params = {"trainNo": train_number, "startDay": "1"}
            r = requests.get(url, headers=headers, params=params, timeout=10)
            data = r.json()
            if data.get("status") and data.get("data"):
                d = data["data"]
                name = d.get("trainName", train_number)
                stations = d.get("stationList", [])
                result = f"Train {train_number} — {name}\n\nStation List:\n"
                for s in stations[:15]:
                    stn = s.get("stationName", "")
                    arr = s.get("schArrival", "--")
                    dep = s.get("schDeparture", "--")
                    result += f"  {stn} | Arr: {arr} | Dep: {dep}\n"
                return result

            # Try schedule endpoint
            url2 = "https://irctc1.p.rapidapi.com/api/v3/getTrainSchedule"
            params2 = {"trainNo": train_number}
            r2 = requests.get(url2, headers=headers, params=params2, timeout=10)
            data2 = r2.json()
            if data2.get("status") and data2.get("data"):
                d = data2["data"]
                name = d.get("trainName", train_number)
                stations = d.get("stationList", [])
                result = f"Train {train_number} — {name}\n\nRoute:\n"
                for s in stations[:15]:
                    stn = s.get("stationName", "")
                    arr = s.get("arrivalTime", "--")
                    dep = s.get("departureTime", "--")
                    day = s.get("dayCount", "")
                    result += f"  {stn} | Arr: {arr} | Dep: {dep} | Day {day}\n"
                return result
    except Exception as e:
        print(f"Train API error: {e}")

    # Fallback — AI knowledge
    prompt = f"""Give the complete route and schedule of Indian train number {train_number}.
Include train name, all major stations with arrival and departure times.
Format clearly station by station.
If you don't know this specific train number, say so."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600, temperature=0
    )
    return response.choices[0].message.content.strip()


def check_pnr(pnr_number):
    """Check PNR status using irctc1.p.rapidapi.com"""
    try:
        if RAPIDAPI_KEY:
            url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"
            headers = {
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": "irctc1.p.rapidapi.com"
            }
            params = {"pnrNumber": pnr_number}
            r = requests.get(url, headers=headers, params=params, timeout=10)
            data = r.json()
            if data.get("status") and data.get("data"):
                p = data["data"]
                result = f"PNR: {pnr_number}\n"
                result += f"Train: {p.get('trainNumber','')} — {p.get('trainName','')}\n"
                result += f"Date: {p.get('dateOfJourney','')}\n"
                result += f"From: {p.get('sourceStation','')} → To: {p.get('destinationStation','')}\n"
                result += f"Class: {p.get('class','')}\n"
                result += f"Chart: {p.get('chartPrepared','Not Prepared')}\n"
                passengers = p.get("passengerList", [])
                for i, pax in enumerate(passengers, 1):
                    booking = pax.get('bookingStatus','')
                    current = pax.get('currentStatus','')
                    result += f"Passenger {i}: Booked={booking} | Current={current}\n"
                return result
    except Exception as e:
        print(f"PNR API error: {e}")

    return f"""PNR {pnr_number} — Live status check failed.

Check your PNR status here:
1. SMS: PNR {pnr_number} to 139
2. Website: indianrail.gov.in
3. App: IRCTC Rail Connect
4. App: NTES
5. Call: 139 (24x7)"""


def get_weather(city):
    try:
        if not WEATHER_API_KEY: return None
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("main"):
            return f"Weather in {city}: {data['weather'][0]['description'].capitalize()}, Temp: {data['main']['temp']}°C, Feels: {data['main']['feels_like']}°C, Humidity: {data['main']['humidity']}%"
    except: pass
    return None


def get_exchange_rate(from_cur, to_cur, amount="1"):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_cur.upper()}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("rates") and to_cur.upper() in data["rates"]:
            rate = data["rates"][to_cur.upper()]
            converted = round(float(amount) * rate, 2)
            return f"{amount} {from_cur.upper()} = {converted} {to_cur.upper()} (Rate: 1 {from_cur.upper()} = {rate} {to_cur.upper()})"
    except: pass
    return None


def get_cricket_score():
    try:
        if CRICAPI_KEY:
            url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"
            r = requests.get(url, timeout=8)
            data = r.json()
            if data.get("data"):
                scores = ""
                for match in data["data"][:5]:
                    name = match.get("name","Match")
                    status = match.get("status","")
                    score_data = match.get("score",[])
                    score_str = " | ".join([f"{s.get('inning','')}: {s.get('r',0)}/{s.get('w',0)} ({s.get('o',0)} ov)" for s in score_data])
                    scores += f"{name}\n{score_str}\n{status}\n\n"
                return scores if scores.strip() else None
    except: pass
    try:
        if NEWS_API_KEY:
            url = f"https://newsapi.org/v2/everything?q=cricket+score+india&language=en&sortBy=publishedAt&pageSize=4&apiKey={NEWS_API_KEY}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get("articles"):
                result = "Latest Cricket News:\n"
                for a in data["articles"][:4]:
                    result += f"- {a['title']}\n"
                return result
    except: pass
    return None


def get_news(topic="India"):
    try:
        if not NEWS_API_KEY: return None
        url = f"https://newsapi.org/v2/everything?q={topic}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("status") == "ok" and data.get("articles"):
            return "".join([f"{i}. {a['title']} — {a['source']['name']}\n" for i,a in enumerate(data["articles"][:5],1)])
    except: pass
    return None


def get_world_time(timezone_name):
    try:
        tz = pytz.timezone(timezone_name)
        return datetime.now(tz).strftime("%A, %d %B %Y — %I:%M %p %Z")
    except: return None


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        user_input = data.get("message","").strip()
        session_id = data.get("session_id","default")
        timezone = data.get("timezone", None)

        if not user_input:
            return jsonify({"error": "Message is empty"}), 400

        language = detect_language(user_input)
        lower = user_input.lower()

        if session_id not in conversation_history:
            conversation_history[session_id] = []
        history = conversation_history[session_id]

        # JOKE HANDLING
        joke_words = ["joke","jokes","funny","laugh","జోక్","హాస్యం","चुटकुला","हंसाओ","நகைச்சுவை","ಜೋಕ್","തമാശ","জোকস","ਜੋਕ","مذاق"]
        is_joke = any(w in lower for w in joke_words)

        if is_joke:
            # English — use free JokeAPI
            if language == "English":
                joke = get_english_joke()
                if not joke:
                    joke = get_ai_joke("English", session_id)
            else:
                # Indian languages — AI generated fresh joke
                joke = get_ai_joke(language, session_id)

            # Wrap with friendly intro
            wrap_prompt = f"""You are Genie, a warm friendly assistant.
The user wants a joke in {language}.
Present this joke warmly in {language} ONLY.
Add ONE short friendly intro line before.
Add ONE short friendly reaction after.
Use respectful polite language — no slang.
No markdown symbols like ** or ##.

Joke:
{joke}"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":wrap_prompt}],
                max_tokens=400, temperature=0.8
            )
            reply = response.choices[0].message.content

        else:
            extra_context = ""

            # Weather
            if any(w in lower for w in ["weather","temperature","rain","humidity","climate"]):
                words = user_input.split()
                city = "Hyderabad"
                for i,w in enumerate(words):
                    if w.lower() in ["weather","in","of","at"] and i+1 < len(words):
                        city = words[i+1]
                weather = get_weather(city)
                if weather:
                    extra_context += f"\nWeather: {weather}\n"

            # News
            if any(w in lower for w in ["news","latest","headlines","breaking"]):
                topic = "India"
                for word in ["cricket","politics","technology","business","sports","bollywood","ipl"]:
                    if word in lower: topic = word; break
                news = get_news(topic)
                if news:
                    extra_context += f"\nLatest {topic} news:\n{news}\n"

            # Time
            if any(w in lower for w in ["time","date","day","clock"]):
                t = get_world_time(timezone) if timezone else get_world_time("Asia/Kolkata")
                if t:
                    extra_context += f"\nTime: {t}\n"

            # Currency
            currency_map = {
                "usd":"USD","dollar":"USD","sgd":"SGD","singapore":"SGD",
                "sar":"SAR","riyal":"SAR","aed":"AED","dirham":"AED",
                "gbp":"GBP","pound":"GBP","eur":"EUR","euro":"EUR",
                "aud":"AUD","cad":"CAD","jpy":"JPY","kwd":"KWD",
                "qar":"QAR","bhd":"BHD","omr":"OMR","myr":"MYR","thb":"THB"
            }
            numbers = re.findall(r'\d+\.?\d*', user_input)
            amount = numbers[0] if numbers else "1"
            for keyword, cur_code in currency_map.items():
                if keyword in lower:
                    rate = get_exchange_rate(cur_code, "INR", amount)
                    if rate:
                        extra_context += f"\nLive Currency: {rate}\n"
                    break

            # Cricket
            if any(w in lower for w in ["cricket","ipl","score","match","t20","odi","test"]):
                score = get_cricket_score()
                if score:
                    extra_context += f"\nCricket:\n{score}\n"
                else:
                    extra_context += "\nCricket live scores not available. Check cricbuzz.com for latest.\n"

            # GST
            if any(w in lower for w in ["gst","tax"]):
                nums = re.findall(r'\d+\.?\d*', user_input)
                if len(nums) >= 2:
                    amt, pct = float(nums[0]), float(nums[1])
                    gst_amt = round(amt * pct / 100, 2)
                    extra_context += f"\nGST: Amount=Rs.{amt}, GST@{pct}%=Rs.{gst_amt}, Total=Rs.{round(amt+gst_amt,2)}\n"

            # Train & PNR
            if any(w in lower for w in ["train","pnr","railway","irctc","రైలు","ट्रेन","ரெயில்"]):
                pnr_match = re.search(r'\b\d{10}\b', user_input)
                train_match = re.search(r'\b\d{4,5}\b', user_input)
                if pnr_match:
                    pnr_info = check_pnr(pnr_match.group())
                    extra_context += f"\nPNR Status:\n{pnr_info}\n"
                elif train_match:
                    train_info = get_train_info(train_match.group())
                    extra_context += f"\nTrain Info:\n{train_info}\n"
                else:
                    extra_context += "\nPlease provide train number (4-5 digits) or PNR number (10 digits).\n"

            system_prompt = f"""You are Genie — a warm, helpful, friendly AI assistant.

LANGUAGE LAW:
Detected language: {language}
Reply ONLY in {language}.
Telugu=తెలుగు, Hindi=हिंदी, Tamil=தமிழ், Kannada=ಕನ್ನಡ, Malayalam=മലയാളം
Never use English in non-English responses except numbers/codes.

RESPECT RULE:
Always use respectful polite language.
Telugu: మీరు, మీకు, అండి — never రా or నువ్వు.
Hindi: always आप, आपको.

{extra_context}

RULES:
No markdown ** or ## or backticks.
Each sentence on new line.
Give accurate info only.
End response warmly.
"""
            history.append({"role":"user","content":user_input})
            if len(history) > 20:
                history = history[-20:]
                conversation_history[session_id] = history

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":system_prompt}] + history,
                max_tokens=1024, temperature=0.85
            )
            reply = response.choices[0].message.content
            history.append({"role":"assistant","content":reply})
            conversation_history[session_id] = history

        # Clean markdown
        reply = re.sub(r'\*\*(.*?)\*\*', r'\1', reply)
        reply = re.sub(r'\*(.*?)\*', r'\1', reply)
        reply = re.sub(r'#{1,6}\s?', '', reply)
        reply = re.sub(r'`{1,3}[a-z]*\n?', '', reply)
        reply = reply.strip()

        return jsonify({"response": reply, "language_detected": language})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/debug-train/<train_number>", methods=["GET"])
def debug_train(train_number):
    """Debug route to test RapidAPI directly"""
    try:
        if not RAPIDAPI_KEY:
            return jsonify({"error": "RAPIDAPI_KEY not set"})

        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "irctc1.p.rapidapi.com"
        }

        # Test endpoint 1
        url1 = "https://irctc1.p.rapidapi.com/api/v1/liveTrainStatus"
        r1 = requests.get(url1, headers=headers, params={"trainNo": train_number, "startDay": "1"}, timeout=10)

        # Test endpoint 2
        url2 = "https://irctc1.p.rapidapi.com/api/v3/getTrainSchedule"
        r2 = requests.get(url2, headers=headers, params={"trainNo": train_number}, timeout=10)

        return jsonify({
            "rapidapi_key_set": bool(RAPIDAPI_KEY),
            "endpoint1_status": r1.status_code,
            "endpoint1_response": r1.json(),
            "endpoint2_status": r2.status_code,
            "endpoint2_response": r2.json(),
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/clear", methods=["POST"])
def clear_history():
    data = request.get_json()
    session_id = data.get("session_id","default")
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
