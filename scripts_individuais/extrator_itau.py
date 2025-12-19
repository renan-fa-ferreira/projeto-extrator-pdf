#!/usr/bin/env python3
"""Extrator individual melhorado para Itaú - formato correto"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_itau_data(pdf_path):
    """Extrai dados do extrato do Itaú"""
    transactions = []
    metadata = {
        'banco': 'Banco Itaú',
        'codigo_banco': '341',
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
                    agencia_conta_match = re.search(r'Agência/Conta:\s*(\d+)/(\d+-\d+)', first_page_text)
                    if agencia_conta_match:
                        metadata['agencia'] = agencia_conta_match.group(1)
                        metadata['conta'] = agencia_conta_match.group(2)
                    
                    periodo_match = re.search(r'Extrato de\s+(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            # Processar todas as páginas
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                print(f"Página {page_num + 1}: {len(lines)} linhas")
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('Data') or line.startswith('Itaú'):
                        continue
                    
                    # Padrão Itaú: DD/MM DESCRIÇÃO AGENCIA.CONTA-DIGITO VALOR
                    itau_match = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d{4}\.\d{5}-\d)\s+([+-]?[\d.,]+)$', line)
                    if itau_match:
                        data = itau_match.group(1)
                        descricao = itau_match.group(2).strip()
                        agencia_origem = itau_match.group(3)
                        valor_str = itau_match.group(4).replace('.', '').replace(',', '.')
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': agencia_origem,
                            'Descrição': descricao,
                            'Valor': valor,
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Padrão: DD/MM DESCRIÇÃO DOCUMENTO VALOR
                    itau_doc_match = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d+)\s+([+-]?[\d.,]+)$', line)
                    if itau_doc_match:
                        data = itau_doc_match.group(1)
                        descricao = itau_doc_match.group(2).strip()
                        documento = itau_doc_match.group(3)
                        valor_str = itau_doc_match.group(4).replace('.', '').replace(',', '.')
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': documento,
                            'Descrição': descricao,
                            'Valor': valor,
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Padrão: DD/MM DESCRIÇÃO VALOR
                    itau_simple_match = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+([+-]?[\d.,]+)$', line)
                    if itau_simple_match:
                        data = itau_simple_match.group(1)
                        descricao = itau_simple_match.group(2).strip()
                        valor_str = itau_simple_match.group(3).replace('.', '').replace(',', '.')
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
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
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    output_dir = script_dir.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    itau_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["ITAU", "ITAÚ", "341"]):
            itau_files.append(pdf_file)
    
    if not itau_files:
        print("Nenhum PDF do Itaú encontrado em data/input/")
        return
    
    pdf_path = itau_files[0]
    print(f"Processando extrato do Itaú: {pdf_path.name}")
    
    transactions, metadata = extract_itau_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    df = pd.DataFrame(transactions)
    
    # Ordenar por data, documento, descrição
    df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m', errors='coerce')
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
    
    output_path = output_dir / (pdf_path.stem + "_itau_extraido.xlsx")
    try:
        df.to_excel(output_path, index=False)
        print(f"\nDados extraídos salvos em: {output_path}")
    except PermissionError:
        print(f"\nAviso: Não foi possível salvar o arquivo (pode estar aberto no Excel)")

if __name__ == "__main__":
    main()