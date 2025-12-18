import tabula
import pandas as pd
from datetime import datetime
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.transaction import Transaction

class TabulaExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_tables(self) -> List[pd.DataFrame]:
        try:
            tables = tabula.read_pdf(
                self.pdf_path, 
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None}
            )
            return tables
        except:
            return []
    
    def extract_transactions(self) -> List[Transaction]:
        tables = self.extract_tables()
        transactions = []
        
        for df in tables:
            if df.empty:
                continue
                
            for _, row in df.iterrows():
                try:
                    # Procura por colunas que parecem datas
                    date_col = None
                    value_col = None
                    desc_col = None
                    
                    for i, cell in enumerate(row):
                        if pd.isna(cell):
                            continue
                            
                        cell_str = str(cell)
                        
                        # Detecta data
                        if date_col is None and ('/' in cell_str or '-' in cell_str):
                            try:
                                if len(cell_str) >= 8:
                                    datetime.strptime(cell_str[:10], '%d/%m/%Y')
                                    date_col = i
                            except:
                                pass
                        
                        # Detecta valor
                        if value_col is None and (',' in cell_str or '.' in cell_str):
                            try:
                                float(cell_str.replace(',', '.').replace('+', '').replace('-', ''))
                                value_col = i
                            except:
                                pass
                    
                    if date_col is not None and value_col is not None:
                        date = datetime.strptime(str(row.iloc[date_col])[:10], '%d/%m/%Y')
                        value = float(str(row.iloc[value_col]).replace(',', '.').replace('+', ''))
                        
                        # Descrição é o que sobrar
                        desc_parts = []
                        for i, cell in enumerate(row):
                            if i != date_col and i != value_col and not pd.isna(cell):
                                desc_parts.append(str(cell))
                        
                        description = ' '.join(desc_parts)
                        
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