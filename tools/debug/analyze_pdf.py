#!/usr/bin/env python3
"""Script para analisar estrutura do PDF"""

import pdfplumber
import pandas as pd

def analyze_pdf_structure(pdf_path):
    """Analisa a estrutura do PDF para entender layout"""
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"=== ANÁLISE DO PDF: {pdf_path} ===\n")
        print(f"Total de páginas: {len(pdf.pages)}\n")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"--- PÁGINA {page_num} ---")
            
            # Extrai texto completo
            text = page.extract_text()
            lines = text.split('\n')
            
            print("CABEÇALHO (primeiras 10 linhas):")
            for i, line in enumerate(lines[:10]):
                print(f"{i+1:2d}: {line}")
            
            print(f"\nTOTAL DE LINHAS: {len(lines)}")
            
            # Procura por tabelas
            tables = page.extract_tables()
            print(f"TABELAS ENCONTRADAS: {len(tables)}")
            
            if tables:
                for i, table in enumerate(tables):
                    print(f"\nTABELA {i+1}:")
                    print(f"Linhas: {len(table)}, Colunas: {len(table[0]) if table else 0}")
                    
                    # Mostra header
                    if table:
                        print("Header:", table[0])
                        
                        # Mostra algumas linhas de exemplo
                        print("Exemplos de linhas:")
                        for j, row in enumerate(table[1:6]):  # 5 primeiras linhas
                            print(f"  {j+1}: {row}")
            
            # Procura por padrões específicos
            print(f"\nPADRÕES ENCONTRADOS:")
            
            # Procura por datas
            import re
            date_pattern = r'\d{2}/\d{2}/\d{4}'
            dates = re.findall(date_pattern, text)
            print(f"- Datas encontradas: {len(dates)} (ex: {dates[:3] if dates else 'nenhuma'})")
            
            # Procura por valores monetários
            money_patterns = [
                r'\d+[.,]\d{2}',  # formato básico
                r'R\$\s*\d+[.,]\d{2}',  # com R$
                r'\d{1,3}(?:[.,]\d{3})*[.,]\d{2}'  # com separadores de milhares
            ]
            
            for pattern in money_patterns:
                values = re.findall(pattern, text)
                print(f"- Valores ({pattern}): {len(values)} (ex: {values[:3] if values else 'nenhum'})")
            
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    pdf_file = "data/input/2018_11_extrato_movimento.pdf"
    analyze_pdf_structure(pdf_file)