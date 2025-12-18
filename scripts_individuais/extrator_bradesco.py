#!/usr/bin/env python3
"""Extrator individual para Bradesco"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_bradesco_data(pdf_path):
    """Extrai dados do extrato do Bradesco"""
    transactions = []
    metadata = {
        'banco': 'Banco Bradesco S/A',
        'codigo_banco': '237',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    # Extrair agência e conta
                    agencia_conta_match = re.search(r'Ag:\s*(\d+)\s*\|\s*CC:\s*(\d+-\d+)', first_page_text)
                    if agencia_conta_match:
                        metadata['agencia'] = agencia_conta_match.group(1)
                        metadata['conta'] = agencia_conta_match.group(2)
                    
                    # Extrair período
                    periodo_match = re.search(r'Entre\s+(\d{2}/\d{2}/\d{4})\s+e\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                

                
                # Múltiplos padrões para Bradesco baseados no formato real
                patterns = [
                    # Padrão 1: Data, documento, valor com sinal, saldo
                    r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+([+-]?[\d.,]+)\s+([\d.,]+)',
                    # Padrão 2: Data, descrição, valor, saldo
                    r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([+-]?[\d.,]+)\s+([\d.,]+)',
                    # Padrão 3: Formato mais simples
                    r'(\d{2}/\d{2}/\d{4})\s+SALDO ANTERIOR\s+([\d.,]+)'
                ]
                
                for pattern_num, pattern in enumerate(patterns):
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        try:
                            groups = match.groups()

                            
                            if len(groups) == 4:  # Padrão com documento/descrição
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                saldo_str = groups[3].replace('.', '').replace(',', '.')
                                
                                # Determinar tipo baseado no sinal
                                if valor_str.startswith('-'):
                                    tipo = 'D'
                                    valor = float(valor_str.replace('-', ''))
                                else:
                                    tipo = 'C'
                                    valor = float(valor_str)
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Código Banco': metadata['codigo_banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': valor,
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str)
                                })
                            elif len(groups) == 2:  # Saldo anterior
                                data = groups[0]
                                saldo_str = groups[1].replace('.', '').replace(',', '.')
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Código Banco': metadata['codigo_banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Descrição': 'SALDO ANTERIOR',
                                    'Valor': 0.0,
                                    'Tipo': 'C',
                                    'Saldo': float(saldo_str)
                                })
                            
                        except Exception as e:
                            continue
                    
                    if transactions:
                        break
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    return transactions, metadata

def main():
    # Definir pastas
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar PDFs do Bradesco na pasta input
    bradesco_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["BRADESCO", "237"]):
            bradesco_files.append(pdf_file)
    
    if not bradesco_files:
        print("Nenhum PDF do Bradesco encontrado em data/input/")
        return
    
    pdf_path = bradesco_files[0]
    
    print(f"Processando extrato do Bradesco: {pdf_path.name}")
    
    transactions, metadata = extract_bradesco_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Salvar em Excel na pasta output
    output_path = output_dir / (pdf_path.stem + "_bradesco_extraido.xlsx")
    df.to_excel(output_path, index=False)
    
    print(f"Metadados extraídos:")
    print(f"  Banco: {metadata['banco']}")
    print(f"  Código: {metadata['codigo_banco']}")
    print(f"  Agência: {metadata['agencia']}")
    print(f"  Conta: {metadata['conta']}")
    print(f"  Período: {metadata['periodo']}")
    print(f"Dados extraídos salvos em: {output_path}")
    print(f"Total de transações: {len(transactions)}")
    print("\nPrimeiras 5 transações:")
    print(df.head().to_string(index=False))

if __name__ == "__main__":
    main()