import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from crewai.tools import BaseTool
from pydantic import BaseModel
from typing import Optional, ClassVar


class TechnicalAnalysisTool(BaseTool):
    name: str = "TechnicalAnalysisTool"
    description: str = "Performs technical analysis for a given stock."  
    def _run(self, stock_symbol: str, period: str = None, start_date:str=None, end_date:str=None, progress=False) -> dict:
        try:
            print(f"[Technical Tool] Requesting data for {stock_symbol}...")
            if start_date and end_date:
                print(f"Using date range: {start_date} to {end_date}")
                data = yf.download(stock_symbol, start=start_date, end=end_date, progress=False)
            else:
                print(f"Using period: {period}")
                data = yf.download(stock_symbol, period=period, progress=False)

            print(f"Raw data shape: {data.shape}, Columns: {data.columns}")

            # Handle MultiIndex if present
            if isinstance(data.columns, pd.MultiIndex):
                print("MultiIndex detected. Flattening...")
                data = data.swaplevel(axis=1)
                if stock_symbol in data.columns:
                    data = data[stock_symbol]
                    print(f"Flattened data columns: {data.columns}")
                else:
                    return {"error": f"Symbol {stock_symbol} not found in data columns after flattening."}

            if data.empty or 'Close' not in data.columns:
                return {"error": "No data available for symbol."}
            if data['Close'].dropna().shape[0] < 30:
                return {"error": "Too few data points to compute indicators. Try a longer period."}

            # Moving Averages
            for ma in [20, 50, 100, 200]:
                data[f'{ma}_MA'] = data['Close'].rolling(window=ma).mean()

            # Exponential Moving Averages
            for ema in [12, 26, 50, 200]:
                data[f'{ema}_EMA'] = data['Close'].ewm(span=ema, adjust=False).mean()

            expected_ema_columns = ['12_EMA', '26_EMA']
            if not all(col in data.columns for col in expected_ema_columns):
                return {"error": f"Missing EMA columns: {expected_ema_columns}"}

            data = data.dropna(subset=expected_ema_columns)
            if data.empty:
                return {"error": "No data left after removing NaNs from EMA columns."}

            # Indicators
            data['MACD'] = data['12_EMA'] - data['26_EMA']
            data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']

            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))

            data['20_MA'] = data['Close'].rolling(window=20).mean()
            data['20_SD'] = data['Close'].rolling(window=20).std()
            data['Upper_BB'] = data['20_MA'] + (data['20_SD'] * 2)
            data['Lower_BB'] = data['20_MA'] - (data['20_SD'] * 2)

            low_14 = data['Low'].rolling(window=14).min()
            high_14 = data['High'].rolling(window=14).max()
            data['%K'] = (data['Close'] - low_14) / (high_14 - low_14) * 100
            data['%D'] = data['%K'].rolling(window=3).mean()

            data['TR'] = np.maximum(data['High'] - data['Low'],
                                    np.maximum(abs(data['High'] - data['Close'].shift()),
                                               abs(data['Low'] - data['Close'].shift())))
            data['ATR'] = data['TR'].rolling(window=14).mean()
            data['OBV'] = (np.sign(data['Close'].diff()) * data['Volume']).cumsum()

            max_price = data['High'].max()
            min_price = data['Low'].min()
            diff = max_price - min_price
            fibonacci_levels = {
                '0%': max_price,
                '23.6%': max_price - 0.236 * diff,
                '38.2%': max_price - 0.382 * diff,
                '50%': max_price - 0.5 * diff,
                '61.8%': max_price - 0.618 * diff,
                '100%': min_price
            }

            data['Support'] = data['Low'].rolling(window=20).min()
            data['Resistance'] = data['High'].rolling(window=20).max()
            data['Potential_Breakout'] = np.where((data['Close'] > data['Resistance'].shift(1)), 'Bullish Breakout',
                                                  np.where((data['Close'] < data['Support'].shift(1)), 'Bearish Breakdown', 'No Breakout'))

            data['Trend'] = np.where((data['Close'] > data['200_MA']) & (data['50_MA'] > data['200_MA']), 'Bullish',
                                     np.where((data['Close'] < data['200_MA']) & (data['50_MA'] < data['200_MA']), 'Bearish', 'Neutral'))

            data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Trend'] = np.where(data['Volume'] > data['Volume_MA'], 'Above Average', 'Below Average')

            latest = data.iloc[-1]
            analysis_results = {
                'Current_Price': latest['Close'],
                'Moving_Averages': {f'{ma}_MA': latest.get(f'{ma}_MA', None) for ma in [20, 50, 100, 200]},
                'Exponential_MAs': {f'{ema}_EMA': latest.get(f'{ema}_EMA', None) for ema in [12, 26, 50, 200]},
                'MACD': {
                    'MACD': latest.get('MACD', None),
                    'Signal_Line': latest.get('Signal_Line', None),
                    'Histogram': latest.get('MACD_Histogram', None)
                },
                'RSI': latest.get('RSI', None),
                'Bollinger_Bands': {
                    'Upper': latest.get('Upper_BB', None),
                    'Middle': latest.get('20_MA', None),
                    'Lower': latest.get('Lower_BB', None)
                },
                'Stochastic': {
                    '%K': latest.get('%K', None),
                    '%D': latest.get('%D', None)
                },
                'ATR': latest.get('ATR', None),
                'OBV': latest.get('OBV', None),
                'Fibonacci_Levels': fibonacci_levels,
                'Support_Resistance': {
                    'Support': latest.get('Support', None),
                    'Resistance': latest.get('Resistance', None)
                },
                'Potential_Breakout': latest.get('Potential_Breakout', None),
                'Trend': latest.get('Trend', None),
                'Volume': {
                    'Current': latest.get('Volume', None),
                    'MA': latest.get('Volume_MA', None),
                    'Trend': latest.get('Volume_Trend', None)
                },
                'Statistics': {
                    'Yearly_High': data['High'].max(),
                    'Yearly_Low': data['Low'].min(),
                    'Average_Volume': data['Volume'].mean(),
                    'Volatility': data['Close'].pct_change().std() * (252 ** 0.5)
                },
                'Interpretation': {
                    'Trend': 'Bullish' if latest['Close'] > latest.get('200_MA', 0) else 'Bearish',
                    'RSI': 'Overbought' if latest.get('RSI', 0) > 70 else ('Oversold' if latest.get('RSI', 0) < 30 else 'Neutral'),
                    'MACD': 'Bullish' if latest.get('MACD', 0) > latest.get('Signal_Line', 0) else 'Bearish',
                    'Stochastic': 'Overbought' if latest.get('%K', 0) > 80 else ('Oversold' if latest.get('%K', 0) < 20 else 'Neutral'),
                    'Bollinger_Bands': 'Overbought' if latest['Close'] > latest.get('Upper_BB', 0) else ('Oversold' if latest['Close'] < latest.get('Lower_BB', 0) else 'Neutral'),
                    'Volume': 'High' if latest.get('Volume', 0) > latest.get('Volume_MA', 0) else 'Low'
                }
            }

            return analysis_results
        except Exception as e:
            return {"error": str(e)}
