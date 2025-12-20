#!/usr/bin/env python3
"""Extrator individual melhorado para Banco BV (Votorantim) - captura TODAS as transações"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def concatenate_broken_lines(lines):
    """Concatena linhas quebradas de descrições"""
    concatenated = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # Se a linha tem data, pode ter descrição quebrada na próxima
        if re.search(r'\d{2}/\d{2}/\d{4}', line):
            # Verificar se próxima linha é continuação (não tem data nem valores)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if (next_line and 
                    not re.search(r'\d{2}/\d{2}/\d{4}', next_line) and
                    not re.search(r'[\d.,]+$', next_line) and
                    not next_line.startswith('Página')):
                    # Concatenar as linhas
                    line = line + " " + next_line
                    i += 1  # Pular próxima linha
        
        concatenated.append(line)
        i += 1
    
    return concatenated

def extract_bv_data(pdf_path):
    """Extrai dados do extrato do Banco BV"""
    transactions = []
    metadata = {
        'banco': 'Banco BV',
        'codigo_banco': '655',
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
                    conta_match = re.search(r'Conta:\s*([\d.-]+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    
                    periodo_match = re.search(r'Período:\s*(\d{2}/\d{2}/\d{4})\s+à\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            # Processar todas as páginas
            current_date = None
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                # Concatenar linhas quebradas
                lines = concatenate_broken_lines(lines)
                print(f"Página {page_num + 1}: {len(lines)} linhas")
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('Página') or line.startswith('Extrato'):
                        continue
                    
                    # Padrão 1: Data + "Saldo do dia" + Valor
                    saldo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+Saldo do dia\s+([\d.,]+)', line)
                    if saldo_match:
                        current_date = saldo_match.group(1)
                        valor_str = saldo_match.group(2).replace('.', '').replace(',', '.')
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': current_date,
                            'Documento': '',
                            'Descrição': 'Saldo do dia',
                            'Valor': float(valor_str),
                            'Tipo': 'C',
                            'Saldo': float(valor_str)
                        })
                        continue
                    
                    # Padrão 2: Apenas detectar nova data
                    date_only = re.search(r'^(\d{2}/\d{2}/\d{4})', line)
                    if date_only:
                        current_date = date_only.group(1)
                        continue
                    
                    # Padrão 3: Transações sem data (usam data atual)
                    if current_date:
                        # DESCRIÇÃO DOCUMENTO VALOR (com sinal)
                        transaction_match = re.search(r'^(.+?)\s+(\d+)\s+([+-]?\s*[\d.,]+)$', line)
                        if transaction_match:
                            descricao = transaction_match.group(1).strip()
                            documento = transaction_match.group(2)
                            valor_str = transaction_match.group(3).replace(' ', '').replace('.', '').replace(',', '.')
                            
                            tipo = 'D' if valor_str.startswith('-') else 'C'
                            valor = float(valor_str.replace('-', ''))
                            
                            transactions.append({
                                'Banco': metadata['banco'],
                                'Código Banco': metadata['codigo_banco'],
                                'Agência': metadata['agencia'],
                                'Conta': metadata['conta'],
                                'Data': current_date,
                                'Documento': documento,
                                'Descrição': descricao,
                                'Valor': valor,
                                'Tipo': tipo,
                                'Saldo': 0.0
                            })
                        
                        # DESCRIÇÃO VALOR (sem documento)
                        else:
                            simple_match = re.search(r'^(.+?)\s+([+-]?\s*[\d.,]+)$', line)
                            if simple_match and not line.isdigit():
                                descricao = simple_match.group(1).strip()
                                valor_str = simple_match.group(2).replace(' ', '').replace('.', '').replace(',', '.')
                                
                                tipo = 'D' if valor_str.startswith('-') else 'C'
                                valor = float(valor_str.replace('-', ''))
                                
                                if len(descricao) > 5 and 'Página' not in descricao:
                                    transactions.append({
                                        'Banco': metadata['banco'],
                                        'Código Banco': metadata['codigo_banco'],
                                        'Agência': metadata['agencia'],
                                        'Conta': metadata['conta'],
                                        'Data': current_date,
                                        'Documento': '',
                                        'Descrição': descricao,
                                        'Valor': valor,
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
    
    bv_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["BV", "VOTORANTIM", "655"]):
            bv_files.append(pdf_file)
    
    if not bv_files:
        print("Nenhum PDF do Banco BV encontrado em data/input/")
        return
    
    pdf_path = bv_files[0]
    print(f"Processando extrato do Banco BV: {pdf_path.name}")
    
    transactions, metadata = extract_bv_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    df = pd.DataFrame(transactions)
    
    # Ordenar por data, documento, descrição
    df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df = df.sort_values(['Data_Sort', 'Documento', 'Descrição'], na_position='last')
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
    
    output_path = output_dir / (pdf_path.stem + "_bv_extraido.xlsx")
    try:
        df.to_excel(output_path, index=False)
        print(f"\nDados extraídos salvos em: {output_path}")
    except PermissionError:
        print(f"\nAviso: Não foi possível salvar o arquivo (pode estar aberto no Excel)")

if __name__ == "__main__":
    main()