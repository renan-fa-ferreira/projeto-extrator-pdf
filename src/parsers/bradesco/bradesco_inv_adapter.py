#!/usr/bin/env python3
"""Adapter para extractor investimentos Bradesco"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from pathlib import Path
from parsers.base_extractor import BaseExtractor

# Importa função do extractor existente
with open('src/parsers/bradesco/bradesco_investimentos_extractor.py', 'r', encoding='utf-8') as f:
    exec(f.read())

class BradescoInvAdapter(BaseExtractor):
    """Adapter para integrar extractor investimentos Bradesco"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extrai dados usando extractor específico do Bradesco investimentos"""
        
        # Usa função existente
        df, header_info = extract_bradesco_investments(self.pdf_path)
        
        # Padroniza formato
        if not df.empty:
            # Filtra apenas movimentações (não resumos)
            df = df[df.get('tipo', '') != 'resumo_investimento']
            
            # Renomeia colunas
            column_mapping = {
                'data': 'data_movimento',
                'historico': 'historico',
                'valor_liquido': 'valor',
                'cliente': 'conta'
            }
            
            df = df.rename(columns=column_mapping)
            df['banco'] = 'BRADESCO INVESTIMENTOS'
            
            # Padroniza saída
            df = self.standardize_output(df, header_info)
        
        return df, header_info