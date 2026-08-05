from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)


def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100/(1+rs))

    return rsi.iloc[-1]


def calculate_vwap(df):

    price = (df.High + df.Low + df.Close)/3

    return (
        price * df.Volume
    ).sum() / df.Volume.sum()



@app.route("/scan")
def scan():

    ticker = request.args.get("ticker")

    if not ticker:
        return jsonify({"error":"No ticker"})


    try:

        stock = yf.Ticker(ticker)


        # 5 minute
        df5 = stock.history(
            interval="5m",
            period="1d"
        )


        # 1 hour
        df1h = stock.history(
            interval="60m",
            period="5d"
        )


        if df5.empty:
            return jsonify({
                "error":"No data"
            })


        close=df5.Close


        price=float(close.iloc[-1])


        ema=float(
            close.ewm(span=20).mean().iloc[-1]
        )


        rsi=float(
            calculate_rsi(close)
        )


        vwap=float(
            calculate_vwap(df5)
        )


        volume=df5.Volume.iloc[-1]


        avg_volume=df5.Volume.tail(20).mean()


        volume_spike = volume > avg_volume*2


        high=float(
            df5.High.tail(20).max()
        )


        low=float(
            df5.Low.tail(20).min()
        )


        breakout = price >= high*0.99



        score=0


        if price>ema:
            score+=20

        if price>vwap:
            score+=20

        if rsi>55:
            score+=20

        if volume_spike:
            score+=20

        if breakout:
            score+=20



        return jsonify({

            "ticker":ticker,

            "price":round(price,2),

            "rsi":round(rsi,1),

            "ema":round(ema,2),

            "vwap":round(vwap,2),

            "volume_spike":volume_spike,

            "breakout":breakout,

            "score":score,

            "probability":score,

            "premarket_high":
                round(float(df5.High.max()),2),

            "premarket_low":
                round(float(df5.Low.min()),2)

        })


    except Exception as e:

        return jsonify({
            "error":str(e)
        })



@app.route("/")

def home():

    return "SST AI Scanner Backend Running"



if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=8501
    )
