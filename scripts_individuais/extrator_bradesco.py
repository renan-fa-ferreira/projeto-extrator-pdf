#!/usr/bin/env python3
"""Extrator individual melhorado para Bradesco - captura TODAS as transações"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def concatenate_description_lines(lines, start_index):
    """Concatena linhas de descrição que foram quebradas"""
    description_parts = []
    i = start_index
    
    while i >= 0:
        line = lines[i].strip()
        
        # Para se encontrar linha com números (valores/documentos) ou data
        if (re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', line) or 
            re.search(r'\d{2}/\d{2}/\d{4}', line) or
            line.isdigit() or
            not line or
            len(line) < 3):
            break
            
        # Adiciona a linha à descrição
        description_parts.insert(0, line)
        i -= 1
        
        # Limita a 3 linhas para evitar pegar dados irrelevantes
        if len(description_parts) >= 3:
            break
    
    return ' '.join(description_parts) if description_parts else "DEP ETV DINHEIRO"

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
            print(f"Processando {len(pdf.pages)} páginas...")
            
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
                    
                    # Padrão principal: DOCUMENTO VALOR SALDO (linha com números)
                    transaction_match = re.search(r'^(\d+)\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})$', line)
                    if transaction_match:
                        doc = transaction_match.group(1)
                        valor_str = transaction_match.group(2).replace('.', '').replace(',', '.')
                        saldo_str = transaction_match.group(3).replace('.', '').replace(',', '.')
                        
                        # Concatenar descrição das linhas anteriores
                        descricao = concatenate_description_lines(lines, i - 1)
                        
                        # Usar data atual ou tentar extrair da linha
                        data_transacao = current_date if current_date else "01/01/2024"
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data_transacao,
                            'Documento': doc,
                            'Descrição': descricao,
                            'Valor': float(valor_str),
                            'Tipo': 'C',
                            'Saldo': float(saldo_str)
                        })
                        continue
                    
                    # Padrão de data: captura nova data de transação
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                    if date_match and not re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', line):
                        current_date = date_match.group(1)
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
    
    # Procurar PDFs do Bradesco na pasta input
    bradesco_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        filename_upper = pdf_file.name.upper()
        if any(word in filename_upper for word in ["BRADESCO", "237", "BRAD"]):
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
    
    # Tentar salvar em Excel na pasta output
    output_path = output_dir / (pdf_path.stem + "_bradesco_extraido.xlsx")
    try:
        df.to_excel(output_path, index=False)
        print(f"\nDados extraídos salvos em: {output_path}")
    except PermissionError:
        print(f"\nAviso: Não foi possível salvar o arquivo (pode estar aberto no Excel)")
        print(f"Feche o arquivo e execute novamente para salvar.")

if __name__ == "__main__":
    main()