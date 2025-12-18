import fitz  # PyMuPDF
import pandas as pd
import re
from datetime import datetime
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.transaction import Transaction

class PyMuPDFExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_text(self) -> str:
        doc = fitz.open(self.pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text
    
    def extract_tables(self) -> List[List]:
        doc = fitz.open(self.pdf_path)
        tables = []
        
        for page in doc:
            tabs = page.find_tables()
            for tab in tabs:
                table_data = tab.extract()
                tables.append(table_data)
        
        doc.close()
        return tables
    
    def extract_transactions(self) -> List[Transaction]:
        text = self.extract_text()
        transactions = []
        
        # Múltiplos padrões para diferentes formatos
        patterns = [
            r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([+-]?\d+[.,]\d{2})',
            r'(\d{2}/\d{2})\s+(.+?)\s+([+-]?\d+[.,]\d{2})',
            r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([+-]?\d+[.,]\d{2})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            
            for match in matches:
                try:
                    date_str = match[0]
                    if len(date_str) == 5:  # DD/MM format
                        date_str = f"{date_str}/2024"
                    
                    date = datetime.strptime(date_str.replace('-', '/'), '%d/%m/%Y')
                    description = match[1].strip()
                    value = float(match[2].replace(',', '.').replace('+', ''))
                    
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