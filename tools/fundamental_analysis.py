import yfinance as yf
import logging
import pandas as pd
import os
from datetime import datetime
from crewai.tools import BaseTool

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
                "P/E Ratio": (
                    "High" if ratios.get('P/E Ratio') is not None and ratios.get('P/E Ratio') > 25
                    else "Moderate" if ratios.get('P/E Ratio') is not None
                    else "Unknown"
                ),
                "Debt to Equity": (
                    "High Leverage" if ratios.get('Debt to Equity') is not None and ratios.get('Debt to Equity') > 2
                    else "Healthy Leverage" if ratios.get('Debt to Equity') is not None
                    else "Unknown"
                ),
                "ROE": (
                    "Strong" if ratios.get('ROE') is not None and ratios.get('ROE') > 0.2
                    else "Average" if ratios.get('ROE') is not None
                    else "Unknown"
                ),
                "Revenue Growth": (
                    "High Growth" if isinstance(revenue_growth, (int, float)) and revenue_growth > 15
                    else "Moderate Growth" if isinstance(revenue_growth, (int, float))
                    else "Unknown"
                )
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
