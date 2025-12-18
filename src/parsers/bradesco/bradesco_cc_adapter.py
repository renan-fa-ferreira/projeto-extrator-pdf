#!/usr/bin/env python3
"""Adapter para extractor conta corrente Bradesco"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from pathlib import Path
from parsers.base_extractor import BaseExtractor

# Importa função do extractor existente
with open('src/parsers/bradesco/bradesco_conta_corrente.py', 'r', encoding='utf-8') as f:
    exec(f.read())

class BradescoCCAdapter(BaseExtractor):
    """Adapter para integrar extractor conta corrente Bradesco"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extrai dados usando extractor específico do Bradesco"""
        
        # Usa função existente
        df, header_info = extract_bradesco_conta_corrente(self.pdf_path)
        
        # Padroniza formato
        if not df.empty:
            # Combina crédito e débito em valor único
            df['valor'] = df['credito'] - df['debito']
            
            # Remove colunas específicas
            df = df.drop(['credito', 'debito'], axis=1, errors='ignore')
            
            # Padroniza saída
            df = self.standardize_output(df, header_info)
        
        return df, header_info