
import os
import time
import pandas as pd
import numpy as np
import streamlit as st

# Optional: live data via ccxt if installed and API available
try:
    import ccxt  # noqa: F401
    CCXT_AVAILABLE = True
except Exception:
    CCXT_AVAILABLE = False

st.set_page_config(page_title="Crypto Bot Demo", layout="wide")

st.title("Crypto Bot Demo — SMA Crossover (Paper)")
st.write("Questa è un'app DEMO: backtest su dati storici o paper trading simulato. Nessun ordine reale viene inviato.")

# --- Data handling ---
@st.cache_data
def load_sample_data():
    # Load sample OHLCV from packaged CSV
    csv_path = "data/sample_BTCUSDT_1h.csv"
    df = pd.read_csv(csv_path, parse_dates=["ts"])
    df = df.sort_values("ts").reset_index(drop=True)
    return df

def fetch_ccxt_ohlcv(symbol="BTC/USDT", timeframe="1h", limit=1000):
    if not CCXT_AVAILABLE:
        st.warning("ccxt non installato/attivo; uso dati di esempio.")
        return load_sample_data()
    try:
        ex = ccxt.binance()
        data = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(data, columns=["ts","o","h","l","c","v"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        return df
    except Exception as e:
        st.warning(f"Errore fetch dati live ({e}); uso dati di esempio.")
        return load_sample_data()

# --- Strategy ---
def sma_crossover(df, fast=20, slow=50):
    df = df.copy()
    df["ma_f"] = df["c"].rolling(fast).mean()
    df["ma_s"] = df["c"].rolling(slow).mean()
    df["signal"] = 0
    # 1 = buy, -1 = sell
    cross_up = (df["ma_f"].shift(1) <= df["ma_s"].shift(1)) & (df["ma_f"] > df["ma_s"])
    cross_dn = (df["ma_f"].shift(1) >= df["ma_s"].shift(1)) & (df["ma_f"] < df["ma_s"])
    df.loc[cross_up, "signal"] = 1
    df.loc[cross_dn, "signal"] = -1
    return df.dropna()

def backtest(df, fee=0.0004, slippage=0.0003):
    df = df.copy()
    position = 0  # 0 flat, 1 long
    entry_price = 0.0
    equity = 1.0  # equity normalizzata
    eq_curve = []
    trades = []

    for i, row in df.iterrows():
        price = row["c"]
        sig = row["signal"]
        if position == 0 and sig == 1:
            # enter long
            entry_price = price * (1 + slippage)
            equity *= (1 - fee)  # fee buy
            position = 1
            trades.append({"ts": row["ts"], "side": "BUY", "price": entry_price})
        elif position == 1 and sig == -1:
            # exit long
            exit_price = price * (1 - slippage)
            equity *= (exit_price / entry_price) * (1 - fee)  # fee sell
            position = 0
            trades.append({"ts": row["ts"], "side": "SELL", "price": exit_price})

        # Mark-to-market
        if position == 1:
            eq = equity * (price / entry_price)
        else:
            eq = equity
        eq_curve.append({"ts": row["ts"], "equity": eq})

    eq_df = pd.DataFrame(eq_curve)
    trade_df = pd.DataFrame(trades)
    return eq_df, trade_df

# --- Sidebar controls ---
with st.sidebar:
    st.header("Parametri")
    data_source = st.selectbox("Dati", ["Esempio (offline)", "Live (ccxt/Binance)"])
    fast = st.slider("SMA veloce", 5, 100, 20, 1)
    slow = st.slider("SMA lenta", 10, 300, 50, 1)
    if slow <= fast:
        st.error("La SMA lenta deve essere > SMA veloce.")
    fees = st.number_input("Fee (per trade)", value=0.0004, step=0.0001, format="%.4f")
    slippage = st.number_input("Slippage (simulato)", value=0.0003, step=0.0001, format="%.4f")
    run_mode = st.selectbox("Modalità", ["Backtest storico", "Paper trading live (simulato)"])
    refresh_sec = st.number_input("Refresh (sec) in paper live", min_value=5, value=20, step=5)

# --- Load data ---
if data_source.startswith("Live"):
    df = fetch_ccxt_ohlcv()
else:
    df = load_sample_data()

if slow <= fast:
    st.stop()

df = df.sort_values("ts").reset_index(drop=True)
df = sma_crossover(df, fast=fast, slow=slow)

# --- Main view ---
tab1, tab2, tab3 = st.tabs(["Grafico", "Backtest", "Log Trades"])

with tab1:
    st.subheader("Prezzo & Medie Mobili")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot(df["ts"], df["c"], label="Close")
    ax.plot(df["ts"], df["ma_f"], label=f"SMA {fast}")
    ax.plot(df["ts"], df["ma_s"], label=f"SMA {slow}")
    # segnali
    buys = df[df["signal"] == 1]
    sells = df[df["signal"] == -1]
    ax.scatter(buys["ts"], buys["c"], marker="^", s=40, label="BUY")
    ax.scatter(sells["ts"], sells["c"], marker="v", s=40, label="SELL")
    ax.legend()
    st.pyplot(fig, clear_figure=True)

with tab2:
    st.subheader("Risultati Backtest")
    eq_df, trade_df = backtest(df, fee=fees, slippage=slippage)
    st.line_chart(eq_df.set_index("ts"))
    ret = eq_df["equity"].iloc[-1] - 1.0
    dd = (eq_df["equity"].cummax() - eq_df["equity"]).max()
    col1, col2 = st.columns(2)
    col1.metric("Rendimento totale", f"{ret*100:.2f}%")
    col2.metric("Max Drawdown", f"{dd*100:.2f}%")
    st.dataframe(eq_df.tail(10))

with tab3:
    st.subheader("Trades (incroci)")
    st.dataframe(df[df["signal"].abs() == 1][["ts","c","signal"]].rename(columns={"c":"price","signal":"sig"}).tail(50))

# --- Paper trading (very simple loop) ---
if run_mode.startswith("Paper"):
    ph = st.empty()
    st.info("Paper trading simulato: calcola segnali sull'ultimo valore e aggiorna.")
    last_sig = None
    for _ in range(3):  # loop limitato per la demo
        live_df = df.copy()
        sig = int(live_df.iloc[-1]["signal"])
        msg = "HOLD"
        if sig == 1 and last_sig != 1:
            msg = "BUY signal"
        elif sig == -1 and last_sig != -1:
            msg = "SELL signal"
        last_sig = sig
        ph.write(f"Ultimo segnale: **{msg}** alle {pd.to_datetime(live_df.iloc[-1]['ts'])}")
        time.sleep(int(refresh_sec))
    st.success("Demo loop concluso. Per un loop continuo, esegui l'app in locale.")
