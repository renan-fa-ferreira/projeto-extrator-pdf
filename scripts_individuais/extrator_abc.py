#!/usr/bin/env python3
"""Extrator individual para Banco ABC Brasil"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_abc_data(pdf_path):
    """Extrai dados do extrato do Banco ABC Brasil"""
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                # Padrão para transações do ABC Brasil
                pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)\s+([DC])\s+([\d.,]+)'
                
                for match in re.finditer(pattern, text):
                    data = match.group(1)
                    descricao = match.group(2).strip()
                    valor_str = match.group(3).replace('.', '').replace(',', '.')
                    tipo = match.group(4)
                    saldo = match.group(5).replace('.', '').replace(',', '.')
                    
                    valor = float(valor_str)
                    
                    transactions.append({
                        'Data': data,
                        'Descrição': descricao,
                        'Valor': valor,
                        'Tipo': tipo,
                        'Saldo': float(saldo)
                    })
                
                # Padrão alternativo
                alt_pattern = r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)'
                
                for match in re.finditer(alt_pattern, text):
                    data = match.group(1)
                    descricao = match.group(2).strip()
                    valor_str = match.group(3).replace('.', '').replace(',', '.')
                    
                    tipo = 'D' if any(word in descricao.upper() for word in ['DEBITO', 'SAQUE', 'PAGAMENTO']) else 'C'
                    valor = float(valor_str)
                    
                    transactions.append({
                        'Data': data,
                        'Descrição': descricao,
                        'Valor': valor,
                        'Tipo': tipo
                    })
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return []
    
    return transactions

def main():
    # Definir pastas
    input_dir = Path("data/input")
    
    # Procurar PDFs do ABC na pasta input
    abc_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["ABC", "246"]):
            abc_files.append(pdf_file)
    
    if not abc_files:
        print("Nenhum PDF do Banco ABC encontrado em data/input/")
        return
    
    pdf_path = abc_files[0]
    
    print(f"Processando extrato do Banco ABC Brasil: {pdf_path.name}")
    
    transactions = extract_abc_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Salvar em Excel na pasta output
    output_path = Path("data/input/output") / (pdf_path.stem + "_abc_extraido.xlsx")
    Path("data/input/output").mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    
    print(f"Dados extraídos salvos em: {output_path}")
    print(f"Total de transações: {len(transactions)}")
    print("\nPrimeiras 5 transações:")
    print(df.head().to_string(index=False))

if __name__ == "__main__":
    main()