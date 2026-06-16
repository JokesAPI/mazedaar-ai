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
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
NASA_API_KEY = os.getenv("NASA_API_KEY")  # get free from api.nasa.gov

client = OpenAI(api_key=OPENAI_API_KEY)
conversation_history = {}
used_jokes_store = {}
used_quotes_store = {}  # Track used quotes per session


def get_quote(language="English", session_id="default", category="motivational"):
    """Get fresh unique quote - never repeats"""
    try:
        # Try Quotable API (free, no key needed)
        tags = "inspirational|motivational|success|life|wisdom"
        url = f"https://api.quotable.io/quotes/random?tags={tags}&limit=5"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data and isinstance(data, list) and len(data) > 0:
            used_key = f"{session_id}_quotes"
            used = used_quotes_store.get(used_key, [])
            # Pick quote not used before
            for q in data:
                quote_id = q.get("_id","")
                if quote_id not in used:
                    used.append(quote_id)
                    used_quotes_store[used_key] = used[-20:]  # keep last 20
                    return f'"{q.get("content","")}" — {q.get("author","")}'
            # If all used, just pick first
            q = data[0]
            return f'"{q.get("content","")}" — {q.get("author","")}'
    except: pass

    # Fallback — AI generated quote
    prompt = f"""Generate ONE unique {category} quote in {language}.
Format: "Quote text" — Author Name
Make it genuinely inspiring and meaningful.
Different from common overused quotes.
Write ONLY the quote, nothing else."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=150, temperature=1.0
    )
    return response.choices[0].message.content.strip()


def get_space_fact(session_id="default"):
    """Get unique space/astronomy fact every time"""
    used_key = f"{session_id}_space"
    used = used_jokes_store.get(used_key, [])

    topics = [
        "black holes and their extreme gravity",
        "neutron stars and pulsars",
        "the Big Bang and origin of universe",
        "dark matter and dark energy mystery",
        "exoplanets and possibility of alien life",
        "supernovas and stellar explosions",
        "the James Webb Space Telescope discoveries",
        "Mars exploration and Perseverance rover",
        "Jupiter's Great Red Spot storm",
        "Saturn's rings composition",
        "Voyager 1 in interstellar space",
        "the Milky Way galaxy structure",
        "time dilation near black holes",
        "asteroid belt and meteorites",
        "solar flares and their Earth impact",
        "moon formation theory",
        "water ice on Mars poles",
        "fastest spinning pulsars",
        "NASA Artemis moon mission",
        "SpaceX Starship developments 2025-2026",
    ]

    available = [t for t in topics if t not in used[-8:]]
    if not available:
        available = topics
        used_jokes_store[used_key] = []

    topic = random.choice(available)
    used_jokes_store[used_key] = used + [topic]

    # Try NASA APOD for real data
    try:
        key = NASA_API_KEY if NASA_API_KEY else "DEMO_KEY"
        # Get random date for variety
        import random as rnd
        year = rnd.choice([2023, 2024, 2025])
        month = rnd.randint(1, 12)
        day = rnd.randint(1, 28)
        date_str = f"{year}-{month:02d}-{day:02d}"
        url = f"https://api.nasa.gov/planetary/apod?api_key={key}&date={date_str}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("title") and data.get("explanation"):
            result = f"Space & Astronomy — {data.get('title','')}\n"
            result += f"Date: {data.get('date','')}\n"
            result += f"{data.get('explanation','')[:400]}...\n"
            if data.get("url"):
                result += f"View: {data.get('url','')}\n"
            return result
    except: pass

    # Fallback — AI generated space fact
    prompt = f"""Share ONE amazing, mind-blowing fact about: {topic}
    Make it WOW factor — something most people don't know.
    Include specific numbers, distances, or comparisons to make it fascinating.
    Keep it 3-4 sentences only.
    End with one thought-provoking question."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=250, temperature=0.9
    )
    return f"Space & Astronomy — {topic.title()}:\n{response.choices[0].message.content.strip()}"


def get_nasa_mars():
    """Get NASA Mars Rover photos info"""
    try:
        key = NASA_API_KEY if NASA_API_KEY else "DEMO_KEY"
        url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key={key}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("latest_photos") and len(data["latest_photos"]) > 0:
            photo = data["latest_photos"][0]
            rover = photo.get("rover",{})
            result = f"NASA Mars Rover — Curiosity:\n"
            result += f"Latest Photo Date: {photo.get('earth_date','')}\n"
            result += f"Camera: {photo.get('camera',{}).get('full_name','')}\n"
            result += f"Rover Status: {rover.get('status','')}\n"
            result += f"Total Photos Taken: {rover.get('total_photos',0)}\n"
            result += f"Photo URL: {photo.get('img_src','')}\n"
            return result
    except: pass
    return None

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
                name = d.get("train_name", train_number)
                source = d.get("source_stn_name", "")
                dest = d.get("dest_stn_name", "")
                run_days = d.get("run_days", "")
                title = d.get("title", "")

                result = f"Train {train_number} — {name}\n"
                result += f"Route: {source} → {dest}\n"
                result += f"Runs on: {run_days}\n"
                result += f"Status: {title}\n\n"
                result += "Major Stops:\n"

                # Get stations from previous_stations list
                stations = d.get("previous_stations", [])
                for s in stations:
                    stn = s.get("station_name", "")
                    sta = s.get("sta", "--")
                    std = s.get("std", "--")
                    platform = s.get("platform_number", "")
                    result += f"  {stn} | Arr: {sta} | Dep: {std} | Platform: {platform}\n"

                # Add destination
                result += f"  {dest} (Destination)\n"
                return result
    except Exception as e:
        print(f"Train API error: {e}")

    # Fallback — AI knowledge
    prompt = f"""Give the complete route and schedule of Indian train number {train_number}.
Include train name, all major stations with arrival and departure times.
Format clearly station by station."""
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
 

        # RIDDLE HANDLING
        riddle_words = ["riddle","riddles","puzzle","brain","బుర్రకు","పజిల్","पहेली","புதிர்"]
        is_riddle = any(w in lower for w in riddle_words)
        is_answer_request = any(w in lower for w in ["answer","reveal","tell me","solution","సమాధానం","जवाब","விடை"])

        if is_riddle and not is_joke:
            used_key = f"{session_id}_riddles"
            used = used_jokes_store.get(used_key, [])
            riddle_topics = [
                "animals","time","shadow","mirror","silence","fire","wind",
                "rain","river","mountain","book","keyboard","clock","candle",
                "ice","music","dream","memory","eye","tooth"
            ]
            available = [t for t in riddle_topics if t not in used[-8:]]
            if not available:
                available = riddle_topics
                used_jokes_store[used_key] = []
            topic = random.choice(available)
            used_jokes_store[used_key] = used + [topic]

            seed = random.randint(1, 99999)
            prompt = f"""Create ONE unique clever riddle about the theme: {topic}
Seed: {seed}
Language: {language} — write riddle ONLY in {language}
Format:
Line 1-3: The riddle clues only
DO NOT show the answer — hide it
Last line: "Can you guess? Reply 'answer' to know!"
Make it clever but solvable. Never repeat common riddles."""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                max_tokens=200, temperature=1.0
            )
            reply = response.choices[0].message.content.strip()
            reply = re.sub(r'\*\*(.*?)\*\*', r'\1', reply)
            reply = re.sub(r'#{1,6}\s?', '', reply)
            history.append({"role":"assistant","content":reply})
            conversation_history[session_id] = history
            return jsonify({"response": reply, "language_detected": language})
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

            # Quote of the Day
            quote_words = ["quote","quotes","motivation","motivational","inspire","inspiration","thought","wisdom","జ్ఞానం","प्रेरणा","உந்துதல்"]
            if any(w in lower for w in quote_words):
                category = "motivational"
                for word in ["success","life","wisdom","happiness","leadership","love","friendship"]:
                    if word in lower:
                        category = word
                        break
                quote = get_quote(language, session_id, category)
                if quote:
                    extra_context += f"\nQuote of the Day ({category}):\n{quote}\n"

            # Space & Astronomy
            nasa_words = ["nasa","space","astronomy","planet","mars","moon","star","galaxy","universe","cosmos","అంతరిక్షం","अंतरिक्ष","space","rocket"]
            if any(w in lower for w in nasa_words):
                space_data = get_space_fact(session_id)
                if space_data:
                    extra_context += f"\n{space_data}\n"

            # Train & PNR — redirect to official sources
            if any(w in lower for w in ["train","pnr","railway","irctc","రైలు","ट्रेन","ரெயில்"]):
                pnr_match = re.search(r'\b\d{10}\b', user_input)
                train_match = re.search(r'\b\d{4,5}\b', user_input)
                if pnr_match:
                    pnr = pnr_match.group()
                    extra_context += f"""
PNR {pnr} — Guide user to check via these official methods:
1. SMS: PNR {pnr} to 139 (free, instant)
2. Website: irctc.co.in
3. App: NTES (National Train Enquiry System)
4. App: Where is my Train
5. Call: 139 (24x7 free helpline)
"""
                elif train_match:
                    train_num = train_match.group()
                    extra_context += f"""
Train {train_num} — Guide user and share any knowledge about this train:
Also suggest:
1. ntes.indianrail.gov.in for live status
2. Where is my Train app
3. RailYatri app
4. Call 139 for info
"""
                else:
                    extra_context += "\nFor train info provide train number (4-5 digits). For PNR provide 10-digit PNR number.\n"

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


@app.route("/debug-pnr/<pnr_number>", methods=["GET"])
def debug_pnr(pnr_number):
    try:
        if not RAPIDAPI_KEY:
            return jsonify({"error": "RAPIDAPI_KEY not set"})
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "irctc1.p.rapidapi.com"
        }
        url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"
        r = requests.get(url, headers=headers, params={"pnrNumber": pnr_number}, timeout=10)
        return jsonify({"status": r.status_code, "response": r.json()})
    except Exception as e:
        return jsonify({"error": str(e)})


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
