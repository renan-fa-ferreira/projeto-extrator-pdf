#!/usr/bin/env python3
"""Debug para entender melhor os valores"""

import pdfplumber
import re

def debug_table_structure(pdf_path):
    """Analisa estrutura das tabelas para entender valores"""
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[1:4], 2):  # Páginas 2-4
            print(f"\n=== PÁGINA {page_num} ===")
            
            tables = page.extract_tables()
            for table_num, table in enumerate(tables):
                if not table:
                    continue
                
                print(f"\nTABELA {table_num + 1}:")
                
                # Encontra linha de header
                header_row = None
                for i, row in enumerate(table):
                    if any('Dt. movimento' in str(cell) for cell in row if cell):
                        header_row = i
                        print(f"Header na linha {i}: {row}")
                        break
                
                if header_row is None:
                    continue
                
                # Mostra algumas linhas de dados
                print("\nLinhas de dados:")
                for i, row in enumerate(table[header_row + 1:header_row + 6]):
                    if not row:
                        continue
                    
                    print(f"Linha {i+1}:")
                    for j, cell in enumerate(row):
                        print(f"  Col {j}: '{cell}'")
                    
                    # Analisa especificamente colunas de valor
                    if len(row) > 5:
                        valor_col = row[5]  # Coluna "Valor R$"
                        saldo_col = row[6] if len(row) > 6 else None
                        
                        print(f"  VALOR: '{valor_col}'")
                        print(f"  SALDO: '{saldo_col}'")
                        
                        # Testa regex nos valores
                        if valor_col:
                            matches = re.findall(r'([\d.,]+)\s*([CD])', str(valor_col))
                            print(f"  Matches valor: {matches}")
                        
                        if saldo_col:
                            matches = re.findall(r'([\d.,]+)\s*([CD])', str(saldo_col))
                            print(f"  Matches saldo: {matches}")
                    
                    print()

if __name__ == "__main__":
    debug_table_structure("data/input/2018_11_extrato_movimento.pdf")