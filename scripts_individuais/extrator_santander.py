#!/usr/bin/env python3
"""Extrator específico para Santander"""

import pdfplumber
import pandas as pd
import re
from pathlib import Path

def extract_santander_transactions(pdf_path):
    """Extrai transações do Santander"""
    transactions = []
    log_info = {'arquivo': pdf_path.name, 'paginas': 0, 'transacoes': 0}
    
    with pdfplumber.open(pdf_path) as pdf:
        log_info['paginas'] = len(pdf.pages)
        print(f"Processando {len(pdf.pages)} páginas...")
        
        # Metadados da primeira página
        first_page = pdf.pages[0].extract_text() if pdf.pages else ""
        agencia_match = re.search(r'AGENCIA\s+(\d+)', first_page)
        conta_match = re.search(r'CONTA\s+(\d+)', first_page)
        
        agencia = agencia_match.group(1) if agencia_match else ""
        conta = conta_match.group(1) if conta_match else ""
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Padrão: DD/MM/YYYY DESCRIÇÃO VALOR
                santander_match = re.search(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)$', line)
                if santander_match:
                    data = santander_match.group(1)
                    descricao = santander_match.group(2).strip()
                    valor_str = santander_match.group(3).strip()
                    
                    # Pular linhas de saldo anterior
                    if "SALDO ANTERIOR" in descricao.upper():
                        continue
                    
                    # Limpar valor (formato brasileiro: 1.234,56)
                    # Remover pontos (milhares) e trocar vírgula por ponto (decimal)
                    if ',' in valor_str:
                        # Formato: 1.234,56 -> 1234.56
                        parts = valor_str.split(',')
                        if len(parts) == 2 and len(parts[1]) == 2:  # Centavos
                            valor_clean = parts[0].replace('.', '') + '.' + parts[1]
                        else:
                            valor_clean = valor_str.replace('.', '').replace(',', '.')
                    else:
                        valor_clean = valor_str.replace('.', '')
                    
                    # Determinar tipo
                    tipo = 'D' if valor_clean.startswith('-') else 'C'
                    
                    try:
                        valor = float(valor_clean.replace('-', ''))
                    except ValueError:
                        continue
                    
                    transactions.append({
                        'Banco': 'Banco Santander',
                        'Codigo Banco': '033',
                        'Agencia': agencia,
                        'Conta': conta,
                        'Data': data,
                        'Documento': '',
                        'Descricao': descricao,
                        'Valor': f"{valor:.2f}".replace('.', ','),
                        'Tipo': tipo,
                        'Saldo': '0,00',
                        'Arquivo': pdf_path.name
                    })
    
    log_info['transacoes'] = len(transactions)
    return transactions, log_info

def main():
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF na pasta input")
        return
    
    all_transactions = []
    logs = []
    
    for pdf_path in pdf_files:
        print(f"\nProcessando: {pdf_path.name}")
        transactions, log_info = extract_santander_transactions(pdf_path)
        logs.append(log_info)
        
        if transactions:
            all_transactions.extend(transactions)
            print(f"  OK {len(transactions)} transações extraídas")
        else:
            print(f"  X Nenhuma transação encontrada")
    
    if all_transactions:
        # Criar DataFrame
        df = pd.DataFrame(all_transactions)
        
        # Ordenar por data
        df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df = df.sort_values('Data_Sort', na_position='last')
        df = df.drop('Data_Sort', axis=1)
        
        # Salvar em CSV UTF-8
        output_path = output_dir / "santander_extraido.csv"
        df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
        
        # Salvar logs
        logs_df = pd.DataFrame(logs)
        logs_path = output_dir / "santander_logs.csv"
        logs_df.to_csv(logs_path, index=False, encoding='utf-8', sep=';')
        
        print(f"\nArquivo salvo: {output_path}")
        print(f"Logs salvos: {logs_path}")
        print(f"Total de transações: {len(all_transactions)}")
        
        # Mostrar amostra
        print("\nPrimeiras 5 transações:")
        print(df.head(5)[['Data', 'Descricao', 'Valor', 'Tipo']].to_string(index=False))

if __name__ == "__main__":
    main()