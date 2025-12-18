#!/usr/bin/env python3
"""Extrator individual para Caixa Econômica Federal"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_caixa_data(pdf_path):
    """Extrai dados do extrato da Caixa"""
    transactions = []
    metadata = {
        'banco': 'Caixa Econômica Federal',
        'codigo_banco': '104',
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
                    # Extrair conta
                    conta_match = re.search(r'Conta Referência:\s*(\d+/\d+/\d+-\d+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    
                    # Extrair período
                    periodo_match = re.search(r'Período:\s*de:\s*(\d{2}/\d{2}/\d{4})\s*até:\s*(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                

                
                # Múltiplos padrões para Caixa baseados no formato real
                patterns = [
                    # Padrão 1: Data, documento, descrição, valor+D/C, saldo+D/C
                    r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+([\d.,]+)([DC])\s+([\d.,]+)([DC])',
                    # Padrão 2: Data, descrição, valor+D/C, saldo+D/C
                    r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)([DC])\s+([\d.,]+)([DC])',
                    # Padrão 3: Formato mais simples
                    r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)([DC])'
                ]
                
                for pattern_num, pattern in enumerate(patterns):
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        try:
                            groups = match.groups()

                            
                            if len(groups) == 7:  # Padrão completo com documento
                                data = groups[0]
                                documento = groups[1]
                                descricao = groups[2].strip()
                                valor_str = groups[3].replace('.', '').replace(',', '.')
                                tipo = groups[4]
                                saldo_str = groups[5].replace('.', '').replace(',', '.')
                                saldo_tipo = groups[6]
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Código Banco': metadata['codigo_banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Documento': documento,
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str)
                                })
                            elif len(groups) == 6:  # Sem documento
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                tipo = groups[3]
                                saldo_str = groups[4].replace('.', '').replace(',', '.')
                                saldo_tipo = groups[5]
                                
                                transactions.append({
                                    'Data': data,
                                    'Documento': '',
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str)
                                })
                            elif len(groups) == 4:  # Formato simples
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                tipo = groups[3]
                                
                                transactions.append({
                                    'Data': data,
                                    'Documento': '',
                                    'Descrição': descricao,
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
        return [], metadata
    
    return transactions, metadata

def main():
    # Definir pastas
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar PDFs da Caixa na pasta input
    caixa_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["CAIXA", "CEF", "104"]):
            caixa_files.append(pdf_file)
    
    if not caixa_files:
        print("Nenhum PDF da Caixa encontrado em data/input/")
        return
    
    pdf_path = caixa_files[0]
    
    print(f"Processando extrato da Caixa: {pdf_path.name}")
    
    transactions, metadata = extract_caixa_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Salvar em Excel na pasta output
    output_path = output_dir / (pdf_path.stem + "_caixa_extraido.xlsx")
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