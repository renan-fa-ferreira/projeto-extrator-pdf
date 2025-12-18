#!/usr/bin/env python3
"""Extrator genérico para bancos não específicos"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def detect_bank_from_text(text):
    """Detecta o banco baseado no texto do PDF"""
    bank_patterns = {
        'Banco do Brasil': ['BANCO DO BRASIL', 'BB', '001'],
        'Banco Bradesco S/A': ['BRADESCO', '237'],
        'Banco Itaú': ['ITAU', 'ITAÚ', '341'],
        'Caixa Econômica Federal': ['CAIXA', 'CEF', '104'],
        'Banco Safra': ['SAFRA', '422'],
        'Banco Daycoval': ['DAYCOVAL', '707'],
        'Banco BV': ['BV', 'VOTORANTIM', '655'],
        'Banco ABC Brasil': ['ABC', '246']
    }
    
    for banco, keywords in bank_patterns.items():
        if any(keyword in text.upper() for keyword in keywords):
            return banco
    
    return 'Banco Não Identificado'

def extract_generic_data(pdf_path):
    """Extrai dados usando múltiplas estratégias genéricas com detecção automática"""
    transactions = []
    metadata = {
        'banco': 'Banco Não Identificado',
        'codigo_banco': '',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Detectar banco na primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    metadata['banco'] = detect_bank_from_text(first_page_text)
                    
                    # Extrair metadados genéricos
                    agencia_match = re.search(r'Ag[eê]ncia[:\s]*(\d+[-]?\d*)', first_page_text)
                    if agencia_match:
                        metadata['agencia'] = agencia_match.group(1)
                    
                    conta_match = re.search(r'Conta[:\s]*(\d+[-]?\d*)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
            
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                # Padrões universais baseados nos bancos implementados
                patterns = [
                    # Padrão BB: Data, ag, lote, histórico, doc, valor, tipo, saldo, tipo
                    r'(\d{2}/\d{2}/\d{4})\s+(\d{4})\s+(\d{8})\s+(.+?)\s+(\d+[.,]\d+)\s+([\d.,]+)\s+([DC])\s+([\d.,]+)\s+([DC])',
                    # Padrão Bradesco: Data, documento, valor com sinal, saldo
                    r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+([+-]?[\d.,]+)\s+([\d.,]+)',
                    # Padrão Caixa: Data, documento, descrição, valor+D/C, saldo+D/C
                    r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+([\d.,]+)([DC])\s+([\d.,]+)([DC])',
                    # Padrão Itaú: Data DD/MM, descrição, documento, valor com sinal
                    r'(\d{2}/\d{2})\s+(.+?)\s+(\d+)\s+([\d.,]+)([+-])',
                    # Padrão genérico com D/C
                    r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)\s+([DC])\s+([\d.,]+)',
                    # Padrão genérico simples
                    r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)\s+([DC])',
                    # Padrão com valores positivos/negativos
                    r'(\d{2}/\d{2}(?:/\d{4})?)\s+(.+?)\s+([+-]?[\d.,]+)'
                ]
                
                for pattern in patterns:
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        try:
                            groups = match.groups()
                            
                            # Processar baseado no número de grupos
                            if len(groups) == 9:  # Padrão BB completo
                                data = groups[0]
                                descricao = groups[3].strip()
                                valor_str = groups[5].replace('.', '').replace(',', '.')
                                tipo = groups[6]
                                saldo_str = groups[7].replace('.', '').replace(',', '.')
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str)
                                })
                            elif len(groups) == 7:  # Padrão Caixa
                                data = groups[0]
                                documento = groups[1]
                                descricao = groups[2].strip()
                                valor_str = groups[3].replace('.', '').replace(',', '.')
                                tipo = groups[4]
                                saldo_str = groups[5].replace('.', '').replace(',', '.')
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Documento': documento,
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str)
                                })
                            elif len(groups) == 5:  # Padrões com 5 grupos
                                data = groups[0]
                                descricao = groups[1].strip()
                                
                                if groups[4] in ['D', 'C']:  # Tipo no final
                                    valor_str = groups[2].replace('.', '').replace(',', '.')
                                    tipo = groups[4]
                                    saldo_str = groups[3].replace('.', '').replace(',', '.')
                                elif groups[4] in ['+', '-']:  # Sinal no final
                                    documento = groups[2]
                                    valor_str = groups[3].replace('.', '').replace(',', '.')
                                    tipo = 'D' if groups[4] == '-' else 'C'
                                    saldo_str = '0'
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str) if saldo_str != '0' else 0.0
                                })
                            elif len(groups) == 4:  # Padrões com 4 grupos
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                
                                if groups[3] in ['D', 'C']:
                                    tipo = groups[3]
                                    saldo_str = '0'
                                else:
                                    saldo_str = groups[3].replace('.', '').replace(',', '.')
                                    tipo = 'D' if valor_str.startswith('-') else 'C'
                                    valor_str = valor_str.replace('-', '')
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': float(valor_str),
                                    'Tipo': tipo,
                                    'Saldo': float(saldo_str) if saldo_str != '0' else 0.0
                                })
                            elif len(groups) == 3:  # Padrão simples
                                data = groups[0]
                                descricao = groups[1].strip()
                                valor_str = groups[2].replace('.', '').replace(',', '.')
                                
                                tipo = 'D' if valor_str.startswith('-') else 'C'
                                valor = float(valor_str.replace('-', ''))
                                
                                transactions.append({
                                    'Banco': metadata['banco'],
                                    'Agência': metadata['agencia'],
                                    'Conta': metadata['conta'],
                                    'Data': data,
                                    'Descrição': descricao,
                                    'Valor': valor,
                                    'Tipo': tipo,
                                    'Saldo': 0.0
                                })
                            
                        except Exception as e:
                            continue
                    
                    if transactions:  # Se encontrou transações, para
                        break
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    # Remover duplicatas
    seen = set()
    unique_transactions = []
    for t in transactions:
        key = (t['Data'], t['Descrição'], t['Valor'])
        if key not in seen:
            seen.add(key)
            unique_transactions.append(t)
    
    return unique_transactions, metadata

def main():
    # Definir pastas
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Processar todos os PDFs encontrados
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF encontrado em data/input/")
        return
    
    print(f"Encontrados {len(pdf_files)} PDFs para processar")
    
    for pdf_path in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processando: {pdf_path.name}")
        print(f"{'='*60}")
        
        transactions, metadata = extract_generic_data(pdf_path)
        
        if not transactions:
            print("Nenhuma transação encontrada")
            continue
        
        # Criar DataFrame
        df = pd.DataFrame(transactions)
        
        # Salvar em Excel na pasta output
        output_path = output_dir / (pdf_path.stem + "_generico_extraido.xlsx")
        df.to_excel(output_path, index=False)
        
        print(f"Banco detectado: {metadata['banco']}")
        print(f"Agência: {metadata['agencia']}")
        print(f"Conta: {metadata['conta']}")
        print(f"Dados extraídos salvos em: {output_path}")
        print(f"Total de transações: {len(transactions)}")
        print("\nPrimeiras 3 transações:")
        print(df.head(3).to_string(index=False))
    
    print(f"\n{'='*60}")
    print(f"Processamento concluído para {len(pdf_files)} arquivos")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()