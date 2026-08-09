from __future__ import annotations

LANGUAGES = ["hinglish", "hindi", "en"]

LESSONS: list[dict] = [
    {
        "id": "candles",
        "level": "beginner",
        "minutes": 3,
        "tags": ["basics", "chart"],
        "title": {
            "hinglish": "Candlestick kya hai?",
            "hindi": "कैंडलस्टिक क्या है?",
            "en": "What is a candlestick?",
        },
        "sections": [
            {
                "title": {
                    "hinglish": "Candle ka body aur wick",
                    "hindi": "कैंडल का बॉडी और विक",
                    "en": "The body and the wick",
                },
                "body": {
                    "hinglish": "Har candle ek time period (1 minute, 1 din) dikhata hai. Body open aur close ke beech ka range hai; green/white matlab close open se upar, red/black matlab neeche. Wick (shadow) us period ka high aur low dikhata hai.",
                    "hindi": "हर कैंडल एक समय अवधि (1 मिनट, 1 दिन) दिखाती है। बॉडी ओपन और क्लोज़ के बीच की रेंज है; हरा/सफ़ेद मतलब क्लोज़ ओपन से ऊपर, लाल/काला मतलब नीचे। विक (शैडो) उस अवधि का हाई और लो दिखाती है।",
                    "en": "Each candle shows one time period (1 minute, 1 day). The body is the range between open and close; green/white means close above open, red/black means below. The wick (shadow) shows that period's high and low.",
                },
            },
            {
                "title": {
                    "hinglish": "Patterns simple hote hain",
                    "hindi": "पैटर्न सरल होते हैं",
                    "en": "Patterns are simple",
                },
                "body": {
                    "hinglish": "Long green candle = buyers zor mein. Long red candle = sellers zor mein. Chhoti wick = clear direction; lambi wick = do taraf se pressure (market uncertain).",
                    "hindi": "लंबी हरी कैंडल = खरीदार मज़बूत। लंबी लाल कैंडल = विक्रेता मज़बूत। छोटी विक = साफ़ दिशा; लंबी विक = दोनों तरफ़ दबाव (बाज़ार अनिश्चित)।",
                    "en": "Long green candle = buyers in control. Long red candle = sellers in control. Short wicks = clear direction; long wicks = pressure from both sides (uncertainty).",
                },
            },
            {
                "title": {
                    "hinglish": "Practice tip",
                    "hindi": "अभ्यास टिप",
                    "en": "Practice tip",
                },
                "body": {
                    "hinglish": "Backtest tab mein kisi bhi symbol ke candles dekho aur socho: 'is bar buy karne walon ka haath upar hai ya neeche?' Ye 5 minute ka exercise roz karo.",
                    "hindi": "बैकटेस्ट टैब में किसी भी सिंबल की कैंडल देखो और सोचो: 'इस बार खरीदने वालों का हाथ ऊपर है या नीचे?' यह 5 मिनट का अभ्यास रोज़ करो।",
                    "en": "Open any symbol's candles in the backtest tab and ask: 'are buyers or sellers in control this bar?' Do this 5-minute exercise daily.",
                },
            },
        ],
    },
    {
        "id": "indicators",
        "level": "beginner",
        "minutes": 4,
        "tags": ["indicators", "rsi", "sma", "macd"],
        "title": {
            "hinglish": "Indicators: RSI, SMA, MACD",
            "hindi": "इंडिकेटर्स: RSI, SMA, MACD",
            "en": "Indicators: RSI, SMA, MACD",
        },
        "sections": [
            {
                "title": {
                    "hinglish": "SMA (simple moving average)",
                    "hindi": "SMA (सरल मूविंग एवरेज)",
                    "en": "SMA (simple moving average)",
                },
                "body": {
                    "hinglish": "SMA20 = pichhle 20 din ka average price. Price SMA ke upar = short-term uptrend, neeche = downtrend. Cross ek simple entry idea hai.",
                    "hindi": "SMA20 = पिछले 20 दिनों का औसत प्राइस। प्राइस SMA के ऊपर = अल्पकालिक अपट्रेंड, नीचे = डाउनट्रेंड। क्रॉस एक सरल एंट्री आइडिया है।",
                    "en": "SMA20 = average price of the last 20 days. Price above SMA = short-term uptrend, below = downtrend. A cross is a simple entry idea.",
                },
            },
            {
                "title": {
                    "hinglish": "RSI (14)",
                    "hindi": "RSI (14)",
                    "en": "RSI (14)",
                },
                "body": {
                    "hinglish": "RSI 0 se 100 tak hota hai. 70 se upar = overbought (kharidne walon ka dabav zyada), 30 se neeche = oversold. Ye 'extreme' signal hai, guaranteed price change nahi.",
                    "hindi": "RSI 0 से 100 तक होता है। 70 से ऊपर = ओवरबॉट (खरीदने वालों का दबाव ज़्यादा), 30 से नीचे = ओवरसोल्ड। यह 'एक्सट्रीम' सिग्नल है, गारंटीड प्राइस चेंज नहीं।",
                    "en": "RSI runs 0–100. Above 70 = overbought (buying pressure high), below 30 = oversold. It's an 'extreme' signal, not a guaranteed price change.",
                },
            },
            {
                "title": {
                    "hinglish": "MACD",
                    "hindi": "MACD",
                    "en": "MACD",
                },
                "body": {
                    "hinglish": "MACD momentum dikhata hai. Jab MACD line signal line ke upar hoti hai = buyers control, neeche = sellers. Momentum + trend dono ek saath dekho.",
                    "hindi": "MACD मोमेंटम दिखाता है। जब MACD लाइन सिग्नल लाइन के ऊपर होती है = खरीदार नियंत्रण, नीचे = विक्रेता। मोमेंटम + ट्रेंड दोनों एक साथ देखो।",
                    "en": "MACD shows momentum. MACD line above the signal line = buyers in control, below = sellers. Look at momentum and trend together.",
                },
            },
        ],
    },
    {
        "id": "backtesting",
        "level": "beginner",
        "minutes": 4,
        "tags": ["backtest", "realism"],
        "title": {
            "hinglish": "Backtest karna kyun zaroori hai",
            "hindi": "बैकटेस्ट करना क्यों ज़रूरी है",
            "en": "Why backtesting matters",
        },
        "sections": [
            {
                "title": {
                    "hinglish": "Idea ko pehle test karo",
                    "hindi": "आइडिया को पहले टेस्ट करो",
                    "en": "Test the idea first",
                },
                "body": {
                    "hinglish": "Strategy code likho, purane data pe chalao, phir pata chalta hai idea kaam karta hai ya nahi. Bina backtest ke 'ye kaam karega' sochna guessing hai.",
                    "hindi": "स्ट्रैटेजी कोड लिखो, पुराने डेटा पर चलाओ, फिर पता चलता है आइडिया काम करता है या नहीं। बिना बैकटेस्ट के 'यह काम करेगा' सोचना अनुमान है।",
                    "en": "Write your strategy, run it on historical data, then you know whether the idea works. Thinking 'it will work' without a backtest is just guessing.",
                },
            },
            {
                "title": {
                    "hinglish": "Realism = trust",
                    "hindi": "यथार्थता = विश्वास",
                    "en": "Realism = trust",
                },
                "body": {
                    "hinglish": "Trade Forge brokerage, STT, GST, slippage sab include karta hai. Ye costs chhote lagte hain par saal bhar mein bade returns kha jate hain. Hamesha 'after costs' numbers dekho.",
                    "hindi": "ट्रेड फोर्ज ब्रोकरेज, STT, GST, स्लिपेज सब शामिल करता है। ये लागत छोटी लगती है पर साल भर में बड़े रिटर्न खा जाती है। हमेशा 'आफ्टर कॉस्ट्स' नंबर देखो।",
                    "en": "Trade Forge includes brokerage, STT, GST, slippage. These costs look small but eat big returns over a year. Always read the 'after costs' numbers.",
                },
            },
            {
                "title": {
                    "hinglish": "Overfit se bacho",
                    "hindi": "ओवरफिट से बचो",
                    "en": "Avoid overfitting",
                },
                "body": {
                    "hinglish": "Agar strategy ek symbol pe 90% return deti hai aur doosre pe loss, to wo sirf usi pe 'fit' hai. Alag symbols aur time periods pe test karo. Simple strategy + long sample = confident.",
                    "hindi": "अगर स्ट्रैटेजी एक सिंबल पर 90% रिटर्न देती है और दूसरे पर नुकसान, तो वह सिर्फ़ उसी पर 'फिट' है। अलग सिंबल और समय अवधि पर टेस्ट करो। सरल स्ट्रैटेजी + लंबा सैंपल = आत्मविश्वास।",
                    "en": "If a strategy gives 90% on one symbol and loses on another, it's overfit to that one. Test across symbols and periods. Simple strategy + long sample = confidence.",
                },
            },
        ],
    },
    {
        "id": "risk",
        "level": "intermediate",
        "minutes": 4,
        "tags": ["risk", "sizing", "stoploss"],
        "title": {
            "hinglish": "Risk management: sabse pehle",
            "hindi": "रिस्क मैनेजमेंट: सबसे पहले",
            "en": "Risk management first",
        },
        "sections": [
            {
                "title": {
                    "hinglish": "1% rule",
                    "hindi": "1% नियम",
                    "en": "The 1% rule",
                },
                "body": {
                    "hinglish": "Ek trade mein apne capital ka max 1% risk karo. Matlab 1 lakh capital = 1000 rupees max loss per trade. Ye rules tumhe 20 consecutive losses mein bhi zinda rakhega.",
                    "hindi": "एक ट्रेड में अपने कैपिटल का अधिकतम 1% रिस्क करो। मतलब 1 लाख कैपिटल = प्रति ट्रेड अधिकतम 1000 रुपये नुकसान। यह नियम लगातार 20 नुकसान में भी ज़िंदा रखेगा।",
                    "en": "Risk max 1% of capital per trade. 1 lakh capital = max ₹1000 loss per trade. This rule keeps you alive through 20 consecutive losses.",
                },
            },
            {
                "title": {
                    "hinglish": "Stop loss ko entry ke pehle socho",
                    "hindi": "स्टॉप लॉस को एंट्री से पहले सोचो",
                    "en": "Plan the stop before entry",
                },
                "body": {
                    "hinglish": "Entry se pehle decide karo: 'agar price itna neeche gaya to main exit karunga'. Stop loss ke bina ek hi trade saal ka profit kha sakta hai.",
                    "hindi": "एंट्री से पहले तय करो: 'अगर प्राइस इतना नीचे गया तो मैं बाहर निकलूंगा'। स्टॉप लॉस के बिना एक ही ट्रेड साल का प्रॉफिट खा सकता है।",
                    "en": "Decide before entry: 'if price falls to X I exit'. Without a stop loss, one trade can eat a year of profit.",
                },
            },
            {
                "title": {
                    "hinglish": "Sizing backtest settings mein",
                    "hindi": "साइज़िंग बैकटेस्ट सेटिंग्स में",
                    "en": "Sizing in backtest settings",
                },
                "body": {
                    "hinglish": "Paper trading mein 'pct' sizing capital ka fixed % lagata hai. Risk management wahi practice karo jo aaj kal real market mein karni hai.",
                    "hindi": "पेपर ट्रेडिंग में 'pct' साइज़िंग कैपिटल का फिक्स % लगाता है। रिस्क मैनेजमेंट वही प्रैक्टिस करो जो कल रियल मार्केट में करनी है।",
                    "en": "Paper trading 'pct' sizing puts a fixed % of capital per trade. Practice the same risk management you'll use in real markets.",
                },
            },
        ],
    },
    {
        "id": "journaling",
        "level": "intermediate",
        "minutes": 3,
        "tags": ["journal", "discipline"],
        "title": {
            "hinglish": "Trading journal kyu rakhe",
            "hindi": "ट्रेडिंग जर्नल क्यों रखे",
            "en": "Why keep a trading journal",
        },
        "sections": [
            {
                "title": {
                    "hinglish": "Records = patterns",
                    "hindi": "रिकॉर्ड = पैटर्न",
                    "en": "Records reveal patterns",
                },
                "body": {
                    "hinglish": "Har trade ka note, pnl, rating, lesson likho. 20 trades baad pattern dikhne lagega: 'main loss ke baad jaldi entry kar leta hoon' jaisi galti.",
                    "hindi": "हर ट्रेड का नोट, PnL, रेटिंग, लेसन लिखो। 20 ट्रेड के बाद पैटर्न दिखने लगेगा: 'मैं लॉस के बाद जल्दी एंट्री कर लेता हूँ' जैसी गलती।",
                    "en": "Write a note, pnl, rating, lesson for every trade. After 20 trades a pattern emerges: a mistake like 'I enter too fast after a loss'.",
                },
            },
            {
                "title": {
                    "hinglish": "AI review ka use karo",
                    "hindi": "AI रिव्यू का उपयोग करो",
                    "en": "Use the AI review",
                },
                "body": {
                    "hinglish": "Journal tab ka 'AI Review my Journal' button aapke entries ko padh kar patterns, strengths aur risks batata hai. Ye sirf padhaya hai, koi buy/sell advice nahi.",
                    "hindi": "जर्नल टैब का 'AI रिव्यू माय जर्नल' बटन आपकी एंट्रीज़ पढ़कर पैटर्न, स्ट्रेंथ और रिस्क बताता है। यह सिर्फ़ पढ़ाता है, कोई बाय/सेल सलाह नहीं।",
                    "en": "The Journal tab's 'AI Review my Journal' button reads your entries and points out patterns, strengths and risks. It's educational only — no buy/sell advice.",
                },
            },
            {
                "title": {
                    "hinglish": "Emotional state likho",
                    "hindi": "इमोशनल स्टेट लिखो",
                    "en": "Record your emotional state",
                },
                "body": {
                    "hinglish": "Note mein bas technical details mat likho — mood bhi likho. Gussa ya revenge bhaav mein li gayi trades hi sabse zyada loss karwati hain.",
                    "hindi": "नोट में सिर्फ़ तकनीकी विवरण मत लिखो — मूड भी लिखो। गुस्सा या रिवेंज भाव में ली गई ट्रेड ही सबसे ज़्यादा नुकसान करवाती हैं।",
                    "en": "Don't just record technical details — note your mood too. The trades taken in anger or revenge are the ones that lose the most.",
                },
            },
        ],
    },
    {
        "id": "screener",
        "level": "beginner",
        "minutes": 3,
        "tags": ["screener", "filters"],
        "title": {
            "hinglish": "Screener kaise use kare",
            "hindi": "स्क्रीनर का उपयोग कैसे करें",
            "en": "How to use the screener",
        },
        "sections": [
            {
                "title": {
                    "hinglish": "Filter = market se chhanai",
                    "hindi": "फ़िल्टर = बाज़ार से छानना",
                    "en": "Filters sieve the market",
                },
                "body": {
                    "hinglish": "Hazaar symbols mein se wahi chuno jo tumhari condition match kare. Example: RSI > 60 = momentum stock. Pehle filter, phir chart par confirm, phir backtest.",
                    "hindi": "हज़ारों सिंबल में से वही चुनो जो तुम्हारी शर्त मिले। उदाहरण: RSI > 60 = मोमेंटम स्टॉक। पहले फ़िल्टर, फिर चार्ट पर कन्फर्म, फिर बैकटेस्ट।",
                    "en": "From thousands of symbols pick only those matching your condition. Example: RSI > 60 = momentum stocks. Filter first, confirm on the chart, then backtest.",
                },
            },
            {
                "title": {
                    "hinglish": "Saved scans",
                    "hindi": "सेव्ड स्कैन्स",
                    "en": "Saved scans",
                },
                "body": {
                    "hinglish": "Achha filter bana to 'Save scan' dabao — agli baar ek click mein chala sakte ho. Apni watchlist ki tarah, par criteria-based.",
                    "hindi": "अच्छा फ़िल्टर बना तो 'सेव स्कैन' दबाओ — अगली बार एक क्लिक में चला सकते हो। अपनी वॉचलिस्ट की तरह, पर मानदंड-आधारित।",
                    "en": "Built a good filter? Hit 'Save scan' and run it anytime with one click — like a watchlist, but criteria-based.",
                },
            },
            {
                "title": {
                    "hinglish": "Ek signal hi kafi nahi",
                    "hindi": "एक सिग्नल ही काफ़ी नहीं",
                    "en": "One signal is never enough",
                },
                "body": {
                    "hinglish": "Screener sirf idea deta hai. Trade tab se us symbol ka backtest chalao aur paper trade karke dekho isse pehle real paisa lagao.",
                    "hindi": "स्क्रीनर सिर्फ़ आइडिया देता है। ट्रेड टैब से उस सिंबल का बैकटेस्ट चलाओ और पेपर ट्रेड करके देखो इससे पहले असली पैसा लगाओ।",
                    "en": "The screener only gives ideas. Backtest the symbol in the trading tab and paper trade it before risking real money.",
                },
            },
        ],
    },
]


def lessons_by_id() -> dict[str, dict]:
    return {lesson["id"]: lesson for lesson in LESSONS}
