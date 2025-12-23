#!/usr/bin/env python3
"""Extrator individual para Caixa Economica Federal"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

def extract_caixa_data(pdf_path):
    """Extrai dados do extrato da Caixa"""
    transactions = []
    log_info = {'arquivo': pdf_path.name, 'paginas': 0, 'transacoes': 0}
    metadata = {
        'banco': 'Caixa Economica Federal',
        'codigo_banco': '104',
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
                    conta_match = re.search(r'Conta[:\s]*(\d+[/-]\d+[/-]\d+[-]\d+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    periodo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+[ae]\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith(('Data', 'Página', 'Consulta')):
                        continue
                    
                    # Padrão Caixa: DD/MM/YYYY DOCUMENTO DESCRIÇÃO VALOR+D/C SALDO+D/C
                    caixa_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+([\d.,]+)([DC])\s+([\d.,]+)([DC])', line)
                    if caixa_match:
                        data = caixa_match.group(1)
                        documento = caixa_match.group(2)
                        descricao = caixa_match.group(3).strip()
                        valor_str = caixa_match.group(4).replace('.', '').replace(',', '.')
                        tipo = caixa_match.group(5)
                        saldo_str = caixa_match.group(6).replace('.', '').replace(',', '.')
                        
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
                            'Data': data,
                            'Documento': documento,
                            'Descricao': descricao,
                            'Valor': f"{valor:.2f}".replace('.', ','),
                            'Tipo': tipo,
                            'Saldo': f"{saldo:.2f}".replace('.', ',')
                        })
                        continue
                    
                    # Padrão sem documento
                    caixa_simple = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)([DC])\s+([\d.,]+)([DC])', line)
                    if caixa_simple:
                        data = caixa_simple.group(1)
                        descricao = caixa_simple.group(2).strip()
                        valor_str = caixa_simple.group(3).replace('.', '').replace(',', '.')
                        tipo = caixa_simple.group(4)
                        saldo_str = caixa_simple.group(5).replace('.', '').replace(',', '.')
                        
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
                            'Data': data,
                            'Documento': '',
                            'Descricao': descricao,
                            'Valor': f"{valor:.2f}".replace('.', ','),
                            'Tipo': tipo,
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
    
    caixa_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["CAIXA", "104", "CEF"]):
            caixa_files.append(pdf_file)
    
    if not caixa_files:
        print("Nenhum PDF da Caixa encontrado em data/input/")
        return
    
    all_transactions = []
    processed_files = 0
    logs = []
    
    for pdf_path in caixa_files:
        print(f"\nProcessando: {pdf_path.name}")
        transactions, metadata, log_info = extract_caixa_data(pdf_path)
        logs.append(log_info)
        
        if transactions:
            all_transactions.extend(transactions)
            processed_files += 1
            
            df = pd.DataFrame(transactions)
            df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(['Data_Sort', 'Documento', 'Descricao'], na_position='last')
            df = df.drop('Data_Sort', axis=1)
            
            output_path = output_dir / (pdf_path.stem + "_caixa_extraido.csv")
            df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
            print(f"Dados extraidos salvos em: {output_path}")
            print(f"Total de transações: {len(transactions)}")
    
    # Salvar logs
    if logs:
        logs_df = pd.DataFrame(logs)
        logs_path = output_dir / "caixa_logs.csv"
        logs_df.to_csv(logs_path, index=False, encoding='utf-8', sep=';')
        print(f"\nLogs salvos em: {logs_path}")

if __name__ == "__main__":
    main()