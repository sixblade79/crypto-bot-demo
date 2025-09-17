# Crypto Bot Demo (Streamlit)

Demo educativa per esplorare una strategia **SMA crossover** su dati cripto.
- Backtest su dati di esempio inclusi (offline).
- Opzione di dati live via `ccxt` (Binance) se desiderato.
- **Nessun ordine reale**: è solo una demo.

## Avvio rapido
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
streamlit run app.py
```

## Note
- I dati di esempio si trovano in `data/sample_BTCUSDT_1h.csv`.
- Per usare dati live, assicurati che la tua rete consenta connessioni e che `ccxt` sia installato.
- Questa app è per scopi educativi, non è un consiglio finanziario.