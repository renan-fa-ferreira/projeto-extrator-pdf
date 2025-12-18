#!/usr/bin/env python3
"""Extractor genérico inteligente para bancos não implementados"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from parsers.base_extractor import BaseExtractor

class GenericSmartExtractor(BaseExtractor):
    """Extractor genérico com múltiplas estratégias"""
    
    def extract_statement(self) -> tuple[pd.DataFrame, dict]:
        """Extração inteligente com múltiplas estratégias"""
        
        strategies = [
            self._extract_table_based,
            self._extract_pattern_based,
            self._extract_line_based
        ]
        
        best_result = pd.DataFrame()
        header_info = {'banco': 'GENÉRICO'}
        
        # Tenta cada estratégia
        for strategy in strategies:
            try:
                df, info = strategy()
                if len(df) > len(best_result):
                    best_result = df
                    header_info.update(info)
            except:
                continue
        
        if not best_result.empty:
            best_result = self.standardize_output(best_result, header_info)
        
        return best_result, header_info
    
    def _extract_table_based(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia baseada em tabelas"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    
                    # Procura header com palavras-chave
                    header_row = None
                    for i, row in enumerate(table):
                        if any(keyword in str(cell).upper() for cell in row if cell
                               for keyword in ['DATA', 'VALOR', 'HISTÓRICO', 'SALDO']):
                            header_row = i
                            break
                    
                    if header_row is None:
                        continue
                    
                    # Mapeia colunas automaticamente
                    header = table[header_row]
                    col_map = self._map_columns(header)
                    
                    # Extrai transações
                    for row in table[header_row + 1:]:
                        transaction = self._extract_transaction_from_row(row, col_map)
                        if transaction:
                            transactions.append(transaction)
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_pattern_based(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia baseada em padrões regex"""
        transactions = []
        header_info = {}
        
        # Padrões comuns de extratos
        patterns = [
            r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,]+)\s+([\d.,]+)',  # Data Desc Valor Saldo
            r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,]+)',  # Data Desc Valor (Safra)
            r'(\d{2}/\d{2})\s+(.+?)\s+(\d+,\d{2})',  # Data Desc Valor simples
            r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+([\d.,]+)',  # Data-Desc-Valor
        ]
        
        with pdfplumber.open(self.pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                
                for match in matches:
                    try:
                        if len(match) >= 3:
                            date_str = match[0]
                            desc = match[1].strip()
                            value_str = match[2]
                            
                            # Normaliza data
                            if len(date_str) == 5:  # DD/MM
                                date_str = f"{date_str}/{datetime.now().year}"
                            
                            date_obj = datetime.strptime(date_str.replace('-', '/'), '%d/%m/%Y')
                            value = float(value_str.replace('.', '').replace(',', '.'))
                            
                            transaction = {
                                'arquivo': Path(self.pdf_path).name,
                                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                'historico': desc,
                                'valor': value,
                                'tipo': 'credit' if value > 0 else 'debit',
                                'banco': 'GENÉRICO'
                            }
                            
                            transactions.append(transaction)
                    except:
                        continue
                
                if transactions:  # Se encontrou com este padrão, para
                    break
        
        return pd.DataFrame(transactions), header_info
    
    def _extract_line_based(self) -> tuple[pd.DataFrame, dict]:
        """Estratégia linha por linha"""
        transactions = []
        header_info = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')
                
                for line in lines:
                    # Procura linhas com data no início
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
            
            if 'DATA' in col_upper or 'LANÇAMENTO' in col_upper:
                col_map['data'] = i
            elif any(x in col_upper for x in ['HISTÓRICO', 'HISTORICO', 'DESCRIÇÃO', 'DESCRICAO', 'COMPLEMENTO']):
                col_map['historico'] = i
            elif 'VALOR' in col_upper and 'R$' in col_upper:
                col_map['valor'] = i
            elif 'SALDO' in col_upper:
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
            
            # Pula linhas de saldo
            if any(x in historico.upper() for x in ['SALDO INICIAL', 'SALDO DISP', 'SALDO ANTERIOR', 'SALDO CONTA']):
                return None
            
            return {
                'arquivo': Path(self.pdf_path).name,
                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                'historico': historico,
                'valor': value,
                'tipo': 'credit' if value > 0 else 'debit',
                'banco': 'GENÉRICO'
            }
            
        except:
            return None
    
    def _parse_line_transaction(self, line):
        """Extrai transação de uma linha de texto"""
        try:
            # Pula linhas de saldo
            if any(x in line.upper() for x in ['SALDO INICIAL', 'SALDO DISP', 'SALDO ANTERIOR']):
                return None
            
            # Padrão Safra: DD/MM DESCRIÇÃO VALOR
            match = re.match(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d+,\d{2})$', line)
            
            if match:
                date_str = match.group(1)
                desc = match.group(2).strip()
                value_str = match.group(3)
                
                # Adiciona ano atual
                date_str = f"{date_str}/{datetime.now().year}"
                
                date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                value = float(value_str.replace(',', '.'))
                
                return {
                    'arquivo': Path(self.pdf_path).name,
                    'data_movimento': date_obj.strftime('%d/%m/%Y'),
                    'historico': desc,
                    'valor': value,
                    'tipo': 'credit' if value > 0 else 'debit',
                    'banco': 'GENÉRICO'
                }
            
            # Padrão geral: data + descrição + valor
            match = re.match(r'^(\d{2}[/-]\d{2}(?:[/-]\d{4})?)\s+(.+?)\s+([\d.,]+)(?:\s|$)', line)
            
            if match:
                date_str = match.group(1)
                desc = match.group(2).strip()
                value_str = match.group(3)
                
                # Normaliza data
                if len(date_str) <= 5:
                    date_str = f"{date_str}/{datetime.now().year}"
                
                date_obj = datetime.strptime(date_str.replace('-', '/'), '%d/%m/%Y')
                value = float(value_str.replace('.', '').replace(',', '.'))
                
                return {
                    'arquivo': Path(self.pdf_path).name,
                    'data_movimento': date_obj.strftime('%d/%m/%Y'),
                    'historico': desc,
                    'valor': value,
                    'tipo': 'credit' if value > 0 else 'debit',
                    'banco': 'GENÉRICO'
                }
        except:
            pass
        
        return None