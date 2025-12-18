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
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    # Extrair agência
                    agencia_match = re.search(r'Ag[eê]ncia\s+(\d+-\d+)', first_page_text)
                    if agencia_match:
                        metadata['agencia'] = agencia_match.group(1)
                    
                    # Extrair conta
                    conta_match = re.search(r'Conta corrente\s+(\d+-\d+)', first_page_text)
                    if conta_match:
                        metadata['conta'] = conta_match.group(1)
                    
                    # Extrair período
                    periodo_match = re.search(r'(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})', first_page_text)
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                

                
                # Múltiplos padrões para BB baseados no formato real
                patterns = [
                    # Padrão 1: Data balancete, ag origem, lote, histórico, documento, valor, tipo, saldo, tipo
                    r'(\d{2}/\d{2}/\d{4})\s+(\d{4})\s+(\d{8})\s+(.+?)\s+(\d+[.,]\d+)\s+([\d.,]+)\s+([DC])\s+([\d.,]+)\s+([DC])',
                    # Padrão 2: Formato simplificado
                    r'(\d{2}/\d{2}/\d{4})\s+(\d{4})\s+(\d{8})\s+(.+?)\s+(\d+[.,]\d+)\s+([\d.,]+)\s+([DC])',
                    # Padrão 3: Ainda mais simples
                    r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(\d+[.,]\d+)\s+([\d.,]+)\s+([DC])'
                ]
                
                for pattern_num, pattern in enumerate(patterns):
                    matches = list(re.finditer(pattern, text))
                    
                    for match in matches:
                        try:
                            groups = match.groups()

                            
                            if len(groups) == 9:  # Padrão completo
                                dt_balancete = groups[0]
                                ag_origem = groups[1]
                                lote = groups[2]
                                historico = groups[3].strip()
                                documento = groups[4]
                                valor_str = groups[5]
                                tipo = groups[6]
                                saldo_str = groups[7]
                                saldo_tipo = groups[8]
                            elif len(groups) == 7:  # Padrão médio
                                dt_balancete = groups[0]
                                ag_origem = groups[1]
                                lote = groups[2]
                                historico = groups[3].strip()
                                documento = groups[4]
                                valor_str = groups[5]
                                tipo = groups[6]
                                saldo_str = "0"
                                saldo_tipo = "C"
                            else:  # Padrão simples
                                dt_balancete = groups[0]
                                historico = groups[1].strip()
                                documento = groups[2]
                                valor_str = groups[3]
                                tipo = groups[4]
                                ag_origem = ""
                                lote = ""
                                saldo_str = "0"
                                saldo_tipo = "C"
                            
                            # Limpar valores
                            valor_str = valor_str.replace('.', '').replace(',', '.')
                            saldo_str = saldo_str.replace('.', '').replace(',', '.')
                            
                            transactions.append({
                                'Banco': metadata['banco'],
                                'Código Banco': metadata['codigo_banco'],
                                'Agência': metadata['agencia'],
                                'Conta': metadata['conta'],
                                'Data': dt_balancete,
                                'Agência Origem': ag_origem,
                                'Lote': lote,
                                'Histórico': historico,
                                'Documento': documento,
                                'Valor': float(valor_str),
                                'Tipo': tipo,
                                'Saldo': float(saldo_str) if saldo_str != "0" else 0.0
                            })
                            
                        except Exception as e:
                            continue
                    
                    if transactions:  # Se já encontrou transações, para
                        break
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    return transactions, metadata

def main():
    # Definir pastas
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    
    # Criar pasta de output se não existir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar PDFs do BB na pasta input
    bb_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["BRASIL", "BB", "001"]):
            bb_files.append(pdf_file)
    
    if not bb_files:
        print("Nenhum PDF do Banco do Brasil encontrado em data/input/")
        print(f"Procurando em: {input_dir.absolute()}")
        print(f"Diretório atual: {Path.cwd()}")
        print(f"Arquivos encontrados: {list(input_dir.glob('*.pdf'))}")
        return
    
    pdf_path = bb_files[0]
    
    print(f"Processando extrato do Banco do Brasil: {pdf_path.name}")
    
    transactions, metadata = extract_bb_data(pdf_path)
    
    if not transactions:
        print("Nenhuma transação encontrada")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(transactions)
    
    # Salvar em Excel na pasta output
    output_path = output_dir / (pdf_path.stem + "_bb_extraido.xlsx")
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