#!/usr/bin/env python3
"""Extractor genérico para bancos não identificados"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from parsers.base_extractor import BaseExtractor

class GenericExtractor(BaseExtractor):
    """Extractor genérico usando pdfplumber"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extração genérica baseada em padrões comuns"""
        
        transactions = []
        header_info = {'banco': 'GENÉRICO'}
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    
                    # Extrai transações por regex
                    lines = text.split('\n')
                    
                    for line in lines:
                        # Procura padrão: data + texto + valor
                        match = re.search(r'(\d{2}/\d{2}/\d{4}).*?([\d.,]+)', line)
                        
                        if match:
                            try:
                                date_str = match.group(1)
                                value_str = match.group(2).replace(',', '.')
                                
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                                value = float(value_str)
                                
                                # Descrição é o texto entre data e valor
                                desc = line.replace(date_str, '').replace(match.group(2), '').strip()
                                
                                transaction = {
                                    'arquivo': Path(self.pdf_path).name,
                                    'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                    'historico': desc,
                                    'documento': '',
                                    'valor': value,
                                    'saldo': None,
                                    'tipo': 'credit' if value > 0 else 'debit',
                                    'conta': '',
                                    'agencia': '',
                                    'banco': 'GENÉRICO'
                                }
                                
                                transactions.append(transaction)
                                
                            except:
                                continue
            
            df = pd.DataFrame(transactions)
            df = self.standardize_output(df, header_info)
            
            return df, header_info
            
        except Exception as e:
            print(f"Erro na extração genérica: {e}")
            return pd.DataFrame(), header_info