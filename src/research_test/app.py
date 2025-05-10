import streamlit as st
import os
import sys
import warnings
from datetime import datetime
from dotenv import load_dotenv
from crew import FinancialCrew

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Load environment variables
load_dotenv()

# Set up page configuration
st.set_page_config(
    page_title="Financial Investment Advisor",
    page_icon="💹",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #2563EB;
        margin-top: 1rem;
    }
    .stAlert {
        background-color: #EFF6FF;
        border-left-color: #3B82F6;
    }
    .info-box {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown('<p class="main-header">Financial AI Advisor</p>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
    
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = ""
    
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

# Sidebar for settings
with st.sidebar:
    st.markdown('<p class="sub-header">Investment Parameters</p>', unsafe_allow_html=True)
    
    company_ticker = st.text_input("Stock Ticker Symbol", "AAPL")
    
    st.markdown('<div class="info-box">Add .JK suffix for Indonesian stocks (e.g., BBRI.JK)</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        time_horizon = st.selectbox(
            "Investment Timeframe",
            ["Short-term", "Medium-term", "Long-term"]
        )
    with col2:
        risk_tolerance = st.select_slider(
            "Risk Tolerance",
            options=["Low", "Moderate", "High"]
        )
    
    st.divider()
    
    if st.button("Run Financial Analysis", use_container_width=True):
        with st.spinner("Running comprehensive financial analysis..."):
            try:
                # Store the current ticker being analyzed
                st.session_state.current_ticker = company_ticker
                
                # Run the crew analysis
                result = FinancialCrew().crew().kickoff(inputs={'company_ticker': company_ticker})
                
                # Store results in session state
                if isinstance(result, dict):
                    st.session_state.analysis_results = result
                else:
                    st.session_state.analysis_results = {"Complete Analysis": str(result)}
                
                # Save results to file
                os.makedirs('./crew_results', exist_ok=True)
                file_path = f"./crew_results/crew_result_{company_ticker}.md"
                with open(file_path, 'w') as file:
                    file.write(str(result))
                
                # Mark analysis as complete
                st.session_state.analysis_complete = True
                
                # Add system message to chat
                system_msg = f"Analysis for {company_ticker} is complete! You can now ask questions about the results."
                st.session_state.messages.append({"role": "assistant", "content": system_msg})
                
            except Exception as e:
                st.error(f"An error occurred while running the analysis: {str(e)}")
    
    st.divider()
    
    # Display information about the agents
    with st.expander("About the AI Agents"):
        st.markdown("""
        This system uses specialized AI agents:
        
        - **Sentiment & News Analyst**: Analyzes recent news and market sentiment
        - **Fundamental Analysis Specialist**: Examines financial statements and ratios
        - **Macroeconomic Analyst**: Evaluates economic indicators and trends
        - **Chief Investment Strategist**: Synthesizes all data into recommendations
        """)

# Main chat interface
st.markdown('<p class="sub-header">Chat with your Financial Advisor</p>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask about investment recommendations...")

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        if not st.session_state.analysis_complete:
            response = "Please run the financial analysis first by clicking the 'Run Financial Analysis' button in the sidebar."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            with st.spinner("Analyzing your question..."):
                # In a real implementation, you would process the user query against the analysis results
                # Here we'll provide a basic response based on the available results
                
                # Get the key sections from the analysis results
                analysis_data = st.session_state.analysis_results
                ticker = st.session_state.current_ticker
                
                # Simple keyword matching for demo purposes
                if any(keyword in prompt.lower() for keyword in ["recommend", "buy", "sell", "invest"]):
                    if "Executive Summary" in analysis_data:
                        response = f"Based on our analysis for {ticker}:\n\n{analysis_data['Executive Summary']}"
                    else:
                        response = f"Based on our comprehensive analysis, here's my recommendation for {ticker}:\n\n"
                        response += "After reviewing the financial fundamentals, recent news sentiment, and macroeconomic factors, "
                        response += "I would suggest considering this stock as part of a diversified portfolio, especially if you have a "
                        response += f"{time_horizon.lower()} investment horizon and {risk_tolerance.lower()} risk tolerance."
                
                elif any(keyword in prompt.lower() for keyword in ["risk", "downside"]):
                    if "Risk and Opportunity" in analysis_data:
                        response = f"Here are the key risks for {ticker}:\n\n{analysis_data['Risk and Opportunity']}"
                    else:
                        response = f"When considering risks for {ticker}, you should be aware of potential market volatility, "
                        response += "sector-specific challenges, and the current macroeconomic environment."
                
                elif any(keyword in prompt.lower() for keyword in ["news", "sentiment", "articles"]):
                    if "Sentiment Analysis" in analysis_data:
                        response = f"Here's the recent news sentiment for {ticker}:\n\n{analysis_data['Sentiment Analysis']}"
                    else:
                        response = f"The recent news sentiment around {ticker} has been mixed. Some positive developments "
                        response += "include potential growth opportunities, while concerns exist around market competition."
                
                elif any(keyword in prompt.lower() for keyword in ["fundamental", "financial", "ratio"]):
                    if "Financial Highlights" in analysis_data:
                        response = f"Here's the fundamental analysis for {ticker}:\n\n{analysis_data['Financial Highlights']}"
                    elif "Fundamental Analysis" in analysis_data:
                        response = f"Here's the fundamental analysis for {ticker}:\n\n{analysis_data['Fundamental Analysis']}"
                    else:
                        response = f"The fundamental analysis for {ticker} shows its current P/E ratio, revenue growth trends, "
                        response += "and profit margins compared to industry peers."
                
                elif any(keyword in prompt.lower() for keyword in ["economy", "macro", "interest", "inflation"]):
                    if "Macroecnomic Condition" in analysis_data:
                        response = f"Here's the macroeconomic analysis for {ticker}:\n\n{analysis_data['Macroecnomic Condition']}"
                    else:
                        response = f"The macroeconomic factors that may affect {ticker} include current interest rates, "
                        response += "inflation trends, and overall economic growth projections."
                
                else:
                    # General overview response
                    response = f"Based on our analysis of {ticker}, considering your {time_horizon.lower()} investment horizon "
                    response += f"and {risk_tolerance.lower()} risk tolerance:\n\n"
                    
                    # Include a summary from available sections
                    if isinstance(analysis_data, dict) and len(analysis_data) > 0:
                        first_key = list(analysis_data.keys())[0]
                        response += f"{analysis_data[first_key][:300]}...\n\n"
                    
                    response += "You can ask specifically about recommendations, risks, news sentiment, "
                    response += "fundamental analysis, or macroeconomic factors affecting this stock."
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# Display current analysis results in an expander if available
if st.session_state.analysis_complete:
    with st.expander("View Full Analysis Report", expanded=False):
        st.markdown(f"## Analysis Report for {st.session_state.current_ticker}")
        
        if isinstance(st.session_state.analysis_results, dict):
            for section, content in st.session_state.analysis_results.items():
                st.markdown(f"### {section}")
                st.markdown(content)
        else:
            st.markdown(st.session_state.analysis_results)