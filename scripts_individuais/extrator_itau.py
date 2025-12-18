#!/usr/bin/env python3
"""Extrator individual para Itaú"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_itau_data(pdf_path):
    """Extrai dados do extrato do Itaú"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                

                
                # Múltiplos padrões para Itaú baseados no formato real
                patterns = [
                    # Padrão 1: Data DD/MM, descrição, documento, valor com sinal
                    r'(\d{2}/\d{2})\s+(.+?)\s+(\d+)\s+([\d.,]+)([+-])',
                    # Padrão 2: Data DD/MM, descrição, valor com sinal
                    r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)([+-])',
                    # Padrão 3: Formato sem sinal (saldo anterior, etc)
                    r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)'
                ]
                
                for pattern_num, pattern in enumerate(patterns):
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        try:
                            groups = match.groups()

                            
                            if len(groups) == 5:  # Com documento e sinal
                                data = groups[0]
                                descricao = groups[1].strip()
                                documento = groups[2]
                                valor_str = groups[3].replace('.', '').replace(',', '.')
                                sinal = groups[4]
                                tipo = 'D' if sinal == '-' else 'C'
                                
                                transactions.append({
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Documento': documento,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': 0.0
                                })
                            elif len(groups) == 4:  # Com sinal
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                sinal = groups[3]
                                tipo = 'D' if sinal == '-' else 'C'
                                
                                transactions.append({
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Documento': '',
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': 0.0
                                })
                            elif len(groups) == 3:  # Sem sinal (saldo, etc)
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                tipo = 'C' if 'SALDO' in descricao.upper() else 'D'
                                
                                transactions.append({
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Documento': '',
                                    'Valor': float(valor_str),
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
    input_dir = Path("data/input")
    
    # Procurar PDFs do Itaú na pasta input
    itau_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["ITAU", "ITAÚ", "341"]):
            itau_files.append(pdf_file)
    
    if not itau_files:
        print("Nenhum PDF do Itaú encontrado em data/input/")
        return
    
    pdf_path = itau_files[0]
    
    print(f"Processando extrato do Itaú: {pdf_path.name}")
    
    transactions = extract_itau_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Salvar em Excel na pasta output
    output_path = Path("data/input/output") / (pdf_path.stem + "_itau_extraido.xlsx")
    Path("data/input/output").mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    
    print(f"Dados extraídos salvos em: {output_path}")
    print(f"Total de transações: {len(transactions)}")
    print("\nPrimeiras 5 transações:")
    print(df.head().to_string(index=False))

if __name__ == "__main__":
    main()