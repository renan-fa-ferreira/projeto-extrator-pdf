#!/usr/bin/env python3
"""Extrator individual para Banco do Brasil"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

def extract_bb_data(pdf_path):
    """Extrai dados do extrato do Banco do Brasil"""
    transactions = []
    log_info = {'arquivo': pdf_path.name, 'paginas': 0, 'transacoes': 0}
    metadata = {
        'banco': 'Banco do Brasil',
        'codigo_banco': '001',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            log_info['paginas'] = len(pdf.pages)
            print(f"Processando {len(pdf.pages)} páginas...")
            
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    agencia_match = re.search(r'Agência:\s*(\d+-\d+)', first_page_text)
                    if agencia_match:
                        metadata['agencia'] = agencia_match.group(1)
                    conta_match = re.search(r'Conta Corrente:\s*(\d+-\d+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith(('Dt.', 'Ag.', 'Página')):
                        continue
                    
                    bb_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)\s+([CD])', line)
                    if bb_match:
                        data = bb_match.group(1)
                        descricao = bb_match.group(2).strip()
                        valor_str = bb_match.group(3).replace('.', '').replace(',', '.')
                        tipo = bb_match.group(4)
                        
                        try:
                            valor = float(valor_str)
                        except ValueError:
                            continue
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Codigo Banco': metadata['codigo_banco'],
                            'Agencia': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': '',
                            'Descricao': descricao,
                            'Valor': f"{valor:.2f}".replace('.', ','),
                            'Tipo': tipo,
                            'Saldo': '0,00'
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
    
    bb_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["BB", "001", "BANCO DO BRASIL"]):
            bb_files.append(pdf_file)
    
    if not bb_files:
        print("Nenhum PDF do Banco do Brasil encontrado em data/input/")
        return
    
    all_transactions = []
    processed_files = 0
    logs = []
    
    for pdf_path in bb_files:
        print(f"\nProcessando: {pdf_path.name}")
        transactions, metadata, log_info = extract_bb_data(pdf_path)
        logs.append(log_info)
        
        if transactions:
            all_transactions.extend(transactions)
            processed_files += 1
            
            df = pd.DataFrame(transactions)
            df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(['Data_Sort', 'Documento', 'Descricao'], na_position='last')
            df = df.drop('Data_Sort', axis=1)
            
            output_path = output_dir / (pdf_path.stem + "_bb_extraido.csv")
            df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
            print(f"Dados extraidos salvos em: {output_path}")
            print(f"Total de transações: {len(transactions)}")
    
    # Salvar logs
    if logs:
        logs_df = pd.DataFrame(logs)
        logs_path = output_dir / "bb_logs.csv"
        logs_df.to_csv(logs_path, index=False, encoding='utf-8', sep=';')
        print(f"\nLogs salvos em: {logs_path}")

if __name__ == "__main__":
    main()