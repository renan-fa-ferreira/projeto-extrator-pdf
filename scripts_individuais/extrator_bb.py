#!/usr/bin/env python3
"""Extrator individual para Banco do Brasil"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_bb_data(pdf_path):
    """Extrai dados do extrato do Banco do Brasil"""
    transactions = []
    metadata = {
        'banco': 'Banco do Brasil',
        'codigo_banco': '001',
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
                    # Extrair agência
                    agencia_match = re.search(r'Agência:\s*(\d+-\d+)', first_page_text)
                    if agencia_match:
                        metadata['agencia'] = agencia_match.group(1)
                    
                    # Extrair conta
                    conta_match = re.search(r'Conta Corrente:\s*(\d+-\d+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
            
            # Processar todas as páginas
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                print(f"Página {page_num + 1}: {len(lines)} linhas")
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith(('Dt.', 'Ag.', 'Página')):
                        continue
                    
                    # Padrão BB: DD/MM/YYYY AG_ORIGEM LOTE HISTÓRICO DOCUMENTO VALOR TIPO
                    bb_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{4})\s+(\d+)\s+(.+?)\s+([\d.]+)\s+([\d.,]+)\s+([CD])', line)
                    if bb_match:
                        data = bb_match.group(1)
                        ag_origem = bb_match.group(2)
                        lote = bb_match.group(3)
                        historico = bb_match.group(4).strip()
                        documento = bb_match.group(5)
                        valor_str = bb_match.group(6).replace('.', '').replace(',', '.')
                        tipo = bb_match.group(7)
                        
                        # Procurar descrição adicional na próxima linha
                        descricao_completa = historico
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not re.search(r'\d{2}/\d{2}/\d{4}', next_line) and len(next_line) > 5:
                                descricao_completa += " " + next_line
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': documento,
                            'Descrição': descricao_completa,
                            'Valor': float(valor_str),
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Padrão BB flexível: qualquer linha com data
                    bb_flex = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+)', line)
                    if bb_flex:
                        data = bb_flex.group(1)
                        resto = bb_flex.group(2).strip()
                        
                        # Tentar extrair valor e tipo do final
                        valor_match = re.search(r'([\d.,]+)\s+([CD])\s*$', resto)
                        if valor_match:
                            valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                            tipo = valor_match.group(2)
                            descricao = resto[:valor_match.start()].strip()
                            
                            # Procurar descrição adicional na próxima linha
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if next_line and not re.search(r'\d{2}/\d{2}/\d{4}', next_line) and len(next_line) > 5:
                                    descricao += " " + next_line
                            
                            transactions.append({
                                'Banco': metadata['banco'],
                                'Código Banco': metadata['codigo_banco'],
                                'Agência': metadata['agencia'],
                                'Conta': metadata['conta'],
                                'Data': data,
                                'Documento': '',
                                'Descrição': descricao,
                                'Valor': float(valor_str),
                                'Tipo': tipo,
                                'Saldo': 0.0
                            })
                            continue
            
            print(f"Total de transações encontradas: {len(transactions)}")
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    return transactions, metadata

def main():
    # Definir pastas
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    output_dir = script_dir.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar PDFs do BB na pasta input
    bb_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["BB", "001", "BANCO DO BRASIL"]):
            bb_files.append(pdf_file)
    
    if not bb_files:
        print("Nenhum PDF do Banco do Brasil encontrado em data/input/")
        return
    
    pdf_path = bb_files[0]
    
    print(f"Processando extrato do Banco do Brasil: {pdf_path.name}")
    
    transactions, metadata = extract_bb_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
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
    print(f"Total de transações: {len(transactions)}")
    print("\nPrimeiras 5 transações:")
    print(df.head().to_string(index=False))
    
    # Salvar em Excel na pasta output
    output_path = output_dir / (pdf_path.stem + "_bb_extraido.xlsx")
    try:
        df.to_excel(output_path, index=False)
        print(f"\nDados extraídos salvos em: {output_path}")
    except PermissionError:
        print(f"\nAviso: Não foi possível salvar o arquivo (pode estar aberto no Excel)")

if __name__ == "__main__":
    main()