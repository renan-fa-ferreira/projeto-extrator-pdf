#!/usr/bin/env python3
"""Extrator individual para Bradesco"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

def extract_bradesco_data(pdf_path):
    """Extrai dados do extrato do Bradesco"""
    transactions = []
    log_info = {'arquivo': pdf_path.name, 'paginas': 0, 'transacoes': 0}
    metadata = {
        'banco': 'Banco Bradesco S/A',
        'codigo_banco': '237',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            log_info['paginas'] = len(pdf.pages)
            print(f"Processando {len(pdf.pages)} páginas...")
            
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    agencia_conta_match = re.search(r'Ag:\s*(\d+)\s*\|\s*CC:\s*(\d+-\d+)', first_page_text)
                    if agencia_conta_match:
                        metadata['agencia'] = agencia_conta_match.group(1)
                        metadata['conta'] = agencia_conta_match.group(2)
            
            current_date = None
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Capturar data
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                    if date_match and not re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', line):
                        current_date = date_match.group(1)
                        continue
                    
                    # Transação: DOCUMENTO VALOR SALDO
                    transaction_match = re.search(r'^(\d+)\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})$', line)
                    if transaction_match:
                        doc = transaction_match.group(1)
                        valor_str = transaction_match.group(2).replace('.', '').replace(',', '.')
                        saldo_str = transaction_match.group(3).replace('.', '').replace(',', '.')
                        
                        # Buscar descrição nas linhas anteriores
                        descricao = "Operacao Bancaria"
                        for j in range(max(0, i-3), i):
                            prev_line = lines[j].strip()
                            if prev_line and not re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', prev_line) and len(prev_line) > 3:
                                descricao = prev_line
                                break
                        
                        data_transacao = current_date if current_date else "01/01/2024"
                        
                        try:
                            valor = float(valor_str)
                            saldo = float(saldo_str)
                        except ValueError:
                            continue
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Codigo Banco': metadata['codigo_banco'],
                            'Agencia': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data_transacao,
                            'Documento': doc,
                            'Descricao': descricao,
                            'Valor': f"{valor:.2f}".replace('.', ','),
                            'Tipo': 'C',
                            'Saldo': f"{saldo:.2f}".replace('.', ',')
                        })
            
            print(f"Total de transações encontradas: {len(transactions)}")
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata, log_info
    
    log_info['transacoes'] = len(transactions)
    return transactions, metadata, log_info

def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    output_dir = script_dir.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    bradesco_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["BRADESCO", "237", "BRAD"]):
            bradesco_files.append(pdf_file)
    
    if not bradesco_files:
        print("Nenhum PDF do Bradesco encontrado em data/input/")
        return
    
    all_transactions = []
    processed_files = 0
    logs = []
    
    for pdf_path in bradesco_files:
        print(f"\nProcessando: {pdf_path.name}")
        transactions, metadata, log_info = extract_bradesco_data(pdf_path)
        logs.append(log_info)
        
        if transactions:
            all_transactions.extend(transactions)
            processed_files += 1
            
            df = pd.DataFrame(transactions)
            df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(['Data_Sort', 'Documento', 'Descricao'], na_position='last')
            df = df.drop('Data_Sort', axis=1)
            
            output_path = output_dir / (pdf_path.stem + "_bradesco_extraido.csv")
            df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
            print(f"Dados extraidos salvos em: {output_path}")
            print(f"Total de transações: {len(transactions)}")
    
    # Salvar logs
    if logs:
        logs_df = pd.DataFrame(logs)
        logs_path = output_dir / "bradesco_logs.csv"
        logs_df.to_csv(logs_path, index=False, encoding='utf-8', sep=';')
        print(f"\nLogs salvos em: {logs_path}")

if __name__ == "__main__":
    main()