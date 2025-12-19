#!/usr/bin/env python3
"""Extrator individual para Banco Safra"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_safra_data(pdf_path):
    """Extrai dados do extrato do Banco Safra"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                except Exception as e:
                    continue
                

                
                # Múltiplos padrões para Safra
                patterns = [
                    # Padrão 1: Data, descrição, valor
                    r'(\d{2}/\d{2})\s+([A-Z][^0-9]+?)\s+([\d.,]+)',
                    # Padrão 2: Data, descrição, valor com sinal, saldo
                    r'(\d{2}/\d{2})\s+(.+?)\s+([+-]?[\d.,]+)\s+([\d.,]+)',
                    # Padrão 3: Data DD/MM/YYYY
                    r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)'
                ]
                
                for pattern_num, pattern in enumerate(patterns):
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        try:
                            groups = match.groups()

                            
                            if len(groups) == 4:  # Com saldo
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                saldo_str = groups[3].replace('.', '').replace(',', '.')
                                
                                tipo = 'D' if valor_str.startswith('-') else 'C'
                                valor = float(valor_str.replace('-', ''))
                                
                                transactions.append({
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': valor,
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str)
                                })
                            elif len(groups) == 3:  # Sem saldo
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                
                                # Determinar tipo baseado na descrição
                                tipo = 'D' if any(word in descricao.upper() for word in ['DEBITO', 'SAQUE', 'PAGAMENTO', 'TRANSFERENCIA']) else 'C'
                                valor = float(valor_str)
                                
                                transactions.append({
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': valor,
                                    'Tipo': tipo,
                                    'Saldo': 0.0
                                })
                            
                        except Exception as e:
                            continue
                    
                    if transactions:
                        break
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return []
    
    return transactions

def main():
    # Definir pastas
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    
    # Procurar PDFs do Safra na pasta input
    safra_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["SAFRA", "422"]):
            safra_files.append(pdf_file)
    
    if not safra_files:
        print("Nenhum PDF do Banco Safra encontrado em data/input/")
        return
    
    pdf_path = safra_files[0]
    
    print(f"Processando extrato do Banco Safra: {pdf_path.name}")
    
    transactions = extract_safra_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Ordenar por data, documento, descrição
    df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Data_Sort'] = df['Data_Sort'].fillna(pd.to_datetime(df['Data'], format='%d/%m', errors='coerce'))
    df = df.sort_values(['Data_Sort', 'Descrição'], na_position='last')
    df = df.drop('Data_Sort', axis=1)
    
    # Salvar em Excel na pasta output
    output_path = Path("data/output") / (pdf_path.stem + "_safra_extraido.xlsx")
    Path("data/output").mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    
    print(f"Dados extraídos salvos em: {output_path}")
    print(f"Total de transações: {len(transactions)}")
    print("\nPrimeiras 5 transações:")
    print(df.head().to_string(index=False))

if __name__ == "__main__":
    main()