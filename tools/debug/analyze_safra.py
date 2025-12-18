#!/usr/bin/env python3
"""Analisador específico para PDFs do Safra"""

import pdfplumber
import re

def analyze_safra_pdf(pdf_path):
    """Analisa estrutura específica do Safra"""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"=== ANÁLISE SAFRA: {pdf_path} ===\n")
            print(f"Total de páginas: {len(pdf.pages)}\n")
            
            for page_num, page in enumerate(pdf.pages[:2], 1):
                print(f"--- PÁGINA {page_num} ---")
                
                text = page.extract_text()
                if not text:
                    print("Página sem texto extraível")
                    continue
                    
                lines = text.split('\n')
                
                print("CABEÇALHO (primeiras 15 linhas):")
                for i, line in enumerate(lines[:15]):
                    print(f"{i+1:2d}: {line}")
                
                # Procura por padrões do Safra
                print(f"\nPADRÕES SAFRA:")
                
                for line in lines[:20]:
                    if any(x in line.upper() for x in ['SAFRA', 'J.SAFRA', 'J SAFRA']):
                        print(f"- Banco: {line}")
                    if any(x in line.upper() for x in ['EXTRATO', 'APLICACAO', 'INVESTIMENTO']):
                        print(f"- Tipo: {line}")
                    if any(x in line.upper() for x in ['CONTA', 'AGÊNCIA']):
                        print(f"- Conta: {line}")
                
                # Tabelas
                tables = page.extract_tables()
                print(f"\nTABELAS: {len(tables)}")
                
                for i, table in enumerate(tables):
                    if table and len(table) > 1:
                        print(f"\nTABELA {i+1}:")
                        print(f"Header: {table[0]}")
                        
                        for j, row in enumerate(table[1:4]):
                            print(f"Linha {j+1}: {row}")
                
                # Padrões de data e valor
                dates = re.findall(r'\d{2}/\d{2}/\d{4}', text)
                values = re.findall(r'\d+[.,]\d{2}', text)
                
                print(f"\nDATAS: {len(dates)} (ex: {dates[:3] if dates else 'nenhuma'})")
                print(f"VALORES: {len(values)} (ex: {values[:5] if values else 'nenhum'})")
                
                print("\n" + "="*50 + "\n")
                
    except Exception as e:
        print(f"Erro ao analisar PDF: {e}")

if __name__ == "__main__":
    import os
    input_folder = "data/input"
    
    for file in os.listdir(input_folder):
        if 'safra' in file.lower() and file.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, file)
            analyze_safra_pdf(pdf_path)
            break
    else:
        print("Nenhum PDF do Safra encontrado.")