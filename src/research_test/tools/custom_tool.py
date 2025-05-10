import yfinance as yf
import requests
import logging
import pandas as pd
import os
from datetime import datetime
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()

class FundamentalAnalysisTool(BaseTool):
    name: str = "FundamentalAnalysisTool"
    description: str = "Analyze market trends and fundamental performance using key metrics."

    def get_fundamental_data(self, company_ticker: str) -> dict:
        """
        Fetches and analyzes key financial metrics for the company.
        """
        try:
            # Fetching stock data
            stock = yf.Ticker(company_ticker)
            data = stock.info

            # Financial Ratios
            ratios = {
                "P/E Ratio": data.get('trailingPE'),
                "Forward P/E": data.get('forwardPE'),
                "P/B Ratio": data.get('priceToBook'),
                "P/S Ratio": data.get('priceToSalesTrailing12Months'),
                "PEG Ratio": data.get('pegRatio'),
                "Debt to Equity": data.get('debtToEquity'),
                "Current Ratio": data.get('currentRatio'),
                "Quick Ratio": data.get('quickRatio'),
                "ROE": data.get('returnOnEquity'),
                "ROA": data.get('returnOnAssets'),
                "ROIC": data.get('returnOnCapital'),
                "Gross Margin": data.get('grossMargins'),
                "Operating Margin": data.get('operatingMargins'),
                "Net Profit Margin": data.get('profitMargins'),
                "Dividend Yield": data.get('dividendYield'),
                "Payout Ratio": data.get('payoutRatio'),
            }
            valuation = {
                'Market Cap' : data.get('marketCap'),
                "Enterprise_value" : data.get('enterpriseValue'),
                "EV/EBITDA": data.get('enterpriseToEbitda'),
                "EV/Revenue": data.get('enterpriseToRevenue'),
            }

            estimate = {
                "Next Year EPS Estimate": data.get('forwardEps'),
                "Next Year Revenue Estimate": data.get('revenueEstimates', {}).get('avg'),
                "Long-term Growth Rate": data.get('longTermPotentialGrowthRate'),
            }

            # Revenue and Earnings Growth Trends (3 years)
            historical_data = stock.financials.infer_objects(copy=False)
            historical_data = historical_data.ffill()
            revenue_growth = self.calculate_growth(historical_data.loc['Total Revenue'])
            earnings_growth = self.calculate_growth(historical_data.loc['Net Income'])

            # DCF Calculation
            cash_flow = stock.cashflow.infer_objects(copy=False)
            cash_flow = cash_flow.ffill()
            free_cash_flow = cash_flow.loc['Free Cash Flow'].dropna().iloc[0] if 'Free Cash Flow' in cash_flow.index else None
            growtRate =  data.get('longTermPotentialGrowthRate', 0.03)
            dcf_value = self.calculate_dcf(free_cash_flow, growtRate)

            growth = {
                "Revenue Growth (3Y)": revenue_growth,
                "Net Income Growth (3Y)": earnings_growth,
            }

            analysis = {
                "Company Name": data.get('longName'),
                "Sector": data.get('sector'),
                "Industry": data.get('industry'),
                "Financial Ratios": ratios,
                "Growth Rates" : growth,
                "DCF Valuation": dcf_value,
                "Future Estimation" : estimate,
                "Last Updated": datetime.fromtimestamp(data.get('lastFiscalYearEnd', 0)).strftime('%Y-%m-%d'),
                "Data Retrieval Date": datetime.now().strftime('%Y-%m-%d'),
            }

            interpretation = {
                "P/E Ratio": "High" if ratios.get('P/E Ratio', 0) > 25 else "Moderate",
                "Debt to Equity": "High Leverage" if ratios.get('Debt to Equity', 0) > 2 else "Healthy Leverage",
                "ROE": "Strong" if ratios.get('ROE', 0) > 0.2 else "Average",
                "Revenue Growth": "High Growth" if revenue_growth > 15 else "Moderate Growth"
            }

            analysis["Interpretations"] = interpretation
            return analysis
        except Exception as e:
            return {"error": str(e)}

    def calculate_growth(self, data: pd.Series, years: int=3) -> float:
        try:
            if len(data) < years:
                return "Not enough data to calculate growth."
            start_value = data.iloc[0]
            end_value = data.iloc[years-1]

            CAGR = ((end_value / start_value) ** (1 / years)) - 1
            growth_percentage = CAGR * 100
            return growth_percentage
        except Exception:
            return "Growth data not available."

    def calculate_dcf(self, fcf: float, growth_rate: float, years= 5) -> str:
        try:
            if fcf is None or pd.isna(fcf):
                return "DCF valuation not available: FCF is NaN"
            discount_rate = 0.1
            terminal_val = fcf * (1 + growth_rate) / (discount_rate - growth_rate)
            projected_cashflows = [fcf * (1 + growth_rate) ** i for i in range(1, years + 1)]
            dcf_value = sum([cf / (1 + discount_rate) ** i for i, cf in enumerate(projected_cashflows, 1)])

            # Discount the terminal value to present value
            total_dcf_value = dcf_value + terminal_val / (1 + discount_rate) ** years

            return total_dcf_value


        except Exception as e:
            return f"DCF valuation not available: {str(e)}"

    def _run(self, company_ticker: str) -> dict:
        return self.get_fundamental_data(company_ticker)

class GoogleSerperSearch(BaseTool):
    name: str = "Google Search News Tool"
    description: str = "Scrape news from Google search using the Serper API, utilizing full company name."
    _cache = {}

    def get_company_name(self, ticker: str) -> str:
        """
        Retrieve the full company name from Yahoo Finance based on the stock ticker.
        """
        try:
            stock = yf.Ticker(ticker)
            company_name = stock.info.get("longName", ticker)  # Jika tidak ditemukan, gunakan ticker sebagai fallback
            return company_name
        except Exception as e:
            logging.error(f"Error retrieving company name for {ticker}: {e}")
            return ticker  # Jika gagal, gunakan ticker saja

    def get_news(self, company_ticker: str) -> dict:
        if company_ticker in self._cache:
            return self._cache[company_ticker]

        try:
            api_key = os.environ.get('SERPER_API')
            if not api_key:
                return {"error": "API key is missing. Set the SERPER_API environment variable."}

            company_name = self.get_company_name(company_ticker)
            api_url = "https://google.serper.dev/search"
            params = {"q": f"{company_name} stock news"}  # Menggunakan nama perusahaan untuk hasil lebih akurat
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            }

            logging.info(f"Fetching news for {company_name} ({company_ticker})")
            response = requests.get(api_url, headers=headers, params=params)

            if response.status_code != 200:
                return {"error": f"Failed to retrieve data: {response.status_code}", "details": response.text}

            news_data = response.json()
            if 'organic' not in news_data:
                return {"error": f"No news found for {company_name}."}

            news_articles = [
                {'title': a.get('title', 'No title'), 'url': a.get('link', ''),
                 'summary': a.get('snippet', 'No summary'), 'sentiment': self.analyze_sentiment(a.get('snippet', ''))}
                for a in news_data.get('organic', [])[:5]  # Ambil maksimal 5 berita
            ]

            self._cache[company_ticker] = news_articles
            return news_articles
        except Exception as e:
            logging.error(f"Error retrieving news for {company_ticker}: {e}")
            return {"error": str(e)}

    def analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis based on keywords."""
        positive_keywords = ["growth", "profit", "expansion", "positive", "record high"]
        negative_keywords = ["loss", "decline", "drop", "negative", "plunge"]
        if any(keyword in text.lower() for keyword in positive_keywords):
            return "positive"
        elif any(keyword in text.lower() for keyword in negative_keywords):
            return "negative"
        else:
            return "neutral"

    def _run(self, company_ticker: str) -> dict:
        return self.get_news(company_ticker)

class MacroeconomicTool(BaseTool):
    name: str = "MacroEconomicDataTool"
    description: str = "Tool to fetch macroeconomic data such as GDP, inflation, unemployment, etc."

    # Konfigurasi agar Pydantic tidak memproses tipe tertentu (str, dict, dsb)
    model_config = {
        "ignored_types": (str, dict),
    }

    def get_country_code(self, country_name: str) -> str:
        country_list = [
            ('Albania', 'AL'), ('Algeria', 'DZ'), ('Angola', 'AO'), ('Argentina', 'AR'),
            ('Australia', 'AU'), ('Austria', 'AT'), ('Azerbaijan', 'AZ'), ('Bangladesh', 'BD'),
            ('Belarus', 'BY'), ('Belgium', 'BE'), ('Bolivia', 'BO'), ('Bosnia And Herzegovina', 'BA'),
            ('Brazil', 'BR'), ('Bulgaria', 'BG'), ('Cambodia', 'KH'), ('Canada', 'CA'),
            ('Chile', 'CL'), ('China', 'CN'), ('Colombia', 'CO'), ('Costa Rica', 'CR'),
            ('Croatia', 'HR'), ('Cyprus', 'CY'), ('Czechia', 'CZ'), ('Democratic Republic Of Congo', 'CD'),
            ('Denmark', 'DK'), ('Dominican Republic', 'DO'), ('Ecuador', 'EC'), ('Egypt', 'EG'),
            ('El Salvador', 'SV'), ('Estonia', 'EE'), ('Ethiopia', 'ET'), ('European Union', 'EU'),
            ('Finland', 'FI'), ('France', 'FR'), ('Germany', 'DE'), ('Ghana', 'GH'),
            ('Greece', 'GR'), ('Guatemala', 'GT'), ('Honduras', 'HN'), ('Hong Kong', 'HK'),
            ('Hungary', 'HU'), ('India', 'IN'), ('Indonesia', 'ID'), ('Iran', 'IR'),
            ('Iraq', 'IQ'), ('Ireland', 'IE'), ('Israel', 'IL'), ('Italy', 'IT'),
            ('Japan', 'JP'), ('Jordan', 'JO'), ('Kazakhstan', 'KZ'), ('Kenya', 'KE'),
            ('Kuwait', 'KW'), ('Kyrgyzstan', 'KG'), ('Laos', 'LA'), ('Latvia', 'LV'),
            ('Lebanon', 'LB'), ('Libya', 'LY'), ('Lithuania', 'LT'), ('Luxembourg', 'LU'),
            ('Macao', 'MO'), ('Malaysia', 'MY'), ('Mexico', 'MX'), ('Mongolia', 'MN'),
            ('Morocco', 'MA'), ('Myanmar', 'MM'), ('Nepal', 'NP'), ('Netherlands', 'NL'),
            ('New Zealand', 'NZ'), ('Nicaragua', 'NI'), ('Nigeria', 'NG'), ('Norway', 'NO'),
            ('Oman', 'OM'), ('Pakistan', 'PK'), ('Panama', 'PA'), ('Paraguay', 'PY'),
            ('Peru', 'PE'), ('Philippines', 'PH'), ('Poland', 'PL'), ('Portugal', 'PT'),
            ('Qatar', 'QA'), ('Romania', 'RO'), ('Russian Federation', 'RU'), ('Saudi Arabia', 'SA'),
            ('Senegal', 'SN'), ('Serbia', 'RS'), ('Singapore', 'SG'), ('Slovakia', 'SK'),
            ('Slovenia', 'SI'), ('South Africa', 'ZA'), ('South Korea', 'KR'), ('Spain', 'ES'),
            ('Sri Lanka', 'LK'), ('Sudan', 'SD'), ('Sweden', 'SE'), ('Switzerland', 'CH'),
            ('Taiwan', 'TW'), ('Tajikistan', 'TJ'), ('Tanzania', 'TZ'), ('Thailand', 'TH'),
            ('Tunisia', 'TN'), ('Turkey', 'TR'), ('Turkmenistan', 'TM'), ('Ukraine', 'UA'),
            ('United Arab Emirates', 'AE'), ('United Kingdom', 'UK'), ('United States', 'US'),
            ('Uruguay', 'UY'), ('Uzbekistan', 'UZ'), ('Venezuela', 'VE'), ('Vietnam', 'VN')
        ]
        country_df = pd.DataFrame(country_list, columns=['name', 'iso2'])
        row = country_df[country_df['name'] == country_name]
        return row.iloc[0]['iso2'] if not row.empty else None

    def get_macro_data(self, series_code: str) -> pd.DataFrame:
        api_token = os.getenv('ECONDB_API_TOKEN')
        if not api_token:
            raise ValueError("API token is missing. Set the ECONDB_API_TOKEN environment variable.")

        url = f"https://www.econdb.com/api/series/{series_code}/?token={api_token}&format=csv"
        df = pd.read_csv(url, index_col='Date', parse_dates=['Date'])

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=5)
        filtered_df = df.loc[start_date:end_date]
        return filtered_df

    def _run(self, company_ticker: str) -> dict:
        try:
            stock_info = yf.Ticker(company_ticker).info
            country_name = stock_info.get('country', None)
            if not country_name:
                return {"error": "Unable to determine the country for the given stock ticker."}

            country_code = self.get_country_code(country_name)
            if not country_code:
                return {"error": "Country code not found for the given country."}

            return {
                "GDP": self.get_macro_data(f'GDP{country_code}').to_dict(),
                "Inflation": self.get_macro_data(f'CPI{country_code}').to_dict(),
                "Unemployment": self.get_macro_data(f'URATE{country_code}').to_dict(),
            }
        except Exception as e:
            return {"error": str(e)}
