#!/usr/bin/env python3
"""Extrator específico para extratos da Caixa Econômica Federal"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

def extract_caixa_statement(pdf_path):
    """Extrai dados específicos do formato Caixa"""
    
    all_transactions = []
    header_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Extrai info do cabeçalho
            for line in lines[:20]:
                if any(x in line.upper() for x in ['CAIXA', 'CEF']):
                    header_info['banco'] = 'CAIXA ECONÔMICA FEDERAL'
                elif 'Agência' in line and 'Op' in line:
                    # Formato: Agência: 1234 Op: 013 Conta: 12345-6
                    ag_match = re.search(r'Agência[:\s]*(\d+)', line)
                    op_match = re.search(r'Op[:\s]*(\d+)', line)
                    conta_match = re.search(r'Conta[:\s]*([\d-]+)', line)
                    
                    if ag_match:
                        header_info['agencia'] = ag_match.group(1)
                    if op_match:
                        header_info['operacao'] = op_match.group(1)
                    if conta_match:
                        header_info['conta'] = conta_match.group(1)
                
                elif 'Período:' in line or 'PERÍODO:' in line:
                    dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                    if len(dates) >= 2:
                        header_info['periodo_inicio'] = dates[0]
                        header_info['periodo_fim'] = dates[1]
            
            # Processa tabelas
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # Procura header de transações
                header_row = None
                for i, row in enumerate(table):
                    if any(keyword in str(cell).upper() for cell in row if cell
                           for keyword in ['DATA', 'HISTÓRICO', 'VALOR', 'SALDO']):
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
                    
                    if 'DATA' in col_upper:
                        col_map['data'] = j
                    elif any(x in col_upper for x in ['HISTÓRICO', 'HISTORICO', 'DESCRIÇÃO']):
                        col_map['historico'] = j
                    elif 'DOCUMENTO' in col_upper or 'DOC' in col_upper:
                        col_map['documento'] = j
                    elif 'VALOR' in col_upper:
                        col_map['valor'] = j
                    elif 'SALDO' in col_upper:
                        col_map['saldo'] = j
                
                # Processa transações
                for row in table[header_row + 1:]:
                    if not row or len(row) < 3:
                        continue
                    
                    try:
                        # Data
                        if 'data' not in col_map:
                            continue
                        
                        date_str = str(row[col_map['data']] or '').strip()
                        if not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                            continue
                        
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                        
                        # Histórico
                        historico = ''
                        if 'historico' in col_map:
                            historico = str(row[col_map['historico']] or '').strip()
                        
                        # Pula saldos
                        if any(x in historico.upper() for x in ['SALDO ANTERIOR', 'SALDO ATUAL']):
                            continue
                        
                        # Documento
                        documento = ''
                        if 'documento' in col_map:
                            documento = str(row[col_map['documento']] or '').strip()
                        
                        # Valor
                        valor = 0.0
                        tipo = 'debit'
                        
                        if 'valor' in col_map and row[col_map['valor']]:
                            valor_str = str(row[col_map['valor']]).strip()
                            
                            # Remove caracteres especiais
                            valor_clean = re.sub(r'[^\d.,-]', '', valor_str)
                            
                            # Detecta tipo
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
                        if 'saldo' in col_map and row[col_map['saldo']]:
                            saldo_str = str(row[col_map['saldo']]).strip()
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
                            'arquivo': Path(pdf_path).name,
                            'data_movimento': date_obj.strftime('%d/%m/%Y'),
                            'historico': historico,
                            'documento': documento,
                            'valor': valor,
                            'saldo': saldo,
                            'tipo': tipo,
                            'conta': header_info.get('conta', ''),
                            'agencia': header_info.get('agencia', ''),
                            'operacao': header_info.get('operacao', ''),
                            'banco': 'CAIXA ECONÔMICA FEDERAL'
                        }
                        
                        all_transactions.append(transaction)
                        
                    except Exception as e:
                        continue
            
            # Fallback: processa linha por linha se não encontrou tabelas
            if not all_transactions:
                for line in lines:
                    if re.match(r'^\d{2}/\d{2}/\d{4}', line):
                        transaction = parse_caixa_line(line, header_info, pdf_path)
                        if transaction:
                            all_transactions.append(transaction)
    
    return pd.DataFrame(all_transactions), header_info

def parse_caixa_line(line, header_info, pdf_path):
    """Parseia linha individual da Caixa"""
    try:
        # Padrão: DD/MM/AAAA DESCRIÇÃO VALOR SALDO
        match = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,-]+)\s+([\d.,-]+)$', line)
        
        if match:
            date_str = match.group(1)
            desc = match.group(2).strip()
            valor_str = match.group(3)
            saldo_str = match.group(4)
            
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            
            # Converte valores
            valor = float(valor_str.replace('.', '').replace(',', '.'))
            saldo = float(saldo_str.replace('.', '').replace(',', '.'))
            
            # Determina tipo
            tipo = 'credit' if valor > 0 else 'debit'
            
            return {
                'arquivo': Path(pdf_path).name,
                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                'historico': desc,
                'documento': '',
                'valor': valor,
                'saldo': saldo,
                'tipo': tipo,
                'conta': header_info.get('conta', ''),
                'agencia': header_info.get('agencia', ''),
                'operacao': header_info.get('operacao', ''),
                'banco': 'CAIXA ECONÔMICA FEDERAL'
            }
    except:
        pass
    
    return None

def main():
    input_folder = "data/input"
    
    pdf_files = [f for f in Path(input_folder).glob("*.pdf") if 'caixa' in f.name.lower()]
    
    if not pdf_files:
        print("Nenhum PDF da Caixa encontrado")
        return
    
    print("=== EXTRATOR CAIXA ===\n")
    
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file.name}")
        
        try:
            df, header = extract_caixa_statement(str(pdf_file))
            
            if not df.empty:
                output_file = f"data/output/caixa_{pdf_file.stem}.xlsx"
                df.to_excel(output_file, index=False)
                
                print(f"✓ {len(df)} transações extraídas")
                print(f"✓ Salvo em: {output_file}")
                
                # Estatísticas
                creditos = df[df['tipo'] == 'credit']['valor'].sum()
                debitos = abs(df[df['tipo'] == 'debit']['valor'].sum())
                
                print(f"- Créditos: R$ {creditos:,.2f}")
                print(f"- Débitos: R$ {debitos:,.2f}")
                
                print(f"\nPreview:")
                print(df[['data_movimento', 'historico', 'valor', 'saldo']].head())
                
            else:
                print("✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"✗ Erro: {e}")

if __name__ == "__main__":
    main()