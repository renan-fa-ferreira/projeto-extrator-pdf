#!/usr/bin/env python3
"""Script avançado com múltiplas estratégias de extração"""

import pdfplumber
import fitz  # PyMuPDF
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

class AdvancedPDFExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.results = {}
    
    def extract_with_pdfplumber(self):
        """Extração usando pdfplumber com análise de layout"""
        transactions = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Tenta extrair tabelas primeiro
                tables = page.extract_tables()
                
                if tables:
                    for table in tables:
                        for row in table:
                            if self._is_transaction_row(row):
                                trans = self._parse_transaction_row(row)
                                if trans:
                                    transactions.append(trans)
                
                # Se não encontrou tabelas, usa texto
                if not transactions:
                    text = page.extract_text()
                    transactions.extend(self._extract_from_text(text))
        
        self.results['pdfplumber'] = transactions
        return transactions
    
    def extract_with_pymupdf(self):
        """Extração usando PyMuPDF"""
        transactions = []
        
        doc = fitz.open(self.pdf_path)
        
        for page in doc:
            # Tenta extrair tabelas estruturadas
            tabs = page.find_tables()
            
            for tab in tabs:
                table_data = tab.extract()
                for row in table_data:
                    if self._is_transaction_row(row):
                        trans = self._parse_transaction_row(row)
                        if trans:
                            transactions.append(trans)
            
            # Se não encontrou, usa texto
            if not transactions:
                text = page.get_text()
                transactions.extend(self._extract_from_text(text))
        
        doc.close()
        self.results['pymupdf'] = transactions
        return transactions
    
    def _is_transaction_row(self, row):
        """Verifica se a linha contém uma transação"""
        if not row or len(row) < 2:
            return False
        
        row_str = ' '.join([str(cell) for cell in row if cell])
        
        # Procura por padrões de data e valor
        has_date = bool(re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', row_str))
        has_value = bool(re.search(r'\d+[.,]\d{2}', row_str))
        
        return has_date and has_value
    
    def _parse_transaction_row(self, row):
        """Converte linha em transação"""
        try:
            row_str = ' '.join([str(cell) for cell in row if cell])
            
            # Extrai data
            date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', row_str)
            if not date_match:
                return None
            
            date = datetime.strptime(date_match.group(1).replace('-', '/'), '%d/%m/%Y')
            
            # Extrai valor
            value_matches = re.findall(r'([+-]?\d+[.,]\d{2})', row_str)
            if not value_matches:
                return None
            
            # Pega o último valor (geralmente é o valor da transação)
            value = float(value_matches[-1].replace(',', '.').replace('+', ''))
            
            # Extrai descrição
            desc = row_str
            desc = re.sub(r'\d{2}[/-]\d{2}[/-]\d{4}', '', desc)
            desc = re.sub(r'[+-]?\d+[.,]\d{2}', '', desc)
            desc = ' '.join(desc.split())
            
            return {
                'data': date.strftime('%d/%m/%Y'),
                'valor': value,
                'descricao': desc,
                'tipo': 'credito' if value > 0 else 'debito'
            }
        except:
            return None
    
    def _extract_from_text(self, text):
        """Extrai transações do texto bruto"""
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            if self._is_transaction_row([line]):
                trans = self._parse_transaction_row([line])
                if trans:
                    transactions.append(trans)
        
        return transactions
    
    def extract_all(self):
        """Executa todas as estratégias e retorna a melhor"""
        strategies = [
            ('pdfplumber', self.extract_with_pdfplumber),
            ('pymupdf', self.extract_with_pymupdf)
        ]
        
        best_result = []
        best_count = 0
        best_method = None
        
        for name, method in strategies:
            try:
                result = method()
                if len(result) > best_count:
                    best_result = result
                    best_count = len(result)
                    best_method = name
                    
                print(f"{name}: {len(result)} transações")
            except Exception as e:
                print(f"{name}: Erro - {e}")
        
        print(f"\nMelhor resultado: {best_method} com {best_count} transações")
        return best_result, best_method

def main():
    pdf_file = "data/input/2018_11_extrato_movimento.pdf"
    
    if not Path(pdf_file).exists():
        print(f"Arquivo não encontrado: {pdf_file}")
        return
    
    print("=== EXTRAÇÃO AVANÇADA DE PDF ===\n")
    
    extractor = AdvancedPDFExtractor(pdf_file)
    transactions, method = extractor.extract_all()
    
    if transactions:
        df = pd.DataFrame(transactions)
        
        # Salva resultado
        output_file = f"data/output/extrato_avancado_{method}.xlsx"
        df.to_excel(output_file, index=False)
        
        print(f"\n✓ Arquivo salvo: {output_file}")
        print(f"✓ Total de transações: {len(df)}")
        
        # Estatísticas
        print(f"\nEstatísticas:")
        print(f"- Débitos: {len(df[df['tipo'] == 'debito'])}")
        print(f"- Créditos: {len(df[df['tipo'] == 'credito'])}")
        print(f"- Valor total: R$ {df['valor'].sum():.2f}")
        
        print(f"\nPreview:")
        print(df.head())
    else:
        print("✗ Nenhuma transação encontrada")

if __name__ == "__main__":
    main()