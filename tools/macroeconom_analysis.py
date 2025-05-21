from pydantic import BaseModel
from crewai.tools import BaseTool
import yfinance as yf
import pandas as pd
import os
from dotenv import load_dotenv
from typing import Type
load_dotenv()

# ✅ Pydantic schema for tool input
class MacroeconomicToolInput(BaseModel):
    description: str  # Wajib field ini agar CrewAI tahu bahwa "input" harus string

class MacroeconomicTool(BaseTool):
    name: str = "MacroEconomicDataTool"
    description: str = "Tool to fetch macroeconomic data such as GDP, inflation, unemployment, etc. Accepts either a stock ticker or a country name."
    args_schema: Type[BaseModel] = MacroeconomicToolInput

    def get_country_code(self, country_name: str) -> str:
        # Daftar negara dan kode-nya
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
        df = pd.DataFrame(country_list, columns=['name', 'code'])
        country_name_clean = country_name.strip().lower()

        match = df[df['name'].str.lower() == country_name_clean]
        if not match.empty:
            return match.iloc[0]['code']

        partial = df[df['name'].str.lower().str.contains(country_name_clean)]
        if not partial.empty:
            return partial.iloc[0]['code']
        return None

    def get_macro_data(self, series_code: str) -> pd.DataFrame:
        url = f"https://www.econdb.com/api/series/{series_code}/?token=6c2b3a95a441987ce777a9133aa601d957d4be35&format=csv"
        df = pd.read_csv(url, index_col='Date', parse_dates=['Date'])
        df = df.last('5YE')
        return df

    def _run(self, description: str) -> dict:
        # Defensive: handle if input is unexpectedly a dict
        input = description.strip()

        try:
            country_code = self.get_country_code(input)
            if not country_code:
                info = yf.Ticker(input).info
                if not info or "country" not in info:
                    return {"error": "Could not resolve country from input."}
                country_code = self.get_country_code(info["country"])

            if not country_code:
                return {"error": f"Unrecognized country: {input}"}

            return {
                "GDP": self.get_macro_data(f"GDP{country_code}").to_dict(),
                "Inflation": self.get_macro_data(f"CPI{country_code}").to_dict(),
                "Unemployment": self.get_macro_data(f"URATE{country_code}").to_dict(),
            }

        except Exception as e:
            return {"error": str(e)}
