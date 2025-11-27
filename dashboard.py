import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# >>> KONFIGURACJA <<<
# Wklej klucz tu, albo zostaw puste jeśli masz go w zmiennych środowiskowych
# Sprawdzamy, czy jesteśmy w chmurze (Streamlit Secrets)
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
else:
    # Fallback dla lokalnego uruchomienia (opcjonalne, ale ryzykowne przy uploadzie)
    # Lepiej zostawić to puste przed wrzuceniem na GitHuba!
    pass

# Konfiguracja strony
st.set_page_config(page_title="AI Inwestor", layout="wide")
st.title("📈 AI Investment Analyzer")

# 1. PANEL BOCZNY (Input)
with st.sidebar:
    st.header("Konfiguracja")
    ticker = st.text_input("Symbol spółki (np. AAPL, BTC-USD):", value="BTC-USD")
    period = st.selectbox("Okres czasu:", ["1mo", "3mo", "6mo", "1y", "5y"], index=2)
    st.info("Wpisz symbol i naciśnij Enter.")


# 2. POBIERANIE DANYCH
def get_data(symbol, okres):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=okres)
        return df, stock.info
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return None, None


df, info = get_data(ticker, period)

if df is not None and not df.empty:
    # 3. WYŚWIETLANIE DANYCH (Wykresy)
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    delta = current_price - prev_price

    col1, col2, col3 = st.columns(3)
    col1.metric("Aktualna Cena", f"{current_price:.2f}", f"{delta:.2f}")
    col2.metric("Najwyższa (High)", f"{df['High'].max():.2f}")
    col3.metric("Najniższa (Low)", f"{df['Low'].min():.2f}")

    # Wykres świecowy (Interaktywny Plotly)
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['Open'], high=df['High'],
                                         low=df['Low'], close=df['Close'])])
    fig.update_layout(title=f"Wykres {ticker}", xaxis_title="Data", yaxis_title="Cena")
    st.plotly_chart(fig, use_container_width=True)

    # 4. MÓZG AI (Analiza)
    st.subheader("🧠 Analiza AI")

    if st.button("Poproś AI o analizę"):
        with st.spinner("AI analizuje dane rynkowe..."):
            try:
                # Przygotowanie danych dla modelu (ostatnie 5 dni)
                ostatnie_dni = df.tail(5).to_string()

                model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

                prompt = f"""
                Jesteś profesjonalnym doradcą inwestycyjnym. Przeanalizuj te dane giełdowe dla {ticker}.

                OSTATNIE DANE:
                {ostatnie_dni}

                Twoje zadanie:
                1. Opisz krótko trend (wzrostowy/spadkowy/boczny).
                2. Wymień kluczowe poziomy wsparcia/oporu na podstawie liczb.
                3. Wydaj werdykt: czy widać sygnały do kupna czy sprzedaży? (Zastrzeż, że to nie porada finansowa).
                4. Używaj języka finansowego, bądź konkretny.
                """

                response = model.invoke(prompt)
                st.write(response.content)

            except Exception as e:
                st.error(f"Błąd AI: {e}")

else:
    st.warning("Brak danych. Sprawdź symbol spółki.")