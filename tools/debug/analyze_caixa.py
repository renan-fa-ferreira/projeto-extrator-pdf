#!/usr/bin/env python3
"""Analisador específico para PDFs da Caixa"""

import pdfplumber
import re

def analyze_caixa_pdf(pdf_path):
    """Analisa estrutura específica da Caixa"""
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"=== ANÁLISE CAIXA: {pdf_path} ===\n")
        print(f"Total de páginas: {len(pdf.pages)}\n")
        
        for page_num, page in enumerate(pdf.pages[:2], 1):
            print(f"--- PÁGINA {page_num} ---")
            
            text = page.extract_text()
            lines = text.split('\n')
            
            print("CABEÇALHO (primeiras 20 linhas):")
            for i, line in enumerate(lines[:20]):
                print(f"{i+1:2d}: {line}")
            
            # Procura por padrões da Caixa
            print(f"\nPADRÕES CAIXA:")
            
            for line in lines[:25]:
                if any(x in line.upper() for x in ['CAIXA', 'CEF', '104']):
                    print(f"- Banco: {line}")
                if any(x in line.upper() for x in ['AGÊNCIA', 'CONTA', 'OPERAÇÃO']):
                    print(f"- Conta: {line}")
                if any(x in line.upper() for x in ['PERÍODO', 'EXTRATO']):
                    print(f"- Período: {line}")
            
            # Tabelas
            tables = page.extract_tables()
            print(f"\nTABELAS: {len(tables)}")
            
            for i, table in enumerate(tables):
                if table and len(table) > 1:
                    print(f"\nTABELA {i+1}:")
                    print(f"Linhas: {len(table)}")
                    print(f"Header: {table[0]}")
                    
                    for j, row in enumerate(table[1:4]):
                        print(f"Linha {j+1}: {row}")
            
            # Padrões de transação
            dates = re.findall(r'\d{2}/\d{2}/\d{4}', text)
            values = re.findall(r'\d+[.,]\d{2}', text)
            
            print(f"\nDATAS: {len(dates)} (ex: {dates[:3] if dates else 'nenhuma'})")
            print(f"VALORES: {len(values)} (ex: {values[:5] if values else 'nenhum'})")
            
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    import os
    input_folder = "data/input"
    
    for file in os.listdir(input_folder):
        if 'caixa' in file.lower() and file.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, file)
            analyze_caixa_pdf(pdf_path)
            break
    else:
        print("Nenhum PDF da Caixa encontrado. Renomeie o arquivo para conter 'caixa' no nome.")