import pdfplumber
import pandas as pd
import re
from datetime import datetime
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.transaction import Transaction

class PDFPlumberExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_text(self) -> str:
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    
    def extract_transactions(self) -> List[Transaction]:
        text = self.extract_text()
        transactions = []
        
        # Padrão para linhas de transação: data valor descrição
        pattern = r'(\d{2}/\d{2}/\d{4})\s+([+-]?\d+[.,]\d{2})\s+(.+?)(?=\d{2}/\d{2}/\d{4}|$)'
        
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            try:
                date = datetime.strptime(match[0], '%d/%m/%Y')
                value = float(match[1].replace(',', '.').replace('+', ''))
                description = match[2].strip()
                
                transaction = Transaction(
                    date=date,
                    description=description,
                    value=value,
                    type='credit' if value > 0 else 'debit'
                )
                transactions.append(transaction)
            except:
                continue
                
        return transactions
    
    def to_dataframe(self) -> pd.DataFrame:
        transactions = self.extract_transactions()
        return pd.DataFrame([t.to_dict() for t in transactions])