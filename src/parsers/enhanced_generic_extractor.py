#!/usr/bin/env python3
"""Extrator genérico aprimorado para bancos específicos"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from parsers.base_extractor import BaseExtractor

class EnhancedGenericExtractor(BaseExtractor):
    """Extrator genérico com estratégias específicas para Safra, Daycoval, BV, Citi"""
    
    def __init__(self, pdf_path: str, bank_name: str = "GENÉRICO"):
        super().__init__(pdf_path)
        self.bank_name = bank_name
        
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extração inteligente baseada no banco"""
        
        strategies = [
            self._extract_safra_format,
            self._extract_daycoval_format,
            self._extract_bv_format,
            self._extract_citi_format,
            self._extract_table_based,
            self._extract_line_based
        ]
        
        best_result = pd.DataFrame()
        header_info = {'banco': self.bank_name}
        
        for strategy in strategies:
            try:
                df, info = strategy()
                if len(df) > len(best_result):
                    best_result = df
                    header_info.update(info)
            except Exception as e:
                continue
        
        if not best_result.empty:
            best_result = self.standardize_output(best_result, header_info)
        
        return best_result, header_info
    
    def _extract_safra_format(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia específica para Safra"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Extrai cabeçalho Safra
                for line in lines[:10]:
                    if 'SAFRA' in line.upper():
                        header_info['banco'] = 'BANCO SAFRA'
                    elif 'CONTA' in line.upper() and re.search(r'\d+', line):
                        header_info['conta'] = re.search(r'(\d+[-.]?\d*)', line).group(1)
                
                # Processa transações formato Safra: DD/MM DESCRIÇÃO VALOR
                for line in lines:
                    # Pula linhas de saldo
                    if any(x in line.upper() for x in ['SALDO INICIAL', 'SALDO DISP', 'SALDO ANTERIOR', 'SALDO CONTA']):
                        continue
                    
                    # Padrão Safra: DD/MM + descrição + valor
                    match = re.match(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d+,\d{2})$', line.strip())
                    
                    if match:
                        try:
                            date_str = f"{match.group(1)}/{datetime.now().year}"
                            desc = match.group(2).strip()
                            value_str = match.group(3)
                            
                            # Pula se descrição contém palavras de saldo
                            if any(x in desc.upper() for x in ['SALDO', 'DISPONIVEL']):
                                continue
                            
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            value = float(value_str.replace(',', '.'))
                            
                            transaction = {
                                'arquivo': Path(self.pdf_path).name,
                                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                'historico': desc,
                                'documento': '',
                                'valor': value,
                                'saldo': None,
                                'tipo': 'credit' if value > 0 else 'debit',
                                'banco': 'BANCO SAFRA'
                            }
                            
                            transactions.append(transaction)
                            
                        except:
                            continue
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_daycoval_format(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia específica para Daycoval"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Extrai cabeçalho Daycoval
                for line in lines[:15]:
                    if 'DAYCOVAL' in line.upper():
                        header_info['banco'] = 'BANCO DAYCOVAL'
                    elif 'AGÊNCIA' in line.upper() or 'AG.' in line.upper():
                        match = re.search(r'(\d+)', line)
                        if match:
                            header_info['agencia'] = match.group(1)
                
                # Processa tabelas
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Procura header
                    header_row = None
                    for i, row in enumerate(table):
                        if any('DATA' in str(cell).upper() for cell in row if cell):
                            header_row = i
                            break
                    
                    if header_row is None:
                        continue
                    
                    # Processa linhas
                    for row in table[header_row + 1:]:
                        if not row or len(row) < 3:
                            continue
                        
                        try:
                            # Data na primeira coluna
                            date_str = str(row[0] or '').strip()
                            if not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                                continue
                            
                            # Descrição e valor nas outras colunas
                            desc_parts = []
                            value = 0.0
                            
                            for cell in row[1:]:
                                if cell and str(cell).strip():
                                    cell_str = str(cell).strip()
                                    
                                    # Se parece com valor
                                    if re.match(r'[\d.,]+$', cell_str):
                                        try:
                                            value = float(cell_str.replace('.', '').replace(',', '.'))
                                        except:
                                            desc_parts.append(cell_str)
                                    else:
                                        desc_parts.append(cell_str)
                            
                            if value != 0.0:
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                                desc = ' '.join(desc_parts)
                                
                                transaction = {
                                    'arquivo': Path(self.pdf_path).name,
                                    'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                    'historico': desc,
                                    'documento': '',
                                    'valor': value,
                                    'saldo': None,
                                    'tipo': 'credit' if value > 0 else 'debit',
                                    'banco': 'BANCO DAYCOVAL'
                                }
                                
                                transactions.append(transaction)
                                
                        except:
                            continue
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_bv_format(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia específica para BV (ex-Votorantim)"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Extrai cabeçalho BV
                for line in lines[:15]:
                    if any(x in line.upper() for x in ['BANCO BV', 'BV S/A', 'VOTORANTIM']):
                        header_info['banco'] = 'BANCO BV'
                
                # Processa linha por linha - formato BV
                for line in lines:
                    # Padrão BV: DD/MM/AAAA ou DD/MM + descrição + valor
                    patterns = [
                        r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)$',
                        r'^(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)$'
                    ]
                    
                    for pattern in patterns:
                        match = re.match(pattern, line.strip())
                        if match:
                            try:
                                date_str = match.group(1)
                                desc = match.group(2).strip()
                                value_str = match.group(3)
                                
                                # Pula saldos
                                if any(x in desc.upper() for x in ['SALDO', 'DISPONIVEL']):
                                    continue
                                
                                # Normaliza data
                                if len(date_str) == 5:
                                    date_str = f"{date_str}/{datetime.now().year}"
                                
                                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                                
                                # Converte valor
                                value_clean = value_str.replace('.', '').replace(',', '.')
                                value = float(value_clean)
                                
                                transaction = {
                                    'arquivo': Path(self.pdf_path).name,
                                    'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                    'historico': desc,
                                    'documento': '',
                                    'valor': value,
                                    'saldo': None,
                                    'tipo': 'credit' if value > 0 else 'debit',
                                    'banco': 'BANCO BV'
                                }
                                
                                transactions.append(transaction)
                                break
                                
                            except:
                                continue
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_citi_format(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia específica para Citibank"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Extrai cabeçalho Citi
                for line in lines[:15]:
                    if any(x in line.upper() for x in ['CITIBANK', 'CITI']):
                        header_info['banco'] = 'CITIBANK'
                
                # Processa tabelas (Citi geralmente usa tabelas)
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Procura header com padrões Citi
                    header_row = None
                    for i, row in enumerate(table):
                        if any(keyword in str(cell).upper() for cell in row if cell
                               for keyword in ['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE']):
                            header_row = i
                            break
                    
                    if header_row is None:
                        continue
                    
                    # Mapeia colunas
                    header = table[header_row]
                    col_map = {}
                    
                    for j, col in enumerate(header):
                        if not col:
                            continue
                        col_upper = str(col).upper()
                        
                        if 'DATE' in col_upper:
                            col_map['data'] = j
                        elif any(x in col_upper for x in ['DESCRIPTION', 'TRANSACTION']):
                            col_map['historico'] = j
                        elif 'AMOUNT' in col_upper:
                            col_map['valor'] = j
                        elif 'BALANCE' in col_upper:
                            col_map['saldo'] = j
                    
                    # Processa transações
                    for row in table[header_row + 1:]:
                        if not row or len(row) < 3:
                            continue
                        
                        try:
                            if 'data' not in col_map or 'valor' not in col_map:
                                continue
                            
                            # Data
                            date_str = str(row[col_map['data']] or '').strip()
                            if not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                                continue
                            
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            
                            # Histórico
                            historico = ''
                            if 'historico' in col_map:
                                historico = str(row[col_map['historico']] or '').strip()
                            
                            # Valor
                            value_str = str(row[col_map['valor']] or '').strip()
                            value = float(re.sub(r'[^\d.,-]', '', value_str).replace(',', '.'))
                            
                            # Saldo
                            saldo = None
                            if 'saldo' in col_map and row[col_map['saldo']]:
                                saldo_str = str(row[col_map['saldo']]).strip()
                                try:
                                    saldo = float(re.sub(r'[^\d.,-]', '', saldo_str).replace(',', '.'))
                                except:
                                    pass
                            
                            transaction = {
                                'arquivo': Path(self.pdf_path).name,
                                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                'historico': historico,
                                'documento': '',
                                'valor': value,
                                'saldo': saldo,
                                'tipo': 'credit' if value > 0 else 'debit',
                                'banco': 'CITIBANK'
                            }
                            
                            transactions.append(transaction)
                            
                        except:
                            continue
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_table_based(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia genérica baseada em tabelas"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Procura header
                    header_row = None
                    for i, row in enumerate(table):
                        if any(keyword in str(cell).upper() for cell in row if cell
                               for keyword in ['DATA', 'VALOR', 'HISTÓRICO', 'SALDO']):
                            header_row = i
                            break
                    
                    if header_row is None:
                        continue
                    
                    # Mapeia e processa
                    col_map = self._map_columns(table[header_row])
                    
                    for row in table[header_row + 1:]:
                        transaction = self._extract_transaction_from_row(row, col_map)
                        if transaction:
                            transactions.append(transaction)
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_line_based(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia genérica linha por linha"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                for line in lines:
                    if re.match(r'^\d{2}[/-]\d{2}', line):
                        transaction = self._parse_line_transaction(line)
                        if transaction:
                            transactions.append(transaction)
        
        return pd.DataFrame(transactions), header_info
    
    def _map_columns(self, header):
        """Mapeia colunas automaticamente"""
        col_map = {}
        
        for i, col in enumerate(header):
            if not col:
                continue
            col_upper = str(col).upper()
            
            if any(x in col_upper for x in ['DATA', 'DATE', 'LANÇAMENTO']):
                col_map['data'] = i
            elif any(x in col_upper for x in ['HISTÓRICO', 'HISTORICO', 'DESCRIÇÃO', 'DESCRIPTION']):
                col_map['historico'] = i
            elif 'VALOR' in col_upper or 'AMOUNT' in col_upper:
                col_map['valor'] = i
            elif 'SALDO' in col_upper or 'BALANCE' in col_upper:
                col_map['saldo'] = i
            elif any(x in col_upper for x in ['DOCUMENTO', 'DOC', 'NÚMERO']):
                col_map['documento'] = i
        
        return col_map
    
    def _extract_transaction_from_row(self, row, col_map):
        """Extrai transação de uma linha da tabela"""
        try:
            if 'data' not in col_map or 'valor' not in col_map:
                return None
            
            date_str = str(row[col_map['data']] or '').strip()
            if not re.match(r'\d{2}[/-]\d{2}', date_str):
                return None
            
            # Normaliza data
            if len(date_str) <= 5:
                date_str = f"{date_str}/{datetime.now().year}"
            
            date_obj = datetime.strptime(date_str.replace('-', '/'), '%d/%m/%Y')
            
            # Valor
            value_str = str(row[col_map['valor']] or '').strip()
            value = float(re.sub(r'[^\d.,-]', '', value_str).replace(',', '.'))
            
            # Histórico
            historico = ''
            if 'historico' in col_map:
                historico = str(row[col_map['historico']] or '').strip()
            
            # Pula saldos
            if any(x in historico.upper() for x in ['SALDO INICIAL', 'SALDO ANTERIOR']):
                return None
            
            return {
                'arquivo': Path(self.pdf_path).name,
                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                'historico': historico,
                'valor': value,
                'tipo': 'credit' if value > 0 else 'debit',
                'banco': self.bank_name
            }
            
        except:
            return None
    
    def _parse_line_transaction(self, line):
        """Extrai transação de uma linha de texto"""
        try:
            # Pula saldos
            if any(x in line.upper() for x in ['SALDO INICIAL', 'SALDO ANTERIOR']):
                return None
            
            # Múltiplos padrões
            patterns = [
                r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)$',
                r'^(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)$'
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    date_str = match.group(1)
                    desc = match.group(2).strip()
                    value_str = match.group(3)
                    
                    # Normaliza data
                    if len(date_str) <= 5:
                        date_str = f"{date_str}/{datetime.now().year}"
                    
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                    value = float(value_str.replace('.', '').replace(',', '.'))
                    
                    return {
                        'arquivo': Path(self.pdf_path).name,
                        'data_movimento': date_obj.strftime('%d/%m/%Y'),
                        'historico': desc,
                        'valor': value,
                        'tipo': 'credit' if value > 0 else 'debit',
                        'banco': self.bank_name
                    }
        except:
            pass
        
        return None