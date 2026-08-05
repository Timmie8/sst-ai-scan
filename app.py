import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go


st.set_page_config(
    page_title="SST AI Finnhub Scanner",
    page_icon="🚀",
    layout="wide"
)


st.title("🚀 SST AI Trading Scanner - Finnhub")


# =========================
# API KEY
# =========================

api_key = st.sidebar.text_input(
    "Finnhub API Key",
    type="password"
)


# =========================
# WATCHLIST
# =========================

if "tickers" not in st.session_state:
    st.session_state.tickers=[
        "NVDA",
        "TSLA",
        "AAPL"
    ]


st.sidebar.header("Watchlist")


new = st.sidebar.text_input(
    "Add ticker"
)


if st.sidebar.button("Add"):

    if new:

        t=new.upper()

        if t not in st.session_state.tickers:
            st.session_state.tickers.append(t)



remove = st.sidebar.selectbox(
    "Remove",
    [""]+st.session_state.tickers
)


if st.sidebar.button("Delete"):

    if remove:
        st.session_state.tickers.remove(remove)



interval = st.sidebar.selectbox(
    "Interval",
    [
        "1",
        "5",
        "15",
        "60"
    ],
    index=1
)



# =========================
# INDICATORS
# =========================


def EMA(data,period=20):

    return (
        data
        .ewm(span=period)
        .mean()
        .iloc[-1]
    )


def RSI(data,period=14):

    delta=data.diff()

    gain=delta.clip(lower=0)

    loss=-delta.clip(upper=0)


    avg_gain=gain.rolling(period).mean()

    avg_loss=loss.rolling(period).mean()


    rs=avg_gain/avg_loss


    rsi=100-(100/(1+rs))

    return rsi.iloc[-1]



def VWAP(df):

    price=(
        df.high+
        df.low+
        df.close
    )/3


    return (
        price*df.volume
    ).sum()/df.volume.sum()



# =========================
# FINNHUB DATA
# =========================


def get_candles(symbol):


    end=int(time.time())

    start=end-86400


    url="https://finnhub.io/api/v1/stock/candle"


    params={

        "symbol":symbol,

        "resolution":interval,

        "from":start,

        "to":end,

        "token":api_key
    }


    r=requests.get(
        url,
        params=params
    )


    data=r.json()


    if data.get("s")!="ok":

        return None



    df=pd.DataFrame({

        "time":data["t"],

        "open":data["o"],

        "high":data["h"],

        "low":data["l"],

        "close":data["c"],

        "volume":data["v"]

    })


    return df



# =========================
# SCORE
# =========================


def calculate_score(df):


    price=df.close.iloc[-1]

    score=0


    ema=EMA(df.close)

    rsi=RSI(df.close)

    vwap=VWAP(df)


    avg_vol=df.volume.tail(20).mean()

    spike=df.volume.iloc[-1] > avg_vol*2


    breakout=price >= df.high.tail(20).max()*0.99



    if price>ema:
        score+=25


    if price>vwap:
        score+=25


    if rsi>55:
        score+=25


    if spike:
        score+=25



    return score,rsi,ema,vwap,spike,breakout



# =========================
# SCANNER
# =========================


results=[]


if api_key:


    for ticker in st.session_state.tickers:


        df=get_candles(ticker)


        if df is None:

            continue



        score,rsi,ema,vwap,spike,breakout=calculate_score(df)


        results.append({

            "Ticker":ticker,

            "Price":round(df.close.iloc[-1],2),

            "RSI":round(rsi,1),

            "EMA20":round(ema,2),

            "VWAP":round(vwap,2),

            "Volume Spike":"🔥" if spike else "",

            "Breakout":"🚀" if breakout else "",

            "AI Score":score

        })



if results:


    table=pd.DataFrame(results)


    table=table.sort_values(
        "AI Score",
        ascending=False
    )


    st.subheader("🔥 SST Top Setups")


    st.dataframe(
        table,
        use_container_width=True
    )


    st.subheader("🏆 Top 3")


    for _,row in table.head(3).iterrows():

        st.success(
            f"{row.Ticker}  →  {row['AI Score']}%"
        )


else:

    st.info(
        "Enter Finnhub API key"
    )
