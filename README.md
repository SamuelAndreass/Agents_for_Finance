## Stock Assistant AI Chatbot [![Streamlit](https://img.shields.io/badge/streamlit-latest-brightgreen)](https://streamlit.io/)  [![OpenAI API](https://img.shields.io/badge/OpenAI-API-blue)](https://platform.openai.com/) [![CrewAI](https://img.shields.io/badge/CrewAI-v1.0-orange)](https://github.com/your-crewai-repo-link)

**Stock Assistant AI Chatbot** is an interactive AI-powered chatbot designed to assist with automated financial market analysis using a modular multi-agent approach. The system leverages large language models (LLMs) alongside specialized analytical tools to provide:

- Evaluate company financial health using key financial ratios and Discounted Cash Flow (DCF) valuation methods.  
- Analyze stock price data with indicators such as RSI, MACD, Bollinger Bands, moving averages, Fibonacci retracements, and breakout patterns.  
- Retrieve macroeconomic data including GDP, inflation, and unemployment rates based on country or stock ticker input.  

The system is built on the **CrewAI** framework for orchestrating multiple agents, with a user-friendly **Streamlit** frontend.

## Key Features

- Automatic intent detection to route user queries to the appropriate analysis agent (fundamental, technical, macroeconomic, or conversational).  
- Input validation for stock tickers and country names.  
- Integration with Yahoo Finance and EconDB APIs for financial and macroeconomic data retrieval.  
- Summarizer agent to generate concise summaries of multi-agent analysis results.  
- Modular multi-agent architecture for easy extension and maintenance.  
- Interactive chatbot interface with real-time AI responses.


## Project Structure

| File                      | Description                                                  |
|---------------------------|--------------------------------------------------------------|
| `app.py`                  | Streamlit app entry point handling UI and user interactions  |
| `crew.py`                 | Definitions of agents, tasks, and crew (multi-agent orchestration) |
| `fundamental_analysis.py` | Tool for fundamental stock analysis using yfinance           |
| `technical_analysis.py`   | Tool for technical stock analysis with various indicators    |
| `macroeconom_analysis.py` | Tool for macroeconomic data retrieval (GDP, CPI, Unemployment, etc.) |
| `config/agents.yaml`      | CrewAI agents configuration file                             |
| `config/tasks.yaml`       | CrewAI tasks configuration file                              |

## Usage

- Enter financial analysis queries or commands in the chat input, for example:  
  - `Fundamental analysis AAPL`  
  - `Technical analysis BBCA.JK for 3mo`  
  - `What's the macro outlook for Indonesia?`  

- The system automatically detects the user intent and dispatches the query to the corresponding agent(s), then summarizes and returns the response in the chat.

## System Architecture

![image](https://github.com/user-attachments/assets/04553028-6d3a-4c65-8335-06e4cbaedd86)

- **Intent Router Agent:** Classifies user intent and routes the request to the appropriate agent  
- **Fundamental Agent:** Runs fundamental financial analysis using `FundamentalAnalysisTool`  
- **Technical Agent:** Performs technical stock analysis via `TechnicalAnalysisTool`  
- **Macro Agent:** Fetches macroeconomic data through `MacroeconomicTool`  
- **Summarizer Agent:** Generates concise summaries from multi-agent outputs  
- **Conversational Agent:** Handles natural language questions unrelated to specific analyses  

## References
- Yahoo Finance API via [yfinance](https://github.com/ranaroussi/yfinance)  
- CrewAI multi-agent framework : [CrewAI](https://docs.crewai.com/introduction)
- OpenAI GPT models: [OpenAI Platform](https://platform.openai.com)  
- EconDB API for macroeconomic data: [EconDB](https://www.econdb.com/api/)  
- Streamlit: [streamlit.io](https://streamlit.io)
  
## Acknowledgements
Some analytical tools and utilities in the `tools/` directory were adapted from:
[YBSener/financial_Agent](https://github.com/YBSener/financial_Agent)
