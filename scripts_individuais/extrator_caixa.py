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
            print(f"Processando {len(pdf.pages)} páginas...")
            
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    # Extrair conta
                    conta_match = re.search(r'Conta[:\s]*(\d+[/-]\d+[/-]\d+[-]\d+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    
                    # Extrair período
                    periodo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+[ae]\s+(\d{2}/\d{2}/\d{4})', first_page_text)
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
                        continue
                    
                    # Padrão sem documento: DD/MM/YYYY DESCRIÇÃO VALOR+D/C SALDO+D/C
                    caixa_simple = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)([DC])\s+([\d.,]+)([DC])', line)
                    if caixa_simple:
                        data = caixa_simple.group(1)
                        descricao = caixa_simple.group(2).strip()
                        valor_str = caixa_simple.group(3).replace('.', '').replace(',', '.')
                        tipo = caixa_simple.group(4)
                        saldo_str = caixa_simple.group(5).replace('.', '').replace(',', '.')
                        
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
                            'Saldo': float(saldo_str)
                        })
                        continue
                    
                    # Padrão flexível: qualquer linha com data
                    caixa_flex = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+)', line)
                    if caixa_flex:
                        data = caixa_flex.group(1)
                        resto = caixa_flex.group(2).strip()
                        
                        # Tentar extrair valor e tipo do final
                        valor_match = re.search(r'([\d.,]+)([DC])\s*$', resto)
                        if valor_match:
                            valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                            tipo = valor_match.group(2)
                            descricao = resto[:valor_match.start()].strip()
                            
                            if len(descricao) > 3:
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
    
    # Procurar PDFs da Caixa na pasta input
    caixa_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if pdf_file.name.upper().startswith("CEF") or any(word in pdf_file.name.upper() for word in ["CAIXA", "104"]):
            caixa_files.append(pdf_file)
    
    if not caixa_files:
        print("Nenhum PDF da Caixa encontrado em data/input/")
        return
    
    # Priorizar PDFs que começam com CEF
    pdf_path = next((f for f in caixa_files if f.name.upper().startswith("CEF")), caixa_files[0])
    
    print(f"Processando extrato da Caixa: {pdf_path.name}")
    
    transactions, metadata = extract_caixa_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Ordenar por data, documento, descrição
    df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df = df.sort_values(['Data_Sort', 'Documento', 'Descrição'], na_position='last')
    df = df.drop('Data_Sort', axis=1)
    
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