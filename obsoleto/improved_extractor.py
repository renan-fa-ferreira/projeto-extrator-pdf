import pdfplumber
import pandas as pd
import re
from datetime import datetime
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.bank_statement import BankHeader, BankTransaction, BankStatement

class ImprovedBankExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_header_info(self, text: str) -> BankHeader:
        """Extrai informações do cabeçalho"""
        header = BankHeader()
        
        lines = text.split('\n')[:15]  # Primeiras 15 linhas
        
        for line in lines:
            line = line.strip()
            
            # Nome do banco
            if any(bank in line.upper() for bank in ['BANCO', 'BRADESCO', 'ITAU', 'SANTANDER', 'CAIXA']):
                header.bank_name = line
            
            # Conta e agência
            if 'CONTA' in line.upper() or 'AG' in line.upper():
                # Procura por números de conta/agência
                numbers = re.findall(r'\d+[-.]?\d*', line)
                if numbers:
                    if 'AG' in line.upper():
                        header.agency = numbers[0]
                    if 'CONTA' in line.upper():
                        header.account_number = numbers[-1]
            
            # Período
            date_matches = re.findall(r'\d{2}/\d{2}/\d{4}', line)
            if len(date_matches) >= 2 and ('PERÍODO' in line.upper() or 'PERIODO' in line.upper()):
                try:
                    header.period_start = datetime.strptime(date_matches[0], '%d/%m/%Y')
                    header.period_end = datetime.strptime(date_matches[1], '%d/%m/%Y')
                except:
                    pass
            
            # Nome do correntista
            if any(word in line.upper() for word in ['CORRENTISTA', 'TITULAR', 'CLIENTE']):
                # Pega a próxima parte que não seja número
                parts = line.split()
                for i, part in enumerate(parts):
                    if not re.match(r'^\d+', part) and len(part) > 3:
                        header.account_holder = ' '.join(parts[i:])
                        break
        
        return header
    
    def extract_transactions_from_table(self, table) -> List[BankTransaction]:
        """Extrai transações de uma tabela estruturada"""
        transactions = []
        
        if not table or len(table) < 2:
            return transactions
        
        # Identifica colunas pelo header
        header = table[0]
        col_mapping = {}
        
        for i, col in enumerate(header):
            if not col:
                continue
            col_lower = str(col).lower()
            
            if 'movimento' in col_lower or 'dt' in col_lower:
                col_mapping['movement_date'] = i
            elif 'balancete' in col_lower:
                col_mapping['balance_date'] = i
            elif 'histórico' in col_lower or 'historico' in col_lower or 'descrição' in col_lower:
                col_mapping['description'] = i
            elif 'documento' in col_lower or 'doc' in col_lower:
                col_mapping['document'] = i
            elif 'valor' in col_lower and 'r$' in col_lower:
                col_mapping['value'] = i
            elif 'saldo' in col_lower:
                col_mapping['balance'] = i
        
        # Processa cada linha
        for row in table[1:]:
            if not row or len(row) < 3:
                continue
            
            try:
                transaction = BankTransaction(movement_date=datetime.now())
                
                # Data movimento (obrigatória)
                if 'movement_date' in col_mapping:
                    date_str = str(row[col_mapping['movement_date']] or '').strip()
                    if date_str and re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                        transaction.movement_date = datetime.strptime(date_str, '%d/%m/%Y')
                    else:
                        continue  # Pula se não tem data válida
                
                # Data balancete
                if 'balance_date' in col_mapping:
                    date_str = str(row[col_mapping['balance_date']] or '').strip()
                    if date_str and re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                        transaction.balance_date = datetime.strptime(date_str, '%d/%m/%Y')
                
                # Descrição
                if 'description' in col_mapping:
                    transaction.description = str(row[col_mapping['description']] or '').strip()
                
                # Documento
                if 'document' in col_mapping:
                    doc = str(row[col_mapping['document']] or '').strip()
                    # Verifica se é realmente um documento (não um valor)
                    if doc and not re.match(r'^[\d.,+-]+$', doc):
                        transaction.document = doc
                
                # Valor - procura em todas as colunas se necessário
                value_found = False
                if 'value' in col_mapping:
                    value_str = str(row[col_mapping['value']] or '').strip()
                    if value_str:
                        transaction.value = self._parse_value(value_str)
                        value_found = True
                
                # Se não encontrou valor na coluna esperada, procura em outras
                if not value_found:
                    for i, cell in enumerate(row):
                        if cell and self._looks_like_money(str(cell)):
                            transaction.value = self._parse_value(str(cell))
                            value_found = True
                            break
                
                # Saldo
                if 'balance' in col_mapping:
                    balance_str = str(row[col_mapping['balance']] or '').strip()
                    if balance_str:
                        transaction.balance = self._parse_value(balance_str)
                
                # Tipo (crédito/débito)
                transaction.type = 'credit' if transaction.value > 0 else 'debit'
                
                if value_found:  # Só adiciona se encontrou um valor válido
                    transactions.append(transaction)
                    
            except Exception as e:
                continue  # Pula linhas com erro
        
        return transactions
    
    def _looks_like_money(self, text: str) -> bool:
        """Verifica se o texto parece um valor monetário"""
        # Remove espaços e verifica padrões monetários
        text = text.strip()
        patterns = [
            r'^\d+[.,]\d{2}$',  # 123,45
            r'^[\d.,]+$',       # 1.234,56
            r'^\d{1,3}(?:[.,]\d{3})*[.,]\d{2}$'  # 1.234.567,89
        ]
        
        return any(re.match(pattern, text) for pattern in patterns)
    
    def _parse_value(self, value_str: str) -> float:
        """Converte string em valor float"""
        if not value_str:
            return 0.0
        
        # Remove espaços e caracteres especiais
        value_str = value_str.strip().replace('R$', '').replace(' ', '')
        
        # Trata valores negativos (em vermelho no PDF)
        is_negative = value_str.startswith('-') or value_str.startswith('(')
        value_str = value_str.replace('-', '').replace('(', '').replace(')', '')
        
        # Converte formato brasileiro (1.234,56) para float
        if ',' in value_str and '.' in value_str:
            # Formato: 1.234.567,89
            value_str = value_str.replace('.', '').replace(',', '.')
        elif ',' in value_str:
            # Formato: 1234,56
            value_str = value_str.replace(',', '.')
        
        try:
            value = float(value_str)
            return -value if is_negative else value
        except:
            return 0.0
    
    def extract_statement(self) -> BankStatement:
        """Extrai extrato completo"""
        with pdfplumber.open(self.pdf_path) as pdf:
            all_text = ""
            all_transactions = []
            
            for page in pdf.pages:
                text = page.extract_text()
                all_text += text + "\n"
                
                # Extrai tabelas da página
                tables = page.extract_tables()
                for table in tables:
                    transactions = self.extract_transactions_from_table(table)
                    all_transactions.extend(transactions)
            
            # Extrai cabeçalho
            header = self.extract_header_info(all_text)
            
            return BankStatement(header=header, transactions=all_transactions)

def main():
    pdf_file = "data/input/2018_11_extrato_movimento.pdf"
    
    print("=== EXTRAÇÃO MELHORADA ===\n")
    
    extractor = ImprovedBankExtractor(pdf_file)
    statement = extractor.extract_statement()
    
    # Mostra informações do cabeçalho
    print("INFORMAÇÕES DO CABEÇALHO:")
    print(f"- Banco: {statement.header.bank_name}")
    print(f"- Titular: {statement.header.account_holder}")
    print(f"- Conta: {statement.header.account_number}")
    print(f"- Agência: {statement.header.agency}")
    print(f"- Período: {statement.header.period_start} a {statement.header.period_end}")
    
    # Mostra transações
    print(f"\nTRANSAÇÕES ENCONTRADAS: {len(statement.transactions)}")
    
    if statement.transactions:
        df = statement.to_dataframe()
        
        # Salva resultado
        output_file = "data/output/extrato_melhorado.xlsx"
        df.to_excel(output_file, index=False)
        
        print(f"✓ Salvo em: {output_file}")
        
        # Estatísticas
        total_debits = df[df['tipo'] == 'debit']['valor'].sum()
        total_credits = df[df['tipo'] == 'credit']['valor'].sum()
        
        print(f"\nESTATÍSTICAS:")
        print(f"- Total débitos: R$ {abs(total_debits):,.2f}")
        print(f"- Total créditos: R$ {total_credits:,.2f}")
        print(f"- Saldo líquido: R$ {total_credits + total_debits:,.2f}")
        
        print(f"\nPREVIEW:")
        print(df.head(10))
    else:
        print("✗ Nenhuma transação encontrada")

if __name__ == "__main__":
    main()