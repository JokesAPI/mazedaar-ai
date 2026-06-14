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
CRICAPI_KEY = os.getenv("CRICAPI_KEY")  # get free key from cricapi.com
client = OpenAI(api_key=OPENAI_API_KEY)
conversation_history = {}

JOKES = {
    "Telugu": [
        "మాస్టర్: వెంకటేశ్వరరావు గారూ, మీ కొడుకు పరీక్షలో ఎందుకు ఫెయిల్ అయ్యాడు?\nతండ్రి: సార్, వాడు చాలా నిజాయితీగా ఉంటాడు.\nమాస్టర్: అంటే?\nతండ్రి: పక్కవాడి పేపర్ చూడలేదు సార్! 😄",
        "డాక్టర్: మీకు ఇంకా ఆరు నెలలే ఉన్నాయి.\nపేషెంట్: డాక్టర్ గారూ, బిల్లు కట్టలేను.\nడాక్టర్: సరే, మరో ఆరు నెలలు ఇస్తాను! 😄",
        "టీచర్: సుబ్బారావు గారూ, మీ అబ్బాయి స్కూల్‌కి ఎందుకు రాలేదు?\nతండ్రి: జ్వరంగా ఉంది సార్.\nటీచర్: నిన్న కూడా అదే చెప్పారు.\nతండ్రి: వాడికి చాలా నిదానంగా నయమవుతుందండి! 😄",
        "భర్త: ఏమండీ, ఈ రోజు వంట చాలా బాగుంది!\nభార్య: నిజంగానా?\nభర్త: అవునండీ, హోటల్‌లో నేర్పించారా? 😄",
        "విద్యార్థి: సార్, నేను ఎందుకు ఫెయిల్ అయ్యాను? 35 మార్కులు వచ్చాయి.\nటీచర్: 36 వస్తే పాస్.\nవిద్యార్థి: మీరు 36 రాయొచ్చు కదా సార్?\nటీచర్: నువ్వు పరీక్షలో 36 రాయొచ్చు కదా! 😄",
        "పోలీస్: ఆగండి! ఎందుకు అంత వేగంగా వెళ్తున్నారు?\nడ్రైవర్: బ్రేకులు పని చేయట్లేదు అయ్యా.\nపోలీస్: అందుకే ఆపమని సైన్ చేశాను!\nడ్రైవర్: అందుకే ఆపలేదు అయ్యా! 😄",
        "అబ్బాయి: నాన్నగారూ, నాకు బైక్ కొనిపెట్టండి.\nనాన్న: చదువు పూర్తయిన తర్వాత.\nఅబ్బాయి: అప్పటికి నడవడానికి కూడా కష్టంగా ఉంటుందండి! 😄",
        "భార్య: విన్నారా? పక్కింటి వారు రోజూ గొడవ పడతారు.\nభర్త: వారిద్దరూ అదృష్టవంతులు.\nభార్య: గొడవ పడితే అదృష్టమా?\nభర్త: కనీసం మాట్లాడుకుంటున్నారు కదా! 😄",
    ],
    "Hindi": [
        "टीचर: बताओ, पानी का फॉर्मूला क्या है?\nपप्पू: H-I-J-K-L-M-N-O!\nटीचर: ये क्या है?\nपप्पू: मैडम, आपने ही कहा था H to O! 😄",
        "पत्नी: सुनो जी, आज खाना नहीं बनाऊंगी।\nपति: क्यों?\nपत्नी: डाइट पर हूं।\nपति: तो मैं भी डाइट पर हूं... होटल चलते हैं! 😄",
        "बेटा: पापा, मुझे बाइक चाहिए।\nपापा: पढ़ाई पूरी करो पहले।\nबेटा: तब तक तो उड़ने वाली कारें आ जाएंगी! 😄",
        "मरीज: डॉक्टर साहब, सब मुझे नजरअंदाज करते हैं।\nडॉक्टर: अगला मरीज आए! 😄",
        "टीचर: अगर 5 बच्चे हैं और तुम्हारे पास 5 टॉफी हैं तो?\nपप्पू: सब मेरी!\nटीचर: क्यों?\nपप्पू: क्योंकि बाकी 4 मेरे दोस्त नहीं हैं! 😄",
    ],
    "Tamil": [
        "மாஸ்டர்: ராமு, தண்ணீரின் சூத்திரம் என்ன?\nராமு: H-I-J-K-L-M-N-O சார்!\nமாஸ்டர்: இது என்ன?\nராமு: நீங்களே சொன்னீங்க சார், H to O! 😄",
        "மனைவி: இன்னிக்கு சமைக்க மாட்டேன்.\nகணவன்: ஏன்?\nமனைவி: டயட்டில் இருக்கேன்.\nகணவன்: நானும் டயட்டில் இருக்கேன்... ஹோட்டல் போலாம்! 😄",
        "மகன்: அப்பா, பைக் வேணும்.\nஅப்பா: படிப்பு முடிஞ்சதும் வாங்கிக்குவோம்.\nமகன்: அப்போ நடக்கவே கஷ்டமா இருக்கும்ல! 😄",
        "நோயாளி: டாக்டர், எல்லாரும் என்னை பார்க்கவே மாட்டேங்கிறாங்க.\nடாக்டர்: அடுத்தவர் வாங்க! 😄",
    ],
    "Kannada": [
        "ಮಾಸ್ಟರ್: ರಾಮು, ನೀರಿನ ಸೂತ್ರ ಏನು?\nರಾಮು: H-I-J-K-L-M-N-O ಸರ್!\nಮಾಸ್ಟರ್: ಇದು ಏನು?\nರಾಮು: ನೀವೇ ಹೇಳಿದ್ರಿ ಸರ್, H to O! 😄",
        "ಹೆಂಡತಿ: ಇವತ್ತು ಅಡಿಗೆ ಮಾಡಲ್ಲ.\nಗಂಡ: ಯಾಕೆ?\nಹೆಂಡತಿ: ಡಯೆಟ್ ಮಾಡ್ತಿದ್ದೇನೆ.\nಗಂಡ: ನಾನೂ ಡಯೆಟ್ ಮಾಡ್ತಿದ್ದೇನೆ... ಹೋಟೆಲ್ ಹೋಗೋಣ! 😄",
        "ರೋಗಿ: ಡಾಕ್ಟರ್, ಎಲ್ಲರೂ ನನ್ನನ್ನು ನಿರ್ಲಕ್ಷಿಸುತ್ತಾರೆ.\nಡಾಕ್ಟರ್: ಮುಂದಿನ ರೋಗಿ ಬರಲಿ! 😄",
    ],
    "Malayalam": [
        "ടീച്ചർ: രാമു, വെള്ളത്തിന്റെ ഫോർമുല എന്താ?\nരാമു: H-I-J-K-L-M-N-O ടീച്ചർ!\nടീച്ചർ: ഇതെന്താ?\nരാമു: നിങ്ങൾ തന്നെ പറഞ്ഞല്ലോ, H to O! 😄",
        "ഭാര്യ: ഇന്ന് പാചകം ഇല്ല.\nഭർത്താവ്: എന്തുകൊണ്ട്?\nഭാര്യ: ഡയറ്റ് ആണ്.\nഭർത്താവ്: ഞാനും ഡയറ്റ് ആണ്... ഹോട്ടലിൽ പോകാം! 😄",
    ],
    "Marathi": [
        "मास्तर: राम्या, पाण्याचं सूत्र काय?\nराम्या: H-I-J-K-L-M-N-O सर!\nमास्तर: हे काय आहे?\nराम्या: तुम्हीच सांगितलं सर, H to O! 😄",
        "बायको: आज स्वयंपाक करणार नाही.\nनवरा: का?\nबायको: डाएट आहे.\nनवरा: मी पण डाएट आहे... हॉटेलला जाऊ! 😄",
    ],
    "Bengali": [
        "মাস্টার: রামু, পানির সূত্র কী?\nরামু: H-I-J-K-L-M-N-O স্যার!\nমাস্টার: এটা কী?\nরামু: আপনিই বললেন স্যার, H to O! 😄",
        "বউ: আজ রান্না করব না।\nস্বামী: কেন?\nবউ: ডায়েটে আছি।\nস্বামী: আমিও ডায়েটে আছি... হোটেলে যাই! 😄",
    ],
    "Gujarati": [
        "માસ્તર: રામુ, પાણીનું સૂત્ર શું છે?\nરામુ: H-I-J-K-L-M-N-O સર!\nમાસ્તર: આ શું છે?\nરામુ: તમે જ કહ્યું સર, H to O! 😄",
        "પત્ની: આજે રસોઈ નહીં કરું.\nપતિ: કેમ?\nપત્ની: ડાઈટ પર છું.\nપતિ: હું પણ ડાઈટ પર છું... હોટેલ જઈએ! 😄",
    ],
    "Punjabi": [
        "ਮਾਸਟਰ: ਰਾਮੂ, ਪਾਣੀ ਦਾ ਫਾਰਮੂਲਾ ਕੀ ਹੈ?\nਰਾਮੂ: H-I-J-K-L-M-N-O ਸਰ!\nਮਾਸਟਰ: ਇਹ ਕੀ ਹੈ?\nਰਾਮੂ: ਤੁਸੀਂ ਹੀ ਕਿਹਾ ਸੀ ਸਰ, H to O! 😄",
        "ਪਤਨੀ: ਅੱਜ ਖਾਣਾ ਨਹੀਂ ਬਣਾਵਾਂਗੀ।\nਪਤੀ: ਕਿਉਂ?\nਪਤਨੀ: ਡਾਈਟ 'ਤੇ ਹਾਂ।\nਪਤੀ: ਮੈਂ ਵੀ ਡਾਈਟ 'ਤੇ ਹਾਂ... ਹੋਟਲ ਚੱਲਦੇ ਹਾਂ! 😄",
    ],
    "Urdu": [
        "استاد: رامو، پانی کا فارمولا کیا ہے؟\nرامو: H-I-J-K-L-M-N-O سر!\nاستاد: یہ کیا ہے؟\nرامو: آپ نے ہی کہا تھا سر، H to O! 😄",
        "بیوی: آج کھانا نہیں بناؤں گی۔\nشوہر: کیوں؟\nبیوی: ڈائٹ پر ہوں۔\nشوہر: میں بھی ڈائٹ پر ہوں... ہوٹل چلتے ہیں! 😄",
    ],
    "English": [
        "Teacher: What is the formula for water?\nStudent: H-I-J-K-L-M-N-O!\nTeacher: What is that?\nStudent: You said it yourself — H to O! 😄",
        "Wife: I won't cook today.\nHusband: Why?\nWife: I'm on a diet.\nHusband: Me too... let's go to a restaurant! 😄",
        "Patient: Doctor, everyone ignores me.\nDoctor: Next please! 😄",
        "Son: Dad, I need a bike.\nDad: After you finish studies.\nSon: By then I'll need a walking stick! 😄",
    ]
}


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
        "Kannada":["ಕನ್ನಡ","ಹೇಳು","ಏನು"],
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


def get_weather(city):
    try:
        if not WEATHER_API_KEY: return None
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("main"):
            return f"Weather in {city}: {data['weather'][0]['description'].capitalize()}, Temp: {data['main']['temp']}°C, Feels like: {data['main']['feels_like']}°C, Humidity: {data['main']['humidity']}%"
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
            return f"{amount} {from_cur.upper()} = {converted} {to_cur.upper()} (Live rate: 1 {from_cur.upper()} = {rate} {to_cur.upper()})"
    except: pass
    return None


def get_cricket_score():
    try:
        # Use cricapi.com with key if available
        if CRICAPI_KEY:
            url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"
            r = requests.get(url, timeout=8)
            data = r.json()
            if data.get("data") and len(data["data"]) > 0:
                scores = ""
                for match in data["data"][:5]:
                    name = match.get("name","Match")
                    status = match.get("status","In Progress")
                    score_data = match.get("score",[])
                    score_str = ""
                    for s in score_data:
                        score_str += f"{s.get('inning','')}: {s.get('r',0)}/{s.get('w',0)} ({s.get('o',0)} ov) "
                    scores += f"{name}\n{score_str}\nStatus: {status}\n\n"
                return scores
    except: pass

    # Fallback: cricket news
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


def get_train_info(train_number):
    try:
        # Using free RailwayAPI
        url = f"https://www.railyatri.in/api/1.3/train_search.json?train_num={train_number}&locale=en"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, timeout=8, headers=headers)
        data = r.json()
        if data.get("train_schedule"):
            schedule = data["train_schedule"]
            name = schedule.get("train_name", "Unknown")
            stations = schedule.get("station_details", [])
            result = f"Train {train_number} - {name}\n"
            result += "Route:\n"
            for s in stations[:10]:
                result += f"  {s.get('station_name','')} ({s.get('station_code','')}) — Arr: {s.get('arr_time','--')} Dep: {s.get('dep_time','--')}\n"
            return result
    except: pass

    # Fallback: use AI knowledge about train
    return f"Train {train_number}: Please check NTES app (railmadad.indianrailways.gov.in) or IRCTC for live train running status and route details."


def check_pnr(pnr_number):
    try:
        url = f"https://www.railyatri.in/api/1.3/pnr_status.json?pnr={pnr_number}&locale=en"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, timeout=8, headers=headers)
        data = r.json()
        if data.get("pnr_status"):
            p = data["pnr_status"]
            result = f"PNR: {pnr_number}\n"
            result += f"Train: {p.get('train_num','')} - {p.get('train_name','')}\n"
            result += f"Date: {p.get('doj','')}\n"
            result += f"From: {p.get('from_station','')} To: {p.get('to_station','')}\n"
            result += f"Class: {p.get('class','')}\n"
            passengers = p.get("pax_details",[])
            for i, pax in enumerate(passengers, 1):
                result += f"Passenger {i}: {pax.get('current_status','Unknown')}\n"
            return result
    except: pass
    return f"PNR {pnr_number}: For live PNR status please check:\n- IRCTC app\n- indianrail.gov.in\n- NTES app\n- SMS PNR {pnr_number} to 139"


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
        joke_words = ["joke","jokes","funny","laugh","జోక్","చుటకుల","హాస్యం","चुटकुला","हंसाओ","நகைச்சுவை","ಜೋಕ್","തമാശ","জোকস","ਜੋਕ","مذاق"]
        is_joke = any(w in lower for w in joke_words)

        if is_joke:
            jokes_list = JOKES.get(language, JOKES["English"])
            used_key = f"{session_id}_used_{language}"
            used = conversation_history.get(used_key, [])
            available = [j for j in jokes_list if j not in used]
            if not available:
                available = jokes_list
                conversation_history[used_key] = []
            joke = random.choice(available)
            if used_key not in conversation_history:
                conversation_history[used_key] = []
            conversation_history[used_key].append(joke)

            wrap_prompt = f"""You are Genie, a warm and friendly AI assistant.
Present this joke to the user warmly in {language} ONLY.
Add ONE short friendly line before the joke.
Add ONE short friendly reaction after.
Use respectful polite language always.
Never use slang or disrespectful words.
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
                    extra_context += f"\nWeather data: {weather}\n"

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
                    extra_context += f"\nCurrent time: {t}\n"

            # Currency
            currency_map = {
                "usd":"USD","dollar":"USD","sgd":"SGD","singapore":"SGD",
                "sar":"SAR","riyal":"SAR","saudi":"SAR","aed":"AED","dirham":"AED",
                "gbp":"GBP","pound":"GBP","eur":"EUR","euro":"EUR",
                "aud":"AUD","cad":"CAD","jpy":"JPY","yen":"JPY",
                "kwd":"KWD","kuwait":"KWD","qar":"QAR","bhd":"BHD","omr":"OMR",
                "myr":"MYR","malaysia":"MYR","thb":"THB","uae":"AED"
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
                    extra_context += "\nCricket scores not available right now. Check cricbuzz.com or ESPN Cricinfo for live scores.\n"

            # GST
            if any(w in lower for w in ["gst","tax"]):
                numbers_gst = re.findall(r'\d+\.?\d*', user_input)
                if len(numbers_gst) >= 2:
                    amt, pct = float(numbers_gst[0]), float(numbers_gst[1])
                    gst_amt = round(amt * pct / 100, 2)
                    extra_context += f"\nGST: Amount=Rs.{amt}, GST@{pct}%=Rs.{gst_amt}, Total=Rs.{round(amt+gst_amt,2)}\n"

            # Train & PNR
            if any(w in lower for w in ["train","pnr","railway","irctc","rail","రైలు","ट्रेन","ரெயில்"]):
                pnr_match = re.search(r'\b\d{10}\b', user_input)
                train_match = re.search(r'\b\d{4,5}\b', user_input)

                if pnr_match:
                    pnr = pnr_match.group()
                    pnr_info = check_pnr(pnr)
                    extra_context += f"\nPNR Status:\n{pnr_info}\n"
                elif train_match:
                    train_num = train_match.group()
                    train_info = get_train_info(train_num)
                    extra_context += f"\nTrain Info:\n{train_info}\n"
                else:
                    extra_context += "\nFor train info please provide train number (e.g. 12759) or PNR number (10 digits).\n"

            system_prompt = f"""You are Genie — a warm, helpful, and friendly AI assistant.

LANGUAGE LAW — NEVER BREAK:
Detected language: {language}
Reply ONLY in {language}.
Telugu=తెలుగు only, Hindi=हिंदी only, Tamil=தமிழ் only
Kannada=ಕನ್ನಡ only, Malayalam=മലയാളം only
Never use English in non-English responses except for numbers/codes/train info.

RESPECT RULE:
Always use respectful polite language.
Telugu: use మీరు, మీకు, అండి — never రా or నువ్వు with strangers.
Hindi: always use आप, आपको.

PERSONALITY:
Warm, helpful, friendly like a trusted knowledgeable friend.
Encouraging and supportive always.

{extra_context}

RULES:
No markdown ** or ## or backticks.
Each sentence on new line.
Give accurate info only — if unsure say honestly.
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
