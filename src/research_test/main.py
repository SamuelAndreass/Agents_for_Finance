#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime
from crew import FinancialCrew
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    try:
        company_ticker = 'BBRI.JK'
        result = FinancialCrew().crew().kickoff(inputs={'company_ticker': company_ticker})
        if isinstance(result, dict):
            markdown = f"# Hasil Analisis {company_ticker}\n"
            for key, value in result.items():
                markdown += f"## {key}\n{value}\n\n"
        else:
            markdown = str(result)
        os.makedirs('./crew_results', exist_ok=True)
        file_path = f"./crew_results/crew_result_{company_ticker}.md"
        result_str = str(result)
        with open(file_path, 'w') as file:
            file.write(result_str)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()