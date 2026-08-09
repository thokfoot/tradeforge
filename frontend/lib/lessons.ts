export interface Lesson {
  id: string;
  section: string;
  title: { en: string; hi: string };
  body: { en: string; hi: string };
}

export interface Section {
  id: string;
  title: { en: string; hi: string };
}

export const SECTIONS: Section[] = [
  { id: "start", title: { en: "Getting Started", hi: "Shuruwaat" } },
  { id: "backtest", title: { en: "Backtesting", hi: "Backtesting" } },
  { id: "indicators", title: { en: "Technical Indicators", hi: "Technical Indicators" } },
  { id: "paper", title: { en: "Paper Trading", hi: "Paper Trading" } },
  { id: "builder", title: { en: "Strategy Builder", hi: "Strategy Builder" } },
  { id: "risk", title: { en: "Risk Management", hi: "Risk Management" } },
];

export const LESSONS: Lesson[] = [
  {
    id: "what-is-trading",
    section: "start",
    title: { en: "What is trading?", hi: "Trading kya hota hai?" },
    body: {
      en: `Trading means buying and selling stocks, cryptocurrencies, or other assets to make a profit.

When you buy a stock at ₹100 and sell it at ₹120, you make ₹20 profit. But if the price drops to ₹80 and you sell, you lose ₹20.

The goal is to buy low and sell high — but nobody knows the future. That's why we test strategies first.

Trade Forge lets you test your ideas on historical data BEFORE risking real money.`,
      hi: `Trading ka matlab hai stocks, crypto, ya doosre assets ko buy karke sell karna profit banane ke liye.

Jab aap ₹100 ka stock khareedte ho aur ₹120 pe bechte ho, aapne ₹20 profit banaya. Lekin agar price ₹80 ho jaaye aur aap sell karo, toh ₹20 ka loss hoga.

Goal hota hai low pe buy karna aur high pe sell — lekin future kisi ko nahi pata. Isliye hum strategies ko pehle test karte hain.

Trade Forge aapko real data pe apne ideas test karne deta hai BINA real paise lagaye.`,
    },
  },
  {
    id: "why-backtest",
    section: "backtest",
    title: { en: "Why backtest?", hi: "Backtest kyun karein?" },
    body: {
      en: `Backtesting means running your trading strategy on historical data to see how it would have performed.

Without backtesting, you are guessing. With backtesting, you have actual numbers:
- How many trades won vs lost? (win rate)
- What was the total return?
- What was the max loss at any point? (drawdown)
- Is the profit worth the risk? (Sharpe ratio)

A strategy that looks good on paper might lose money. Only numbers tell the real story.`,
      hi: `Backtesting ka matlab hai apni trading strategy ko purane data pe test karna, ye dekhne ke liye ki wo pehle kaise perform karti.

Bina backtest ke aap guess kar rahe ho. Backtest ke saath aapke paas real numbers hain:
- Kitne trades jeete vs haare? (win rate)
- Total return kitna tha?
- Sabse bada loss ek time pe kitna tha? (drawdown)
- Kya profit risk ke layak hai? (Sharpe ratio)

Ek strategy jo dekhne mein acchi lagti hai, wo actually loss kar sakti hai. Sirf numbers sach batate hain.`,
    },
  },
  {
    id: "reading-results",
    section: "backtest",
    title: { en: "Reading your backtest results", hi: "Backtest results kaise padhein?" },
    body: {
      en: `When you run a backtest, you get these key numbers:

- **Total Return %**: How much profit/loss overall.
- **Win Rate %**: Percentage of winning trades. Above 40% is decent.
- **Sharpe Ratio**: Measures return vs risk. Above 1 is good, above 2 is excellent.
- **Max Drawdown %**: Worst peak-to-trough drop. Keep this under 20% ideally.
- **Profit Factor**: Gross profit / gross loss. Above 1.5 is good.
- **Total Trades**: More trades = more reliable the test.

If your strategy has 60% win rate but loses money, check: are losses bigger than wins? That's a common trap.`,
      hi: `Backtest run karne ke baad, aapko ye key numbers milte hain:

- **Total Return %**: Overall profit ya loss kitna hua.
- **Win Rate %**: Jeetne wali trades ka %. 40% se upar achha hai.
- **Sharpe Ratio**: Return vs risk ka ratio. 1 se upar achha, 2 se upar excellent.
- **Max Drawdown %**: Worst peak-to-trough drop. Ideally 20% se kam rakho.
- **Profit Factor**: Total profit ÷ total loss. 1.5 se upar achha.
- **Total Trades**: Jitne zyada trades, utna reliable test.

Agar 60% win rate hai lekin loss ho raha hai: check karo ki losses wins se bade toh nahi? Ye common trap hai.`,
    },
  },
  {
    id: "what-is-rsi",
    section: "indicators",
    title: { en: "RSI — Relative Strength Index", hi: "RSI kya hai?" },
    body: {
      en: `RSI measures how fast and how much a price is moving. It ranges from 0 to 100.

- **RSI above 70** = overbought (maybe too expensive, price may drop)
- **RSI below 30** = oversold (maybe too cheap, price may bounce)

Common use: Buy when RSI crosses above 30 (oversold bounce), sell when RSI crosses below 70 (overbought pullback).

But be careful! In a strong trend, RSI can stay overbought for a long time. Always combine with other checks.

The Screener tab can filter stocks by RSI. The Strategy Builder can use RSI in entry/exit rules.`,
      hi: `RSI measure karta hai ki price kitni fast aur kitni door move kar raha hai. 0 se 100 ke beech.

- **RSI 70 ke upar** = overbought (shayad zyada mehnga, price gir sakta hai)
- **RSI 30 ke neeche** = oversold (shayad zyada sasta, price upar aa sakta hai)

Common use: Buy karo jab RSI 30 ke upar cross kare (oversold bounce), sell karo jab RSI 70 ke neeche cross kare (overbought pullback).

Lekin savdhan! Strong trend mein RSI der tak overbought reh sakta hai. Hamesha doosre checks ke saath combine karo.

Screener tab mein RSI se stocks filter kar sakte ho. Strategy Builder mein RSI ko entry/exit rules mein use kar sakte ho.`,
    },
  },
  {
    id: "what-is-sma",
    section: "indicators",
    title: { en: "SMA — Simple Moving Average", hi: "SMA (Moving Average) kya hai?" },
    body: {
      en: `SMA is the average price over the last N days. It smooths out noise and shows the trend.

- **SMA 20** = 1 month average (short-term trend)
- **SMA 50** = ~2.5 months (medium-term trend)
- **SMA 200** = ~10 months (long-term trend)

When price is above SMA, the trend is UP. When below, the trend is DOWN.

Golden Cross: SMA 50 crosses above SMA 200 → bullish signal.
Death Cross: SMA 50 crosses below SMA 200 → bearish signal.

Moving averages lag — they react to past data, not future. Use them with other indicators.`,
      hi: `SMA pichle N dinon ka average price hai. Ye noise ko smooth karta hai aur trend dikhata hai.

- **SMA 20** = 1 mahine ka average (short-term trend)
- **SMA 50** = ~2.5 mahine (medium-term trend)
- **SMA 200** = ~10 mahine (long-term trend)

Jab price SMA ke upar ho, trend UP hai. Jab neeche ho, trend DOWN hai.

Golden Cross: SMA 50 jab SMA 200 ke upar cross kare → bullish signal.
Death Cross: SMA 50 jab SMA 200 ke neeche cross kare → bearish signal.

Moving averages piche reh jaate hain — past data pe react karte hain, future pe nahi. Doosre indicators ke saath use karo.`,
    },
  },
  {
    id: "what-is-macd",
    section: "indicators",
    title: { en: "MACD — Moving Average Convergence Divergence", hi: "MACD kya hai?" },
    body: {
      en: `MACD shows the relationship between two moving averages (12-day and 26-day).

It has 3 parts:
- **MACD Line**: Fast EMA minus slow EMA
- **Signal Line**: 9-day EMA of the MACD line
- **Histogram**: MACD line minus signal line (shows momentum)

When MACD crosses above Signal → bullish (buy signal).
When MACD crosses below Signal → bearish (sell signal).

The Screener tab has a MACD filter. Use it to find stocks where MACD is above or below its signal line.`,
      hi: `MACD do moving averages (12-din aur 26-din) ke relationship ko dikhata hai.

Iske 3 parts hain:
- **MACD Line**: Fast EMA minus slow EMA
- **Signal Line**: MACD line ka 9-day EMA
- **Histogram**: MACD line minus signal line (momentum dikhata hai)

Jab MACD Signal ke upar cross kare → bullish (buy signal).
Jab MACD Signal ke neeche cross kare → bearish (sell signal).

Screener tab mein MACD filter hai. Stocks dhundne ke liye jahan MACD signal ke upar ya neeche ho.`,
    },
  },
  {
    id: "bollinger-bands",
    section: "indicators",
    title: { en: "Bollinger Bands — %B", hi: "Bollinger Bands aur %B kya hai?" },
    body: {
      en: `Bollinger Bands are 3 lines around the price:
- Middle: SMA 20
- Upper: SMA 20 + 2 standard deviations
- Lower: SMA 20 - 2 standard deviations

**%B** tells you where the price sits between the bands:
- %B = 0 → price at lower band (oversold)
- %B = 1 → price at upper band (overbought)
- %B above 1 or below 0 → price is outside the bands (extreme)

When price touches the lower band, it may bounce up. When it touches the upper band, it may pull back.

Use the Screener's Bollinger %B filter to find stocks near the edges.`,
      hi: `Bollinger Bands price ke aas-paas 3 lines hain:
- Middle: SMA 20
- Upper: SMA 20 + 2 standard deviations
- Lower: SMA 20 - 2 standard deviations

**%B** batata hai ki price bands ke beech mein kahan hai:
- %B = 0 → price lower band pe (oversold)
- %B = 1 → price upper band pe (overbought)
- %B 1 se upar ya 0 se neeche → price bands ke bahar (extreme)

Jab price lower band ko touch kare, upar bounce kar sakta hai. Jab upper band touch kare, neeche pullback kar sakta hai.

Screener ka Bollinger %B filter use karo extreme stocks dhundne ke liye.`,
    },
  },
  {
    id: "paper-trading-how",
    section: "paper",
    title: { en: "How paper trading works", hi: "Paper trading kaise kaam karta hai?" },
    body: {
      en: `Paper trading is simulated trading with virtual money. You start with ₹1,00,000 or any amount you choose.

You can:
- Place BUY and SELL orders at current market prices
- Track your positions and profit/loss in real time
- Reset your account anytime to start fresh

The fills use real price data (there's a small delay for free data). This gives you a realistic experience without any risk.

**How to use it:**
1. Go to the Paper Trading tab
2. Select a market and symbol
3. Enter quantity and click BUY/SELL
4. Watch your equity grow (or shrink!) in the positions table
5. Reset when you want to try a new approach`,
      hi: `Paper trading virtual paise ke saath simulated trading hai. Aap ₹1,00,000 ya koi bhi amount se start karte ho.

Aap kar sakte ho:
- Current market price pe BUY aur SELL orders
- Real-time mein apne positions aur profit/loss track karna
- Kabhi bhi account reset karke fresh start karna

Fills real price data use karte hain (free data mein thoda delay hota hai). Bina kisi risk ke realistic experience milta hai.

**Kaise use karein:**
1. Paper Trading tab pe jao
2. Market aur symbol select karo
3. Quantity enter karo aur BUY/SELL pe click karo
4. Positions table mein apna equity badhta (ya girta!) dekho
5. Nayi approach try karne ke liye reset karo`,
    },
  },
  {
    id: "replay-to-paper",
    section: "paper",
    title: { en: "Replay to Paper feature", hi: "Replay to Paper feature" },
    body: {
      en: `The Replay to Paper button lets you take a backtest result and replay every trade into your paper trading account.

This is powerful because:
- You see EXACTLY how each trade played out in the account
- All fills are reconstructed from the backtest — you can verify every entry and exit
- The final equity in your paper account will match the backtest return

To use it:
1. Run a backtest on the Dashboard
2. Make sure you're logged in
3. Click "Replay to Paper"
4. Your paper account is reset and all trades are replayed
5. Check the Paper Trading tab to see your positions and history`,
      hi: `Replay to Paper button aapko backtest result ke sabhi trades ko paper trading account mein replay karne deta hai.

Ye isliye powerful hai:
- EXACTLY dekh sakte ho ki har trade account mein kaise play out hua
- Sabhi fills backtest se reconstruct hote hain — har entry aur exit verify kar sakte ho
- Paper account ka final equity backtest return se match karega

Kaise use karein:
1. Dashboard pe backtest run karo
2. Ensure karo ki logged in ho
3. "Replay to Paper" pe click karo
4. Paper account reset hota hai aur sab trades replay hote hain
5. Paper Trading tab mein positions aur history check karo`,
    },
  },
  {
    id: "builder-blocks",
    section: "builder",
    title: { en: "Strategy Builder blocks", hi: "Strategy Builder blocks" },
    body: {
      en: `The Strategy Builder lets you create trading strategies visually — no coding needed.

Each strategy has Entry rules and Exit rules. Each rule has one or more conditions joined by AND or OR.

A **condition block** checks one thing:
- Indicator: close, open, high, low, volume, SMA, EMA, RSI
- Operator: above or below
- Target: a number (e.g. 30 for RSI) OR another indicator (e.g. SMA 20)

Example: "RSI above 70" → overbought signal.

**AND** means ALL conditions must be true. **OR** means ANY condition triggers.

When Entry is true, you BUY at the next bar's open. When Exit is true, you SELL.

After generating, you can test your strategy immediately with the inline backtest runner.`,
      hi: `Strategy Builder aapko visually trading strategies banane deta hai — coding ki zaroorat nahi.

Har strategy mein Entry rules aur Exit rules hote hain. Har rule mein ek ya zyada conditions AND ya OR se judi hui.

Ek **condition block** ek cheez check karta hai:
- Indicator: close, open, high, low, volume, SMA, EMA, RSI
- Operator: above (upar) ya below (neeche)
- Target: number (jaise RSI ke liye 30) YA doosra indicator (jaise SMA 20)

Example: "RSI above 70" → overbought signal.

**AND** matlab SAARI conditions true honi chahiye. **OR** matlab KOI BHI condition trigger ho sakti hai.

Jab Entry true ho, aap next bar ke open pe BUY karte ho. Jab Exit true ho, SELL.

Generate karne ke baad, turant inline backtest runner se strategy test kar sakte ho.`,
    },
  },
  {
    id: "position-sizing",
    section: "risk",
    title: { en: "Position sizing — don't bet everything", hi: "Position sizing — sab kuch mat lagao" },
    body: {
      en: `Position sizing decides how much of your capital you put in each trade.

**Fixed sizing**: Always buy N shares (e.g. 10 shares of RELIANCE). Simple but ignores account size.

**Percentage sizing**: Invest X% of your capital per trade (e.g. 10%). As your account grows/shrinks, position size adjusts automatically.

Rule of thumb: Never risk more than 1-2% of your account on a single trade. If your stop-loss is 5% away, your position size should be 20-40% of your account — not the whole thing.

Example: ₹1,00,000 account. 2% risk = ₹2,000. If stop-loss is 5%, max position = ₹2,000 ÷ 5% = ₹40,000. That's 40% of account — a good max for one position.`,
      hi: `Position sizing decide karta hai ki har trade mein apni capital ka kitna hissa lagana hai.

**Fixed sizing**: Hamesha N shares khareedo (jaise 10 RELIANCE shares). Simple lekin account size ignore karta hai.

**Percentage sizing**: Har trade mein X% capital lagao (jaise 10%). Account badhta/ghat-ta hai toh position size automatically adjust hota hai.

Rule of thumb: Kabhi bhi ek trade mein apne account ka 1-2% se zyada risk mat lo. Agar stop-loss 5% door hai, toh position size 20-40% hona chahiye — poori capital nahi.

Example: ₹1,00,000 account. 2% risk = ₹2,000. Agar stop-loss 5%, max position = ₹2,000 ÷ 5% = ₹40,000. Ye account ka 40% hai — ek position ke liye accha max.`,
    },
  },
  {
    id: "drawdown-real",
    section: "risk",
    title: { en: "Drawdown — the hidden killer", hi: "Drawdown — chhupa hua killer" },
    body: {
      en: `Max Drawdown is the biggest drop from a peak to the bottom before recovering. It shows how much pain you'd have to endure.

Example: Your ₹1,00,000 grows to ₹1,50,000, then drops to ₹1,20,000, then goes back up. Your drawdown is 20% (from 1.5L to 1.2L).

Why it matters:
- A 50% drawdown needs a 100% gain just to break even
- A 20% drawdown needs only a 25% gain to recover
- Many traders quit during drawdowns — that's when they crystalize losses

Watch the drawdown % on every backtest. If it's above 20-30%, the strategy might be too risky for real money.

Sharpe Ratio and Calmar Ratio help compare strategies: higher = smoother returns with less pain.`,
      hi: `Max Drawdown peak se bottom tak ka sabse bada drop hai recovery se pehle. Ye dikhata hai ki kitna dard sehna padega.

Example: Aapka ₹1,00,000 badhta hai ₹1,50,000 tak, phir girta hai ₹1,20,000 tak, phir upar jaata hai. Drawdown 20% hai (1.5L se 1.2L).

Kyun matter karta hai:
- 50% drawdown recover karne ke liye 100% gain chahiye
- 20% drawdown recover karne ke liye sirf 25% gain
- Bahut traders drawdown ke time quit kar dete hain — tabhi loss permanent ho jaata hai

Har backtest pe drawdown % dekho. Agar 20-30% se upar hai, strategy real money ke liye risky ho sakti hai.

Sharpe Ratio aur Calmar Ratio strategies compare karne mein help karte hain: higher = smoother returns with less pain.`,
    },
  },
  {
    id: "brokerage-costs",
    section: "risk",
    title: { en: "Indian brokerage costs", hi: "Indian brokerage charges" },
    body: {
      en: `Trading in India has real costs that eat into your profits. Trade Forge includes ALL of them in backtests:

- **Brokerage**: Usually ₹20 or 0.03% per trade (whichever is lower) — Zerodha-style
- **STT (Securities Transaction Tax)**: 0.1% on delivery buy+sell, 0.025% on intraday sell
- **Exchange transaction charges**: NSE ~0.00325%
- **GST**: 18% on brokerage + exchange charges
- **SEBI turnover fees**: ~0.0001%
- **Stamp duty**: Varies by state (~0.015% on delivery buy)

Total typical cost: ~0.1-0.15% per side for delivery. For a ₹10,000 trade, that's about ₹10-15 per side.

This is why frequent trading is expensive — costs add up quickly. A strategy that makes ₹5 per trade but costs ₹15 per trade is a losing strategy. Backtests show the REAL numbers including these charges.`,
      hi: `India mein trading ke real costs hain jo aapke profit ko khaate hain. Trade Forge backtests mein YE SAB include karta hai:

- **Brokerage**: Usually ₹20 ya 0.03% per trade (jo bhi kam ho) — Zerodha-style
- **STT**: Delivery buy+sell pe 0.1%, intraday sell pe 0.025%
- **Exchange transaction charges**: NSE ~0.00325%
- **GST**: Brokerage + exchange charges pe 18%
- **SEBI turnover fees**: ~0.0001%
- **Stamp duty**: State ke hisaab se (~0.015% delivery buy pe)

Total typical cost: ~0.1-0.15% per side for delivery. ₹10,000 trade ke liye ye ~₹10-15 per side.

Isliye frequent trading mehngi hai — costs jaldi add hote hain. Ek strategy jo ₹5 per trade profit karti hai lekin ₹15 ka cost hai, wo loss wali strategy hai. Backtests REAL numbers dikhate hain including these charges.`,
    },
  },
];
