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

# ✅ QUALITY TELUGU JOKES - Clear, Funny, Respectful
JOKES = {
    "Telugu": [
        "మాస్టర్: వెంకటేశ్వరరావు గారూ, మీ కొడుకు పరీక్షలో ఎందుకు ఫెయిల్ అయ్యాడు?\nతండ్రి: సార్, వాడు చాలా నిజాయితీగా ఉంటాడు.\nమాస్టర్: అంటే?\nతండ్రి: పక్కవాడి పేపర్ చూడలేదు సార్! 😄",
        "డాక్టర్: మీకు ఇంకా ఆరు నెలలే ఉన్నాయి.\nపేషెంట్: డాక్టర్ గారూ, బిల్లు కట్టలేను.\nడాక్టర్: సరే, మరో ఆరు నెలలు ఇస్తాను! 😄",
        "టీచర్: సుబ్బారావు గారూ, మీ అబ్బాయి స్కూల్‌కి ఎందుకు రాలేదు?\nతండ్రి: జ్వరంగా ఉంది సార్.\nటీచర్: నిన్న కూడా అదే చెప్పారు.\nతండ్రి: వాడికి చాలా నిదానంగా నయమవుతుందండి! 😄",
        "భర్త: ఏమండీ, ఈ రోజు వంట చాలా బాగుంది!\nభార్య: నిజంగానా?\nభర్త: అవునండీ, హోటల్‌లో నేర్పించారా? 😄",
        "అమ్మ: బేటా, నువ్వు ఎప్పుడు పెళ్ళి చేసుకుంటావు?\nకొడుకు: అమ్మా, పెళ్ళికి ముందు నేను బాగా నిద్రపోతాను.\nఅమ్మ: పెళ్ళి తర్వాత?\nకొడుకు: తర్వాత అమ్మ ప్రశ్నలే నిద్రపోనివ్వవు! 😄",
        "విద్యార్థి: సార్, మీరు చెప్పింది నాకు అర్థం కాలేదు.\nటీచర్: ఎందుకు?\nవిద్యార్థి: మీరు చెప్పేటప్పుడు నేను నిద్రపోయాను సార్! 😄",
        "పోలీస్: ఆగండి! ఎందుకు అంత వేగంగా వెళ్తున్నారు?\nడ్రైవర్: బ్రేకులు పని చేయట్లేదు అయ్యా.\nపోలీస్: అందుకే ఆపమని సైన్ చేశాను!\nడ్రైవర్: అందుకే ఆపలేదు అయ్యా! 😄",
        "భార్య: విన్నారా? పక్కింటి వారు రోజూ గొడవ పడతారు.\nభర్త: వారిద్దరూ అదృష్టవంతులు.\nభార్య: గొడవ పడితే అదృష్టమా?\nభర్త: కనీసం మాట్లాడుకుంటున్నారు కదా! 😄",
        "విద్యార్థి: సార్, నేను ఎందుకు ఫెయిల్ అయ్యాను? 35 మార్కులు వచ్చాయి.\nటీచర్: 36 వస్తే పాస్.\nవిద్యార్థి: మీరు 36 రాయొచ్చు కదా సార్?\nటీచర్: నువ్వు పరీక్షలో 36 రాయొచ్చు కదా! 😄",
        "అబ్బాయి: నాన్నగారూ, నాకు బైక్ కొనిపెట్టండి.\nనాన్న: చదువు పూర్తయిన తర్వాత.\nఅబ్బాయి: అప్పటికి నడవడానికి కూడా కష్టంగా ఉంటుందండి! 😄",
    ],
    "Hindi": [
        "टीचर: बताओ, पानी का फॉर्मूला क्या है?\nपप्पू: H-I-J-K-L-M-N-O!\nटीचर: ये क्या है?\nपप्पू: मैडम, आपने ही कहा था H to O! 😄",
        "पत्नी: सुनो जी, आज खाना नहीं बनाऊंगी।\nपति: क्यों?\nपत्नी: डाइट पर हूं।\nपति: तो मैं भी डाइट पर हूं... होटल चलते हैं! 😄",
        "डॉक्टर: आपको आराम चाहिए।\nमरीज: ठीक है।\nडॉक्टर: और ये दवाई भी लेना।\nमरीज: डॉक्टर साहब, आराम करूं या दवाई लूं? 😄",
        "बेटा: पापा, मुझे बाइक चाहिए।\nपापा: पढ़ाई पूरी करो पहले।\nबेटा: तब तक तो उड़ने वाली कारें आ जाएंगी! 😄",
        "टीचर: अगर 5 बच्चे हैं और तुम्हारे पास 5 टॉफी हैं तो?\nपप्पू: सब मेरी!\nटीचर: क्यों?\nपप्पू: क्योंकि बाकी 4 मेरे दोस्त नहीं हैं! 😄",
        "मरीज: डॉक्टर साहब, सब मुझे नजरअंदाज करते हैं।\nडॉक्टर: अगला मरीज आए! 😄",
    ],
    "Tamil": [
        "மாஸ்டர்: ராமு, தண்ணீரின் சூத்திரம் என்ன?\nராமு: H-I-J-K-L-M-N-O சார்!\nமாஸ்டர்: இது என்ன?\nராமு: நீங்களே சொன்னீங்க சார், H to O! 😄",
        "மனைவி: இன்னிக்கு சமைக்க மாட்டேன்.\nகணவன்: ஏன்?\nமனைவி: டயட்டில் இருக்கேன்.\nகணவன்: நானும் டயட்டில் இருக்கேன்... ஹோட்டல் போலாம்! 😄",
        "டாக்டர்: உங்களுக்கு ஓய்வு வேணும்.\nபேஷன்ட்: சரி.\nடாக்டர்: இந்த மாத்திரையும் சாப்பிடணும்.\nபேஷன்ட்: ஓய்வா எடுக்கணும் இல்லன்னா மாத்திரையா? 😄",
        "மகன்: அப்பா, பைக் வேணும்.\nஅப்பா: படிப்பு முடிஞ்சதும் வாங்கிக்குவோம்.\nமகன்: அப்போ நடக்கவே கஷ்டமா இருக்கும்ல! 😄",
    ],
    "Kannada": [
        "ಮಾಸ್ಟರ್: ರಾಮು, ನೀರಿನ ಸೂತ್ರ ಏನು?\nರಾಮು: H-I-J-K-L-M-N-O ಸರ್!\nಮಾಸ್ಟರ್: ಇದು ಏನು?\nರಾಮು: ನೀವೇ ಹೇಳಿದ್ರಿ ಸರ್, H to O! 😄",
        "ಹೆಂಡತಿ: ಇವತ್ತು ಅಡಿಗೆ ಮಾಡಲ್ಲ.\nಗಂಡ: ಯಾಕೆ?\nಹೆಂಡತಿ: ಡಯೆಟ್ ಮಾಡ್ತಿದ್ದೇನೆ.\nಗಂಡ: ನಾನೂ ಡಯೆಟ್ ಮಾಡ್ತಿದ್ದೇನೆ... ಹೋಟೆಲ್ ಹೋಗೋಣ! 😄",
        "ರೋಗಿ: ಡಾಕ್ಟರ್, ಎಲ್ಲರೂ ನನ್ನನ್ನು ನಿರ್ಲಕ್ಷಿಸುತ್ತಾರೆ.\nಡಾಕ್ಟರ್: ಮುಂದಿನ ರೋಗಿ ಬರಲಿ! 😄",
    ],
    "Malayalam": [
        "ടീച്ചർ: രാമു, വെള്ളത്തിന്റെ ഫോർമുല എന്താ?\nരാമു: H-I-J-K-L-M-N-O ടീച്ചർ!\nടീച്ചർ: ഇതെന്താ?\nരാമു: നിങ്ങൾ തന്നെ പറഞ്ഞല്ലോ, H to O! 😄",
        "ഭാര്യ: ഇന്ന് പാചകം ഇല്ല.\nഭർത്താവ്: എന്തുകൊണ്ട്?\nഭാര്യ: ഡയറ്റ് ആണ്.\nഭർത്താവ്: ഞാനും ഡയറ്റ് ആണ്... ഹോട്ടലിൽ പോകാം! 😄",
        "രോഗി: ഡോക്ടർ, എല്ലാവരും എന്നെ അവഗണിക്കുന്നു.\nഡോക്ടർ: അടുത്ത രോഗി വരൂ! 😄",
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
        # Try cricbuzz-style free API
        url = "https://api.cricapi.com/v1/currentMatches?apikey=free&offset=0"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("data") and len(data["data"]) > 0:
            scores = ""
            for match in data["data"][:5]:
                name = match.get("name","Match")
                status = match.get("status","In Progress")
                scores += f"{name}: {status}\n"
            return scores if scores else None
    except: pass
    # Fallback — use news API for cricket
    try:
        if NEWS_API_KEY:
            url = f"https://newsapi.org/v2/everything?q=cricket+score+today&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get("articles"):
                scores = ""
                for a in data["articles"][:3]:
                    scores += f"{a['title']}\n"
                return scores
    except: pass
    return None


def get_train_info(train_number):
    try:
        url = f"https://indianrailapi.com/api/v2/TrainSchedule/apikey/free/TrainNumber/{train_number}/"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("TrainSchedule"):
            train = data["TrainSchedule"]
            name = train.get("TrainName","Unknown")
            stations = train.get("Stations",[])
            result = f"Train {train_number} - {name}\n"
            for s in stations[:8]:
                result += f"{s.get('StationName','')} — Arr: {s.get('ArrivalTime','--')} Dep: {s.get('DepartureTime','--')}\n"
            return result
    except: pass
    # Fallback using AI knowledge
    return None


def check_pnr(pnr_number):
    try:
        url = f"https://indianrailapi.com/api/v2/PNRCheck/apikey/free/PNRNumber/{pnr_number}/"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("Pnr"):
            p = data["Pnr"]
            result = f"PNR: {pnr_number}\n"
            result += f"Train: {p.get('TrainNo','')} - {p.get('TrainName','')}\n"
            result += f"Date: {p.get('DateOfJourney','')}\n"
            result += f"From: {p.get('From','')} To: {p.get('To','')}\n"
            for passenger in p.get("PassengerList",[]):
                result += f"Passenger {passenger.get('Number','')}: {passenger.get('CurrentStatus','')}\n"
            return result
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

        # ---- JOKE HANDLING ----
        joke_words = ["joke","jokes","funny","laugh","జోక్","చుటకుల","చుటకులు","హాస్యం","चुटकुला","हंसाओ","நகைச்சுவை","ಜೋಕ್","തമാശ","জোকস","ਜੋਕ","مذاق"]
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
The user wants a joke in {language}.
Present this joke warmly and respectfully in {language} ONLY.
Add ONE friendly line before the joke.
Add ONE friendly line after the joke.
Use respectful language — never use slang like "రా" or "da" or disrespectful words.
No markdown symbols like ** or ##.

Joke to present:
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

            # Currency — supports all major currencies including SGD
            currency_map = {
                "usd":"USD","dollar":"USD","sgd":"SGD","singapore":"SGD",
                "sar":"SAR","riyal":"SAR","saudi":"SAR","aed":"AED","dirham":"AED",
                "uae":"AED","gbp":"GBP","pound":"GBP","eur":"EUR","euro":"EUR",
                "aud":"AUD","cad":"CAD","jpy":"JPY","yen":"JPY","kwd":"KWD",
                "kuwait":"KWD","qar":"QAR","qatar":"QAR","bhd":"BHD","omr":"OMR"
            }
            numbers = re.findall(r'\d+\.?\d*', user_input)
            amount = numbers[0] if numbers else "1"
            for keyword, cur_code in currency_map.items():
                if keyword in lower:
                    rate = get_exchange_rate(cur_code, "INR", amount)
                    if rate:
                        extra_context += f"\nLive Currency Rate: {rate}\n"
                    break

            # Cricket
            if any(w in lower for w in ["cricket","ipl","score","match","t20","test match","odi"]):
                score = get_cricket_score()
                if score:
                    extra_context += f"\nLive Cricket Scores:\n{score}\n"
                else:
                    extra_context += "\nCricket: Could not fetch live scores right now. Please check cricbuzz.com for latest scores.\n"

            # GST
            if any(w in lower for w in ["gst","tax"]):
                numbers_gst = re.findall(r'\d+\.?\d*', user_input)
                if len(numbers_gst) >= 2:
                    amt, pct = float(numbers_gst[0]), float(numbers_gst[1])
                    gst_amt = round(amt * pct / 100, 2)
                    extra_context += f"\nGST Calculation: Amount=₹{amt}, GST@{pct}%=₹{gst_amt}, Total=₹{round(amt+gst_amt,2)}\n"

            # Train info
            train_keywords = ["train","pnr","railway","irctc","rail"]
            if any(w in lower for w in train_keywords):
                # Check for PNR (10 digit number)
                pnr_match = re.search(r'\b\d{10}\b', user_input)
                # Check for train number (4-5 digit number)
                train_match = re.search(r'\b\d{4,5}\b', user_input)

                if pnr_match:
                    pnr = pnr_match.group()
                    pnr_info = check_pnr(pnr)
                    if pnr_info:
                        extra_context += f"\nPNR Status:\n{pnr_info}\n"
                    else:
                        extra_context += f"\nPNR {pnr}: Could not fetch live status. Please check indianrail.gov.in or NTES app for PNR status.\n"
                elif train_match:
                    train_num = train_match.group()
                    train_info = get_train_info(train_num)
                    if train_info:
                        extra_context += f"\nTrain Info:\n{train_info}\n"
                    else:
                        extra_context += f"\nTrain {train_num}: Please check indianrail.gov.in or NTES app for live train status.\n"

            system_prompt = f"""You are Genie — a warm, helpful, and friendly AI assistant.

LANGUAGE LAW — NEVER BREAK:
Detected language: {language}
Reply ONLY in {language}.
Telugu=తెలుగు only, Hindi=हिंदी only, Tamil=தமிழ் only
Kannada=ಕನ್ನಡ only, Malayalam=മലയാളം only
Never use English in non-English responses except for code or numbers.

RESPECT RULE — VERY IMPORTANT:
Always use respectful, polite language.
Telugu: use "మీరు", "మీకు", "అండి" — never "రా", "డా", "నువ్వు" with strangers
Hindi: use "आप", "आपको" — always respectful
All languages: treat user like a respected guest

PERSONALITY:
- Warm, helpful, friendly like a trusted friend
- Never rude or disrespectful
- Encouraging and supportive

{extra_context}

RESPONSE RULES:
- No markdown ** or ## or backticks
- Each sentence on new line
- Give accurate information only
- If data not available, say honestly and suggest where to check
- End warmly
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
