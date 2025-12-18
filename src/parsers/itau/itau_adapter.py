#!/usr/bin/env python3
"""Adapter para extractor do Itaú"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from pathlib import Path
from parsers.base_extractor import BaseExtractor

# Importa função do extractor existente
with open('src/parsers/itau/itau_extractor.py', 'r', encoding='utf-8') as f:
    exec(f.read())

class ItauAdapter(BaseExtractor):
    """Adapter para integrar extractor do Itaú com interface padrão"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extrai dados usando extractor específico do Itaú"""
        
        # Usa função existente
        df, header_info = extract_itau_statement(self.pdf_path)
        
        # Padroniza formato
        if not df.empty:
            df['arquivo'] = Path(self.pdf_path).name
            
            # Padroniza saída
            df = self.standardize_output(df, header_info)
        
        return df, header_info