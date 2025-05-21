import startup_env_patch
import streamlit as st
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yaml
import json
from openai import OpenAI
from crew import FinancialCrew
import openai
from crewai import Crew, Process
import re
import yfinance as yf
from tools.macroeconom_analysis import MacroeconomicTool
# Load environment variables

# ========== Streamlit Config ==========
st.set_page_config(page_title="Financial Chatbot", page_icon="💬", layout="wide")
warnings.filterwarnings("ignore")

# ========== Helper Functions ==========

def load_agent_configs(config_path="./config/agents.yaml"):
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"Error loading agent configs: {e}")
        return None

def is_valid_openai_key(api_key: str) -> bool:
    try:
        client = openai.OpenAI(api_key=api_key)
        _ = client.models.list()
        return True
    except Exception as e:
        print("[API KEY INVALID]", str(e))
        return False

# ========== API Key Setup Page ==========
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if not st.session_state.authenticated:    
    st.title("💬 Financial Assistant")
    st.warning("We don't save any of your API key. It is only saved in current session", icon="⚠️")
    if not st.session_state.authenticated:
        st.session_state.api_key = st.text_input("API Key", type="password")
        if st.button("Continue"):
            if st.session_state.api_key.startswith("sk-") and len(st.session_state.api_key) > 20:
                st.session_state.authenticated = True
                st.success("Your API Key is valid. Redirecting to main page...")
                st.rerun()
            else:
                st.error("Your API key is not valid. input OPEN API key with 'sk-'.")

        st.stop()


class GenericChatAgent:
    def __init__(self, agent_config, api_key=None):
        self.agent_config = agent_config
        self.api_key = api_key
        self.system_prompt = f"Role: {agent_config.get('role', '')}\\nGoal: {agent_config.get('goal', '')}\\nBackstory: {agent_config.get('backstory', '')}\\nInstructions: {agent_config.get('prompt', '')}"
        self.history = [{"role": "system", "content": self.system_prompt}]

    def query(self, user_prompt):
        if not user_prompt:
            return "Ask someting..."
        client = OpenAI(api_key=self.api_key)
        self.history.append({"role": "user", "content": user_prompt})
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.history,
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"Error: {str(e)}"

        self.history.append({"role": "assistant", "content": reply})
        return reply

def initialize_agent(agent_name, agent_configs, api_key):
    if agent_configs and agent_name in agent_configs:
        agent_config = agent_configs[agent_name]
        return GenericChatAgent(agent_config, api_key)
    return None

# ========== Session State Initialization ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_interaction" not in st.session_state:
    st.session_state.last_interaction = datetime.now()
if "agent_configs" not in st.session_state:
    st.session_state.agent_configs = load_agent_configs()

api_key = api_key = st.session_state.api_key
configs = st.session_state.agent_configs

# Inisialisasi Agents
if "intent_router_agent" not in st.session_state:
    st.session_state.intent_router_agent = initialize_agent("intent_router", configs, api_key)
if "fundamental_agent" not in st.session_state:
    st.session_state.fundamental_agent = initialize_agent("fundamental", configs, api_key)
if "macro_agent" not in st.session_state:
    st.session_state.macro_agent = initialize_agent("macro", configs, api_key)
if "summarizer_agent" not in st.session_state:
    st.session_state.summarizer_agent = initialize_agent("summarizer", configs, api_key)
if "main_conversational_agent" not in st.session_state:
    st.session_state.main_conversational_agent = initialize_agent("conversational_agent", configs, api_key)

# Cache CrewAI object
def get_crew():
    return FinancialCrew()
crew = get_crew()

# ========== Check Ticker ==========
def is_valid_ticker(company_ticker):
    try:
        ticker = yf.Ticker(company_ticker)
        inf = ticker.info
        # Bisa juga cek data harga
        price_data = ticker.history(period="1d")
        if (
            inf is None
            or not isinstance(inf, dict)
            or "shortName" not in inf
            or inf.get("regularMarketPrice") is None
            or price_data.empty
        ):
            return False
        return True
    except Exception as e:
        print(f"[Ticker Validation Exception] {e}")
        return False
    
# ========== is valid ticker or country ==========
def is_valid_company(input_text):
    try:
        info = yf.Ticker(input_text).info
        return info is not None and "country" in info and info["country"] is not None
    except Exception:
        return False
def is_valid_country(country_input):
    macro_tool = MacroeconomicTool()
    code = macro_tool.get_country_code(country_input)
    return code is not None

def is_valid_macro_input(input_text):
    return is_valid_country(input_text) or is_valid_company(input_text)
# ========== Agent Logic (merged from main.py) ==========
def run_agent_by_intent(intent_data, crew: FinancialCrew, user_input: str):
    entities = intent_data.get("entities", {})
    company_ticker = (
        entities.get("company_ticker")
        or entities.get("ticker")
        or entities.get("ticker_symbol")
        or entities.get("company")
        or entities.get("stock")
        or entities.get("stock_symbol")
    )
    intent = intent_data.get("intent", "").lower()
    print("[Intent]", intent)
    print("[entities]", entities)
    print("[Ticker]", company_ticker)
    print("[Country]", entities.get("country"))

    if intent == "fundamental_analysis" and company_ticker:
        if not is_valid_ticker(company_ticker):
            return 'Ticker not found! please input the correct ticker name (Read Descalimer).'
        print(f"[Dispatcher] Running fundamental analysis for {company_ticker}")
        fundamental_crew = Crew(
            agents=[crew.fundamental()],
            tasks=[crew.fundamental_task()],
            process=Process.sequential,
            verbose=True,
        )
        print("[Fundamental Input Given]", company_ticker)
        print("[TASK DESCRIPTION]", crew.fundamental_task().description)
        result = fundamental_crew.kickoff(inputs={"company_ticker": company_ticker})
        return result

    elif intent == "technical_analysis":
        period = entities.get("period") or intent_data.get("period")   # backup, in case LLM outputs directly
        if not is_valid_ticker(company_ticker):
            return 'Ticker not found! please input the correct ticker name (Read Descalimer).'
        if not company_ticker:
            return "Please specify the stock ticker you want technical analysis for. Example: 'Technical analysis AAPL for 3 months.'"
        
        print(f"[Dispatcher] Running technical analysis for {company_ticker} ({period})")
        technical_crew = Crew(
            agents=[crew.technical_agent()],
            tasks=[crew.technical_task()],
            process=Process.sequential,
            verbose=True,
        )
        result = technical_crew.kickoff(inputs={"stock_symbol": company_ticker, "period": period})
        return result

    elif intent == "macro_outlook":
        macro_input = entities.get("country") or company_ticker or user_input

        if isinstance(macro_input, dict):
            macro_input = macro_input.get("description", "")
        
        print("[Normalized Macro Input]", macro_input)

        valid = is_valid_macro_input(macro_input)
        print("is_valid_macro_input:", valid)

        if not valid:
            return "Country or ticker not found! please input the correct ticker or country name (Read Descalimer)."
        else:
            print(f"[Dispatcher] Running macroeconomic analysis with input: {macro_input}")
            macro_crew = Crew(
                agents=[crew.macro()],
                tasks=[crew.macro_task()],
                process=Process.sequential,
                verbose=True,
            )
            print("[Macro Input Given]", macro_input)
            print("[TASK DESCRIPTION]", crew.macro_task().description)
            if isinstance(macro_input, dict):
                macro_input = macro_input.get("description", "") or ""
            macro_input = str(macro_input).strip()
            result = macro_crew.kickoff(inputs={'input' : macro_input})
            return result

    
    elif intent == "conversation":
        print("[Dispatcher] Running conversational agent.")
        return st.session_state.main_conversational_agent.query(user_input)

    return "Sorry, I couldn't understand your request or the input was missing."

def is_error_message(report):
    if not isinstance(report, str):
        return False
    msg = report.lower()
    return any([
        "couldn't understand" in msg,
        "please specify the stock ticker" in msg,
        "sorry" in msg,
        "error" in msg,
        "not found" in msg,
        "no data available" in msg,
        "missing" in msg,
        "Please check your input" in msg
    ])

def handle_user_query(crew, prompt, chat_history):
    # Step 1: Detect intent
    intent_output = st.session_state.intent_router_agent.query(prompt)
    print("=== INTENT DETECTED ===")
    print(intent_output)
    try:
        intent_data = json.loads(intent_output)
        if "intent" not in intent_data or "entities" not in intent_data:
            raise ValueError("Invalid format: Missing keys.")
    except Exception as e:
         print("[Intent Parsing Error]", str(e))
         return "Sorry, I couldn’t understand your request.", chat_history
    # Step 2: Run agent based on intent
    allowed_intents = ["fundamental_analysis", "technical_analysis", "macro_outlook"]

    if intent_data["intent"] not in allowed_intents:
        return "I'm currently focused on financial analysis such as fundamental, technical, or macroeconomic insights. Please ask something related to those topics.", chat_history

    report = run_agent_by_intent(intent_data, crew, prompt)
    str_report = str(report)
    # Cek dulu apakah report adalah pesan error
    if not report or is_error_message(report):
    # Kalau error, langsung return tanpa proses summary
        return report, chat_history

    # Step 3: Summarize output jika bukan hasil dari main_conversational_agent
    if intent_data.get("intent") != "conversation":
        summary_prompt = f"""
        Here is the result of the technical or fundamental analysis or macroeconomic analysis:
        {str_report}

        PUser request was: "{prompt}"

         Please summarize only the information relevant to the request. If the user mentioned specific elements like RSI or MACD, just highlight those points. If nothing specific is mentioned, provide a general and comprehensive summary.
        """

        summary = st.session_state.summarizer_agent.query(summary_prompt)

        print(f"summary result {summary}")
        return summary, chat_history + [{"role": "assistant", "content": summary}]
    else:
        # Kalau sudah langsung hasil dari conversational agent
        return report, chat_history + [{"role": "assistant", "content": report}]

def clean_llm_markdown(text):
    # Remove excessive backslashes, e.g. \\n, \|, \t, etc
    return text.replace("\\n", "\n").replace("\\|", "|").replace("\\\\", "\\")

# ========== Chat UI ==========
st.title("💬 Financial Assistant")
with st.expander("ℹ️Disclaimerℹ️"):
    st.markdown('''
        This chatbot is your **AI-powered Financial Assistant**.  
        It can help you with a variety of financial insights and tasks.:

        ### 🧠 Supported Capabilities:
        - **📊 Technical Analysis**  
          Get insights on stock trends, RSI, MACD, Bollinger Bands, and more.
        - **📈 Fundamental Analysis**  
          Analyze company fundamentals such as earnings, P/E ratio, revenue, etc.
        - **🌍 Macroeconomic Outlook**  
          Understand trends at the national (e.g., inflation, GDP).
        - **💬 Conversational Q&A**  
          Ask follow-up questions, get explanations, or explore financial topics in natural language.
        - **🔍 Ticker Interpretation**  
          Automatically understands stock symbols like AAPL, NVDA, or TSLA.

        ### ⚠️ International Ticker Format Notice:
        For **non-U.S. stock tickers**, make sure to include the correct exchange suffix.  
        Examples:
        - Indonesian stocks → BBCA.JK, TLKM.JK
        - Japanese stocks → 7203.T (Toyota)
        - London stocks → VOD.L (Vodafone)
        - Toronto stocks → RY.TO (Royal Bank of Canada)

        If you're unsure, refer to the ticker format used on Yahoo Finance.
        
                
        ### ⚠️ DISCLAIMER ⚠️ :
        The analysis is not 100% correct, DYOR (Do your own research)
        
    ''')


timeout_minutes = 30
now = datetime.now()
if now - st.session_state.last_interaction > timedelta(minutes=timeout_minutes):
    st.session_state.messages = []
    st.session_state.chat_history = []
    st.warning("Session timed out. Chat cleared.")
    st.session_state.last_interaction = now

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input field
prompt = st.chat_input("Ask me anything...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response, updated_history = handle_user_query(crew, prompt, st.session_state.chat_history)
            st.session_state.chat_history = updated_history
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(clean_llm_markdown(response))
    st.session_state.last_interaction = datetime.now()

