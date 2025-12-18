#!/usr/bin/env python3
"""Adapter para extractor da Caixa"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from pathlib import Path
from parsers.base_extractor import BaseExtractor

# Importa função do extractor existente
with open('src/parsers/caixa/caixa_govconta_extractor.py', 'r', encoding='utf-8') as f:
    exec(f.read())

class CaixaAdapter(BaseExtractor):
    """Adapter para integrar extractor da Caixa com interface padrão"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extrai dados usando extractor específico da Caixa"""
        
        # Usa função existente
        df, header_info = extract_caixa_govconta(self.pdf_path)
        
        # Padroniza formato
        if not df.empty:
            df['arquivo'] = Path(self.pdf_path).name
            
            # Padroniza saída
            df = self.standardize_output(df, header_info)
        
        return df, header_info