import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go


# ==========================
# SST AI SCANNER
# ==========================

st.set_page_config(
    page_title="SST AI Scanner",
    page_icon="🚀",
    layout="wide"
)


st.title("🚀 SST AI Trading Scanner")
st.caption("Yahoo Finance • Intraday • AI Score")


# ==========================
# WATCHLIST
# ==========================

if "tickers" not in st.session_state:
    st.session_state.tickers = [
        "NVDA",
        "TSLA",
        "AAPL"
    ]


with st.sidebar:

    st.header("Watchlist")

    new_ticker = st.text_input(
        "Add ticker"
    )


    if st.button("Add"):

        if new_ticker:
            t = new_ticker.upper()

            if t not in st.session_state.tickers:
                st.session_state.tickers.append(t)


    remove = st.selectbox(
        "Remove ticker",
        [""] + st.session_state.tickers
    )


    if st.button("Delete"):

        if remove:
            st.session_state.tickers.remove(remove)



# ==========================
# INDICATORS
# ==========================


def ema(series, length=20):

    return (
        series
        .ewm(span=length)
        .mean()
        .iloc[-1]
    )



def rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)


    avg_gain = gain.rolling(period).mean()

    avg_loss = loss.rolling(period).mean()


    rs = avg_gain / avg_loss


    value = 100 - (100/(1+rs))


    return value.iloc[-1]



def vwap(df):

    price = (
        df.High +
        df.Low +
        df.Close
    ) / 3


    return (
        price * df.Volume
    ).sum() / df.Volume.sum()



def volume_spike(df):

    avg = (
        df.Volume
        .tail(20)
        .mean()
    )


    current = (
        df.Volume
        .iloc[-1]
    )


    return current > avg * 2



# ==========================
# SCORING
# ==========================


def ai_score(df):

    price = df.Close.iloc[-1]

    score = 0


    e = ema(df.Close)

    r = rsi(df.Close)

    v = vwap(df)



    if price > e:
        score += 25


    if price > v:
        score += 25


    if r > 55:
        score += 25


    if volume_spike(df):
        score += 25


    return score



# ==========================
# SCANNER
# ==========================


results=[]


for ticker in st.session_state.tickers:


    try:

        data = yf.download(
            ticker,
            period="5d",
            interval="5m",
            progress=False
        )


        if data.empty:

            continue



        # Multi timeframe
        score = ai_score(data)


        price = float(
            data.Close.iloc[-1]
        )


        r = float(
            rsi(data.Close)
        )


        e = float(
            ema(data.Close)
        )


        v = float(
            vwap(data)
        )


        spike = volume_spike(data)


        high = float(
            data.High.max()
        )


        low = float(
            data.Low.min()
        )


        if score >=75:
            signal="🔥 STRONG BUY"

        elif score >=50:
            signal="👀 WATCH"

        else:
            signal="⚠️ WEAK"



        results.append({

            "Ticker":ticker,
            "Price":round(price,2),
            "RSI":round(r,1),
            "EMA20":round(e,2),
            "VWAP":round(v,2),
            "Volume Spike":spike,
            "High":round(high,2),
            "Low":round(low,2),
            "AI Score":score,
            "Signal":signal

        })


    except Exception as ex:

        st.warning(
            f"{ticker}: {ex}"
        )



# ==========================
# DISPLAY
# ==========================


if results:


    df=pd.DataFrame(results)


    df=df.sort_values(
        "AI Score",
        ascending=False
    )


    st.subheader("🔥 Top SST Setups")


    st.dataframe(
        df,
        use_container_width=True
    )


    st.subheader("🏆 Top 3")


    for _,row in df.head(3).iterrows():

        st.success(
            f"{row.Ticker} → {row['AI Score']}%  {row.Signal}"
        )



    # Chart

    selected = st.selectbox(
        "Chart",
        st.session_state.tickers
    )


    chart = yf.download(
        selected,
        period="5d",
        interval="5m",
        progress=False
    )


    if not chart.empty:


        fig=go.Figure()


        fig.add_trace(
            go.Candlestick(
                x=chart.index,
                open=chart.Open,
                high=chart.High,
                low=chart.Low,
                close=chart.Close
            )
        )


        fig.update_layout(
            height=500,
            template="plotly_dark"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


else:

    st.info(
        "No data available"
    )
