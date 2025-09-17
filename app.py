
import pandas as pd
import numpy as np
import streamlit as st
import time

try:
    import ccxt
    CCXT_AVAILABLE = True
except Exception:
    CCXT_AVAILABLE = False

from strategies import sma_crossover, rsi_strategy, bollinger_strategy

st.set_page_config(page_title="Crypto Bot Demo Multi-Strategia", layout="wide")
st.title("Crypto Bot Demo — Multi-Strategia (Paper Trading)")

@st.cache_data
def load_sample_data():
    df = pd.read_csv("data/sample_BTCUSDT_1h.csv", parse_dates=["ts"])
    return df.sort_values("ts").reset_index(drop=True)

def fetch_ccxt(symbol="BTC/USDT", timeframe="1h", limit=500):
    if not CCXT_AVAILABLE:
        st.warning("ccxt non disponibile, uso dati di esempio.")
        return load_sample_data()
    try:
        ex = ccxt.binance()
        data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=["ts","o","h","l","c","v"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        return df
    except Exception as e:
        st.warning(f"Errore fetch dati: {e}")
        return load_sample_data()

# Sidebar
with st.sidebar:
    st.header("Parametri")
    source = st.selectbox("Dati", ["Esempio", "Live (Binance)"])
    strat_name = st.selectbox("Strategia", ["SMA Crossover", "RSI", "Bollinger"])
    run_mode = st.selectbox("Modalità", ["Backtest", "Paper live (simulato)"])
    refresh = st.number_input("Refresh (sec) in live", 5, 60, 20)

# Load data
df = load_sample_data() if source=="Esempio" else fetch_ccxt()

# Strategy
if strat_name == "SMA Crossover":
    df = sma_crossover(df, fast=20, slow=50)
elif strat_name == "RSI":
    df = rsi_strategy(df, period=14, low=30, high=70)
elif strat_name == "Bollinger":
    df = bollinger_strategy(df, period=20, stds=2)

# Grafico
st.subheader("Grafico con segnali")
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(df["ts"], df["c"], label="Close")
if "ma_f" in df: ax.plot(df["ts"], df["ma_f"], label="MA veloce")
if "ma_s" in df: ax.plot(df["ts"], df["ma_s"], label="MA lenta")
if "upper" in df: ax.plot(df["ts"], df["upper"], "--", label="Boll upper")
if "lower" in df: ax.plot(df["ts"], df["lower"], "--", label="Boll lower")
buys = df[df["signal"]==1]
sells = df[df["signal"]==-1]
ax.scatter(buys["ts"], buys["c"], marker="^", color="g", label="BUY")
ax.scatter(sells["ts"], sells["c"], marker="v", color="r", label="SELL")
ax.legend()
st.pyplot(fig, clear_figure=True)

# Log segnali recenti
st.subheader("Segnali recenti")
st.dataframe(df[["ts","c","signal"]].tail(20))

if run_mode.startswith("Paper"):
    st.info("Paper trading simulato in corso (demo).")
    ph = st.empty()
    last_sig = None
    for i in range(3):
        sig = int(df.iloc[-1]["signal"])
        msg = "HOLD"
        if sig == 1 and last_sig != 1:
            msg = "BUY"
        elif sig == -1 and last_sig != -1:
            msg = "SELL"
        last_sig = sig
        ph.write(f"Ultimo segnale: **{msg}** @ {df.iloc[-1]['c']}")
        time.sleep(int(refresh))
    st.success("Demo loop concluso. Riavvia per ripetere.")
