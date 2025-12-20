#!/usr/bin/env python3
"""Extrator individual melhorado para Banco Daycoval - captura TODAS as transações"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_daycoval_data(pdf_path):
    """Extrai dados do extrato do Banco Daycoval"""
    transactions = []
    metadata = {
        'banco': 'Banco Daycoval',
        'codigo_banco': '707',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processando {len(pdf.pages)} páginas...")
            
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    agencia_match = re.search(r'Agência[:\s]*(\d+[-]?\d*)', first_page_text)
                    if agencia_match:
                        metadata['agencia'] = agencia_match.group(1)
                    
                    conta_match = re.search(r'Conta[:\s]*(\d+[-]?\d*)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    
                    periodo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+[ae]\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            # Processar todas as páginas
            current_date = None
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                print(f"Página {page_num + 1}: {len(lines)} linhas")
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Padrão 1: Data completa DD/MM/YYYY
                    date_full_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)\s+([DC])', line)
                    if date_full_match:
                        current_date = date_full_match.group(1)
                        descricao = date_full_match.group(2).strip()
                        valor_str = date_full_match.group(3).replace('.', '').replace(',', '.')
                        tipo = date_full_match.group(4)
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': current_date,
                            'Documento': '',
                            'Descrição': descricao,
                            'Valor': float(valor_str),
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Padrão 2: Data curta DD/MM
                    date_short_match = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)', line)
                    if date_short_match:
                        current_date = date_short_match.group(1)
                        descricao = date_short_match.group(2).strip()
                        valor_str = date_short_match.group(3).replace('.', '').replace(',', '.')
                        
                        # Determinar tipo baseado na descrição
                        tipo = 'D' if any(word in descricao.upper() for word in ['DEBITO', 'SAQUE', 'PAGAMENTO', 'TARIFA']) else 'C'
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': current_date,
                            'Documento': '',
                            'Descrição': descricao,
                            'Valor': float(valor_str),
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Padrão 3: Apenas detectar nova data
                    date_only = re.search(r'^(\d{2}/\d{2}/\d{4})$', line)
                    if date_only:
                        current_date = date_only.group(1)
                        continue
                    
                    date_only_short = re.search(r'^(\d{2}/\d{2})$', line)
                    if date_only_short:
                        current_date = date_only_short.group(1)
                        continue
                    
                    # Padrão 4: Transações sem data (usam data atual)
                    if current_date:
                        # DESCRIÇÃO VALOR TIPO
                        no_date_match = re.search(r'^(.+?)\s+([\d.,]+)\s+([DC])$', line)
                        if no_date_match:
                            descricao = no_date_match.group(1).strip()
                            valor_str = no_date_match.group(2).replace('.', '').replace(',', '.')
                            tipo = no_date_match.group(3)
                            
                            if len(descricao) > 3 and not descricao.upper().startswith('DATA'):
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Código Banco': metadata['codigo_banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': current_date,
                                    'Documento': '',
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': 0.0
                                })
                        
                        # DESCRIÇÃO VALOR (sem tipo)
                        else:
                            simple_match = re.search(r'^(.+?)\s+([\d.,]+)$', line)
                            if simple_match and not line.isdigit():
                                descricao = simple_match.group(1).strip()
                                valor_str = simple_match.group(2).replace('.', '').replace(',', '.')
                                
                                # Determinar tipo baseado na descrição
                                tipo = 'D' if any(word in descricao.upper() for word in ['DEBITO', 'SAQUE', 'PAGAMENTO', 'TARIFA']) else 'C'
                                
                                if len(descricao) > 3 and not descricao.upper().startswith('DATA'):
                                    transactions.append({
                                        'Banco': metadata['banco'],
                                        'Código Banco': metadata['codigo_banco'],
                                        'Agência': metadata['agencia'],
                                        'Conta': metadata['conta'],
                                        'Data': current_date,
                                        'Documento': '',
                                        'Descrição': descricao,
                                        'Valor': float(valor_str),
                                        'Tipo': tipo,
                                        'Saldo': 0.0
                                    })
            
            print(f"Total de transações encontradas: {len(transactions)}")
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    return transactions, metadata

def main():
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    daycoval_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["DAYCOVAL", "707"]):
            daycoval_files.append(pdf_file)
    
    if not daycoval_files:
        print("Nenhum PDF do Banco Daycoval encontrado em data/input/")
        return
    
    pdf_path = daycoval_files[0]
    print(f"Processando extrato do Banco Daycoval: {pdf_path.name}")
    
    transactions, metadata = extract_daycoval_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    df = pd.DataFrame(transactions)
    
    # Ordenar por data, documento, descrição
    df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Data_Sort'] = df['Data_Sort'].fillna(pd.to_datetime(df['Data'], format='%d/%m', errors='coerce'))
    df = df.sort_values(['Data_Sort', 'Descrição'], na_position='last')
    df = df.drop('Data_Sort', axis=1)
    
    print(f"Metadados extraídos:")
    print(f"  Banco: {metadata['banco']}")
    print(f"  Código: {metadata['codigo_banco']}")
    print(f"  Agência: {metadata['agencia']}")
    print(f"  Conta: {metadata['conta']}")
    print(f"  Período: {metadata['periodo']}")
    print(f"Total de transações: {len(transactions)}")
    print("\nPrimeiras 5 transações:")
    print(df.head().to_string(index=False))
    
    output_path = output_dir / (pdf_path.stem + "_daycoval_extraido.xlsx")
    try:
        df.to_excel(output_path, index=False)
        print(f"\nDados extraídos salvos em: {output_path}")
    except PermissionError:
        print(f"\nAviso: Não foi possível salvar o arquivo (pode estar aberto no Excel)")

if __name__ == "__main__":
    main()