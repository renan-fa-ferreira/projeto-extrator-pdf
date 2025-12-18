#!/usr/bin/env python3
"""Analisador específico para PDFs do Bradesco"""

import pdfplumber
import re

def analyze_bradesco_pdf(pdf_path):
    """Analisa estrutura específica do Bradesco"""
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"=== ANÁLISE BRADESCO: {pdf_path} ===\n")
        print(f"Total de páginas: {len(pdf.pages)}\n")
        
        for page_num, page in enumerate(pdf.pages[:3], 1):  # Primeiras 3 páginas
            print(f"--- PÁGINA {page_num} ---")
            
            text = page.extract_text()
            lines = text.split('\n')
            
            print("CABEÇALHO (primeiras 15 linhas):")
            for i, line in enumerate(lines[:15]):
                print(f"{i+1:2d}: {line}")
            
            # Procura por padrões do Bradesco
            print(f"\nPADRÕES BRADESCO:")
            
            # Agência e conta
            for line in lines[:20]:
                if 'AGÊNCIA' in line.upper() or 'CONTA' in line.upper():
                    print(f"- Conta/Agência: {line}")
                if 'BRADESCO' in line.upper():
                    print(f"- Banco: {line}")
                if 'PERÍODO' in line.upper() or 'PERIODO' in line.upper():
                    print(f"- Período: {line}")
            
            # Tabelas
            tables = page.extract_tables()
            print(f"\nTABELAS: {len(tables)}")
            
            for i, table in enumerate(tables):
                if table and len(table) > 1:
                    print(f"\nTABELA {i+1}:")
                    print(f"Header: {table[0]}")
                    
                    # Mostra algumas linhas
                    for j, row in enumerate(table[1:4]):
                        print(f"Linha {j+1}: {row}")
            
            # Padrões de data e valor
            dates = re.findall(r'\d{2}/\d{2}/\d{4}', text)
            values = re.findall(r'\d+[.,]\d{2}', text)
            
            print(f"\nDATAS: {len(dates)} (ex: {dates[:3] if dates else 'nenhuma'})")
            print(f"VALORES: {len(values)} (ex: {values[:5] if values else 'nenhum'})")
            
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    # Coloque o arquivo do Bradesco na pasta input
    import os
    input_folder = "data/input"
    
    # Procura por PDFs do Bradesco
    for file in os.listdir(input_folder):
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, file)
            print(f"Analisando: {file}")
            analyze_bradesco_pdf(pdf_path)
            break