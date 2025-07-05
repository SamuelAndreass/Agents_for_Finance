import yfinance as yf
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from crewai.tools import BaseTool

class FundamentalAnalysisQuarterlyTool(BaseTool):
    name: str = "FundamentalAnalysisQuarterlyTool"
    description: str = "Extract quarterly fundamental ratios, growth, and valuation data using Yahoo Finance and yfinance."

    def _run(self, ticker: str, year: int, quarter: int) -> dict:
        analyzer = _InternalFundamentalAnalyzer(ticker)
        return analyzer.full_quarterly_report(year, quarter)


class _InternalFundamentalAnalyzer:
    def __init__(self, ticker):
        self.ticker = ticker
        self.yf_ticker = yf.Ticker(ticker)
        self.q_income = self.yf_ticker.quarterly_financials
        self.q_bs = self.yf_ticker.quarterly_balance_sheet
        self.q_cf = self.yf_ticker.quarterly_cashflow

    def get_value(self, df, label, quarter_date):
        try:
            return df.loc[label, quarter_date]
        except Exception:
            return None

    def get_prev_quarter(self, df, quarter_date):
        cols = list(df.columns)
        if quarter_date in cols:
            idx = cols.index(quarter_date)
            if idx + 1 < len(cols):
                return cols[idx + 1]
        return None

    def valuation_measures_per_quarter(self, year, quarter):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        })
        driver = webdriver.Chrome(options=chrome_options)

        url = f"https://finance.yahoo.com/quote/{self.ticker}/key-statistics?p={self.ticker}"
        driver.get(url)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
        except Exception:
            driver.quit()
            return None

        html = driver.page_source
        driver.quit()

        tables = pd.read_html(html, flavor="lxml")
        for df in tables:
            if 'Market Cap' in df.iloc[:, 0].values:
                df = df.set_index(df.columns[0])
                col_map = {
                    1: f"3/31/{year}",
                    2: f"6/30/{year}",
                    3: f"9/30/{year}",
                    4: f"12/31/{year}",
                }
                col = col_map.get(quarter)
                if col in df.columns:
                    return df[col].to_dict()
        return None

    def analyze_quarter(self, quarter_date):
        q_income = self.q_income
        q_bs = self.q_bs
        q_cf = self.q_cf

        if quarter_date not in q_income.columns:
            raise Exception(f"Quarter {quarter_date} not available.")

        prev_q = self.get_prev_quarter(q_income, quarter_date)
        result = {}

        revenue = self.get_value(q_income, "Total Revenue", quarter_date)
        net_income = self.get_value(q_income, "Net Income", quarter_date)
        prev_revenue = self.get_value(q_income, "Total Revenue", prev_q) if prev_q else None
        prev_net_income = self.get_value(q_income, "Net Income", prev_q) if prev_q else None

        result["revenue"] = revenue
        result["net_income"] = net_income
        result["revenue_growth_vs_prev"] = ((revenue - prev_revenue) / abs(prev_revenue) * 100) if (prev_revenue and revenue) else None
        result["net_income_growth_vs_prev"] = ((net_income - prev_net_income) / abs(prev_net_income) * 100) if (prev_net_income and net_income) else None

        gross_profit = self.get_value(q_income, "Gross Profit", quarter_date)
        operating_income = self.get_value(q_income, "Operating Income", quarter_date)
        result["gross_margin"] = gross_profit / revenue * 100 if gross_profit and revenue else None
        result["operating_margin"] = operating_income / revenue * 100 if operating_income and revenue else None
        result["net_margin"] = net_income / revenue * 100 if net_income and revenue else None

        result["free_cash_flow"] = self.get_value(q_cf, "Free Cash Flow", quarter_date)
        result["operating_cash_flow"] = self.get_value(q_cf, "Operating Cash Flow", quarter_date)

        result["cash_equivalents"] = self.get_value(q_bs, "Cash And Cash Equivalents", quarter_date)
        result["total_debt"] = self.get_value(q_bs, "Total Debt", quarter_date)
        result["net_debt"] = self.get_value(q_bs, "Net Debt", quarter_date)
        result["eps"] = self.get_value(q_income, "Diluted EPS", quarter_date)
        result["buyback"] = self.get_value(q_cf, "Repurchase Of Capital Stock", quarter_date)
        result["dividend"] = self.get_value(q_cf, "Cash Dividends Paid", quarter_date)

        try:
            current_assets = self.get_value(q_bs, "Total Current Assets", quarter_date)
            current_liabilities = self.get_value(q_bs, "Total Current Liabilities", quarter_date)
            if current_assets and current_liabilities:
                result["current_ratio"] = current_assets / current_liabilities

            total_equity = self.get_value(q_bs, "Total Stockholder Equity", quarter_date)
            if result["total_debt"] and total_equity:
                result["debt_to_equity"] = result["total_debt"] / total_equity
            if total_equity and net_income:
                result["roe"] = net_income / total_equity * 100
            total_assets = self.get_value(q_bs, "Total Assets", quarter_date)
            if total_assets and net_income:
                result["roa"] = net_income / total_assets * 100
        except Exception as e:
            result["ratio_error"] = str(e)

        return result

    def full_quarterly_report(self, year, quarter):
        quarter_map = {
            1: pd.Timestamp(f"{year}-03-31"),
            2: pd.Timestamp(f"{year}-06-30"),
            3: pd.Timestamp(f"{year}-09-30"),
            4: pd.Timestamp(f"{year}-12-31"),
        }
        quarter_date = quarter_map[quarter]
        data = self.yf_ticker.info

        try:
            analysis = self.analyze_quarter(quarter_date)
        except Exception:
            analysis = {}

        try:
            val_measures = self.valuation_measures_per_quarter(year, quarter)
        except Exception:
            val_measures = {}

        return {
            "Company Name": data.get('longName', self.ticker),
            "Sector": data.get('sector', '-'),
            "Industry": data.get('industry', '-'),
            "Quarter": str(quarter_date.date()),
            "Financial Ratios": {
                "Gross Margin (%)": analysis.get("gross_margin"),
                "Operating Margin (%)": analysis.get("operating_margin"),
                "Net Margin (%)": analysis.get("net_margin"),
                "Current Ratio": analysis.get("current_ratio"),
                "Debt to Equity": analysis.get("debt_to_equity"),
                "ROE (%)": analysis.get("roe"),
                "ROA (%)": analysis.get("roa"),
            },
            "Growth Rates": {
                "Revenue Growth QoQ": analysis.get("revenue_growth_vs_prev"),
                "Net Income Growth QoQ": analysis.get("net_income_growth_vs_prev"),
            },
            "EPS": analysis.get("eps"),
            "Free Cash Flow": analysis.get("free_cash_flow"),
            "Operating Cash Flow": analysis.get("operating_cash_flow"),
            "Cash & Equivalents": analysis.get("cash_equivalents"),
            "Total Debt": analysis.get("total_debt"),
            "Net Debt": analysis.get("net_debt"),
            "Buyback": analysis.get("buyback"),
            "Dividend": analysis.get("dividend"),
            "Valuation Measures": val_measures,
            "Data Retrieval Date": datetime.now().strftime('%Y-%m-%d')
        }
