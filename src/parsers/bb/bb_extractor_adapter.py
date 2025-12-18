#!/usr/bin/env python3
"""Adapter para extractor do BB"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from pathlib import Path
from parsers.base_extractor import BaseExtractor

# Importa função do extractor existente
with open('src/parsers/bb/bb_folder_extractor.py', 'r', encoding='utf-8') as f:
    exec(f.read())

class BBExtractorAdapter(BaseExtractor):
    """Adapter para integrar extractor do BB com interface padrão"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extrai dados usando extractor específico do BB"""
        
        # Usa função existente
        df, contas_info = extract_bb_statement(self.pdf_path)
        
        # Padroniza formato
        if not df.empty:
            # Renomeia colunas para padrão
            column_mapping = {
                'data_movimento': 'data_movimento',
                'historico': 'historico', 
                'documento': 'documento',
                'valor': 'valor',
                'saldo': 'saldo',
                'tipo': 'tipo',
                'conta': 'conta',
                'agencia': 'agencia',
                'banco': 'banco'
            }
            
            df = df.rename(columns=column_mapping)
            df['arquivo'] = Path(self.pdf_path).name
            
            # Padroniza saída
            df = self.standardize_output(df, contas_info)
        
        return df, contas_info