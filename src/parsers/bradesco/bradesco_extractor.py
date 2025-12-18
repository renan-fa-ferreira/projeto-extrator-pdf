#!/usr/bin/env python3
"""Extrator específico para extratos do Bradesco"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.bank_statement import BankHeader, BankTransaction, BankStatement

class BradescoExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_header_info(self, text: str) -> dict:
        """Extrai informações do cabeçalho do Bradesco"""
        header = {}
        lines = text.split('\n')[:20]
        
        for line in lines:
            line = line.strip()
            
            # Banco
            if 'BRADESCO' in line.upper():
                header['banco'] = line
            
            # Agência e conta - padrões do Bradesco
            if 'AGÊNCIA' in line.upper() or 'AG.' in line.upper():
                # Procura por números
                numbers = re.findall(r'\d+[-.]?\d*', line)
                if numbers:
                    header['agencia'] = numbers[0]
            
            if 'CONTA' in line.upper() and 'CORRENTE' in line.upper():
                # Procura por número da conta
                match = re.search(r'(\d+[-.]?\d*)', line)
                if match:
                    header['conta'] = match.group(1)
            
            # Período
            if 'PERÍODO' in line.upper() or 'PERIODO' in line.upper():
                dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                if len(dates) >= 2:
                    try:
                        header['periodo_inicio'] = datetime.strptime(dates[0], '%d/%m/%Y')
                        header['periodo_fim'] = datetime.strptime(dates[1], '%d/%m/%Y')
                    except:
                        pass
            
            # Nome do titular
            if any(word in line.upper() for word in ['TITULAR', 'CLIENTE', 'CORRENTISTA']):
                # Pega texto após a palavra-chave
                for keyword in ['TITULAR', 'CLIENTE', 'CORRENTISTA']:
                    if keyword in line.upper():
                        parts = line.upper().split(keyword)
                        if len(parts) > 1:
                            header['titular'] = parts[1].strip()
                        break
        
        return header
    
    def extract_transactions_from_table(self, table, page_info) -> list:
        """Extrai transações de tabela do Bradesco"""
        transactions = []
        
        if not table or len(table) < 2:
            return transactions
        
        # Identifica header da tabela
        header_row = None
        for i, row in enumerate(table):
            if any(keyword in str(cell).upper() for cell in row if cell 
                   for keyword in ['DATA', 'HISTÓRICO', 'VALOR', 'SALDO']):
                header_row = i
                break
        
        if header_row is None:
            return transactions
        
        # Mapeia colunas
        header = table[header_row]
        col_mapping = {}
        
        for i, col in enumerate(header):
            if not col:
                continue
            col_upper = str(col).upper()
            
            if 'DATA' in col_upper:
                col_mapping['data'] = i
            elif 'HISTÓRICO' in col_upper or 'HISTORICO' in col_upper or 'DESCRIÇÃO' in col_upper:
                col_mapping['historico'] = i
            elif 'DOCUMENTO' in col_upper or 'DOC' in col_upper:
                col_mapping['documento'] = i
            elif 'VALOR' in col_upper:
                col_mapping['valor'] = i
            elif 'SALDO' in col_upper:
                col_mapping['saldo'] = i
        
        # Processa transações
        for row in table[header_row + 1:]:
            if not row or len(row) < 3:
                continue
            
            try:
                # Data
                if 'data' not in col_mapping:
                    continue
                
                date_str = str(row[col_mapping['data']] or '').strip()
                if not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                    continue
                
                date_mov = datetime.strptime(date_str, '%d/%m/%Y')
                
                # Histórico
                historico = ''
                if 'historico' in col_mapping:
                    historico = str(row[col_mapping['historico']] or '').strip()
                
                # Pula linhas de saldo
                if any(x in historico.upper() for x in ['SALDO ANTERIOR', 'SALDO ATUAL']):
                    continue
                
                # Documento
                documento = ''
                if 'documento' in col_mapping:
                    documento = str(row[col_mapping['documento']] or '').strip()
                
                # Valor - Bradesco pode ter formatos diferentes
                valor = 0.0
                tipo = 'debit'
                
                if 'valor' in col_mapping and row[col_mapping['valor']]:
                    valor_str = str(row[col_mapping['valor']]).strip()
                    
                    # Remove caracteres especiais
                    valor_clean = re.sub(r'[^\d.,-]', '', valor_str)
                    
                    # Detecta se é débito ou crédito
                    if '-' in valor_str or 'D' in valor_str.upper():
                        tipo = 'debit'
                    else:
                        tipo = 'credit'
                    
                    # Converte valor
                    try:
                        if ',' in valor_clean and '.' in valor_clean:
                            valor_clean = valor_clean.replace('.', '').replace(',', '.')
                        elif ',' in valor_clean:
                            valor_clean = valor_clean.replace(',', '.')
                        
                        valor = float(valor_clean.replace('-', ''))
                        if tipo == 'debit':
                            valor = -valor
                    except:
                        continue
                
                # Saldo
                saldo = None
                if 'saldo' in col_mapping and row[col_mapping['saldo']]:
                    saldo_str = str(row[col_mapping['saldo']]).strip()
                    try:
                        saldo_clean = re.sub(r'[^\d.,-]', '', saldo_str)
                        if ',' in saldo_clean and '.' in saldo_clean:
                            saldo_clean = saldo_clean.replace('.', '').replace(',', '.')
                        elif ',' in saldo_clean:
                            saldo_clean = saldo_clean.replace(',', '.')
                        saldo = float(saldo_clean.replace('-', ''))
                    except:
                        pass
                
                # Cria transação
                transaction = {
                    'arquivo': Path(self.pdf_path).name,
                    'data_movimento': date_mov.strftime('%d/%m/%Y'),
                    'historico': historico,
                    'documento': documento,
                    'valor': valor,
                    'saldo': saldo,
                    'tipo': tipo,
                    'conta': page_info.get('conta', ''),
                    'agencia': page_info.get('agencia', ''),
                    'banco': page_info.get('banco', 'BRADESCO'),
                    'titular': page_info.get('titular', '')
                }
                
                transactions.append(transaction)
                
            except Exception as e:
                continue
        
        return transactions
    
    def extract_statement(self):
        """Extrai extrato completo do Bradesco"""
        all_transactions = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                
                # Extrai info da página
                page_info = self.extract_header_info(text)
                
                # Processa tabelas
                tables = page.extract_tables()
                for table in tables:
                    transactions = self.extract_transactions_from_table(table, page_info)
                    all_transactions.extend(transactions)
        
        return pd.DataFrame(all_transactions)

def main():
    # Procura PDF do Bradesco na pasta input
    input_folder = "data/input"
    
    pdf_files = list(Path(input_folder).glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF encontrado na pasta input")
        return
    
    print("=== EXTRATOR BRADESCO ===\n")
    
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file.name}")
        
        try:
            extractor = BradescoExtractor(str(pdf_file))
            df = extractor.extract_statement()
            
            if not df.empty:
                # Remove duplicatas e ordena
                df = df.drop_duplicates()
                df['data_obj'] = pd.to_datetime(df['data_movimento'], format='%d/%m/%Y')
                df = df.sort_values('data_obj').drop('data_obj', axis=1)
                
                # Salva resultado
                output_file = f"data/output/bradesco_{pdf_file.stem}.xlsx"
                df.to_excel(output_file, index=False)
                
                print(f"✓ {len(df)} transações extraídas")
                print(f"✓ Salvo em: {output_file}")
                
                # Estatísticas
                creditos = df[df['tipo'] == 'credit']['valor'].sum()
                debitos = abs(df[df['tipo'] == 'debit']['valor'].sum())
                
                print(f"- Créditos: R$ {creditos:,.2f}")
                print(f"- Débitos: R$ {debitos:,.2f}")
                print(f"- Líquido: R$ {creditos - debitos:,.2f}")
                
                print(f"\nPreview:")
                print(df[['data_movimento', 'historico', 'valor', 'tipo']].head())
                
            else:
                print("✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"✗ Erro: {e}")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()