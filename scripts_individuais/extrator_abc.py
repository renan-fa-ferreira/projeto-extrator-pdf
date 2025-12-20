#!/usr/bin/env python3
"""Extrator individual melhorado para Banco ABC Brasil"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_abc_data(pdf_path):
    """Extrai dados do extrato do Banco ABC Brasil"""
    transactions = []
    metadata = {
        'banco': 'Banco ABC Brasil',
        'codigo_banco': '246',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    # Extrair agência e conta
                    agencia_match = re.search(r'Agência[:\s]*(\d+[-]?\d*)', first_page_text)
                    if agencia_match:
                        metadata['agencia'] = agencia_match.group(1)
                    
                    conta_match = re.search(r'Conta[:\s]*(\d+[-]?\d*)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    
                    # Extrair período
                    periodo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+[ae]\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            # Processar todas as páginas
            all_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
            
            # Padrões específicos para ABC Brasil
            patterns = [
                # Padrão 1: Data completa, descrição, valor, tipo, saldo
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)\s+([DC])\s+([\d.,]+)',
                # Padrão 2: Data, documento, descrição, valor, saldo
                r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+([\d.,]+)\s+([\d.,]+)',
                # Padrão 3: Data simples, descrição, valor
                r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)\s+([DC])',
                # Padrão 4: Formato genérico
                r'(\d{2}/\d{2}(?:/\d{4})?)\s+(.+?)\s+([\d.,]+)',
                # Padrão 5: Buscar por linhas com valores monetários
                r'(.+?)\s+([\d.,]+)\s+([DC])\s+([\d.,]+)',
                # Padrão 6: Transações sem tipo explícito
                r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, all_text)
                
                for match in matches:
                    try:
                        groups = match.groups()
                        
                        if len(groups) == 5:  # Padrão completo
                            data = groups[0]
                            descricao = groups[1].strip()
                            valor_str = groups[2].replace('.', '').replace(',', '.')
                            tipo = groups[3] if groups[3] in ['D', 'C'] else 'C'
                            saldo_str = groups[4].replace('.', '').replace(',', '.')
                            documento = ''
                            
                            # Se o segundo campo é número, pode ser documento
                            if groups[1].isdigit():
                                documento = groups[1]
                                descricao = groups[2].strip()
                                valor_str = groups[3].replace('.', '').replace(',', '.')
                                saldo_str = groups[4].replace('.', '').replace(',', '.')
                        
                        elif len(groups) == 4:  # 4 grupos
                            if groups[0].count('/') == 2:  # Data completa
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                tipo = groups[3] if groups[3] in ['D', 'C'] else 'C'
                                saldo_str = '0'
                                documento = ''
                            else:  # Sem data ou formato diferente
                                continue
                        
                        elif len(groups) == 3:  # 3 grupos
                            data = groups[0]
                            descricao = groups[1].strip()
                            valor_str = groups[2].replace('.', '').replace(',', '.')
                            tipo = 'C'  # Default
                            saldo_str = '0'
                            documento = ''
                        
                        else:
                            continue
                        
                        # Validar se é uma transação válida
                        if (len(descricao) > 2 and 
                            not descricao.upper().startswith('DATA') and
                            not descricao.upper().startswith('SALDO') and
                            valor_str.replace('.', '').isdigit()):
                            
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
                                'Saldo': float(saldo_str) if saldo_str != '0' else 0.0
                            })
                    
                    except Exception as e:
                        continue
                
                if transactions:
                    break
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    return transactions, metadata

def main():
    # Definir pastas
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar PDFs do ABC Brasil na pasta input
    abc_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["ABC", "246"]):
            abc_files.append(pdf_file)
    
    if not abc_files:
        print("Nenhum PDF do Banco ABC Brasil encontrado em data/input/")
        return
    
    pdf_path = abc_files[0]
    
    print(f"Processando extrato do Banco ABC Brasil: {pdf_path.name}")
    
    transactions, metadata = extract_abc_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Ordenar por data, documento, descrição
    df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Data_Sort'] = df['Data_Sort'].fillna(pd.to_datetime(df['Data'], format='%d/%m', errors='coerce'))
    df = df.sort_values(['Data_Sort', 'Documento', 'Descrição'], na_position='last')
    df = df.drop('Data_Sort', axis=1)
    
    # Salvar em Excel na pasta output
    output_path = output_dir / (pdf_path.stem + "_abc_extraido.xlsx")
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