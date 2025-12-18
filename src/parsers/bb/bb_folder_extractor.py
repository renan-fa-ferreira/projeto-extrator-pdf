#!/usr/bin/env python3
"""Extrator para todos os PDFs da pasta input"""

import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
from pathlib import Path

def extract_bb_statement(pdf_path):
    """Extrai dados específicos do formato BB"""
    
    all_transactions = []
    contas_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Extrai info específica desta página
            page_info = {}
            
            for line in lines[:15]:
                if 'BANCO' in line and '001' in line:
                    page_info['banco'] = line.strip()
                elif 'Agência' in line:
                    match = re.search(r'(\d+-\d+)', line)
                    if match:
                        page_info['agencia'] = match.group(1)
                elif 'Conta corrente' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if re.match(r'\d+-\w+', part):
                            page_info['conta'] = part
                            page_info['nome_conta'] = ' '.join(parts[i+1:])
                            break
                elif 'Período do extrato' in line:
                    match = re.search(r'(\d+/\d+)', line)
                    if match:
                        page_info['periodo'] = match.group(1)
            
            # Armazena info da conta se encontrou
            if 'conta' in page_info:
                contas_info[page_info['conta']] = page_info
            
            # Processa tabelas
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # Verifica se é tabela de transações
                header_row = None
                for i, row in enumerate(table):
                    if any('Dt. movimento' in str(cell) for cell in row if cell):
                        header_row = i
                        break
                
                if header_row is None:
                    continue
                
                # Processa transações
                for row in table[header_row + 1:]:
                    if not row or len(row) < 4:
                        continue
                    
                    # Pula linhas de cabeçalho ou vazias
                    if any(x in str(row[0] or '') for x in ['Dt. movimento', 'Lançamentos']):
                        continue
                    
                    try:
                        # Data movimento (primeira coluna)
                        date_str = str(row[0] or '').strip()
                        if not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                            continue
                        
                        date_mov = datetime.strptime(date_str, '%d/%m/%Y')
                        
                        # Histórico (coluna 3, índice 3)
                        historico = str(row[3] or '').strip()
                        if not historico or historico in ['', 'None']:
                            continue
                        
                        # Pula linhas de saldo anterior e saldo final
                        if any(x in historico.upper() for x in ['SALDO ANTERIOR', 'S A L D O']):
                            continue
                        
                        # Documento (coluna 4, índice 4)
                        documento = str(row[4] or '').strip()
                        if documento == 'None':
                            documento = ''
                        
                        # Procura valor em múltiplas colunas
                        valor = 0.0
                        tipo = 'debit'
                        valor_encontrado = False
                        
                        # Verifica colunas 5 e 6 para valores
                        for col_idx in [5, 6]:
                            if col_idx < len(row) and row[col_idx]:
                                cell_value = str(row[col_idx]).strip()
                                
                                # Procura padrão: número + C/D
                                matches = re.findall(r'([\d.,]+)\s*([CD])', cell_value)
                                
                                for match in matches:
                                    valor_num = match[0]
                                    cd_flag = match[1]
                                    
                                    # Converte valor brasileiro para float
                                    if '.' in valor_num and ',' in valor_num:
                                        # Formato: 1.234.567,89
                                        valor_num = valor_num.replace('.', '').replace(',', '.')
                                    elif ',' in valor_num:
                                        # Formato: 1234,89
                                        valor_num = valor_num.replace(',', '.')
                                    
                                    try:
                                        valor = float(valor_num)
                                        tipo = 'credit' if cd_flag == 'C' else 'debit'
                                        if tipo == 'debit':
                                            valor = -valor
                                        valor_encontrado = True
                                        break
                                    except:
                                        continue
                                
                                if valor_encontrado:
                                    break
                        
                        if not valor_encontrado:
                            continue
                        
                        # Saldo (coluna 6, índice 6)
                        saldo = None
                        if len(row) > 6 and row[6] and str(row[6]) != 'None':
                            saldo_str = str(row[6]).strip()
                            match = re.search(r'([\d.,]+)\s*([CD])', saldo_str)
                            if match:
                                try:
                                    saldo_num = match.group(1)
                                    if '.' in saldo_num and ',' in saldo_num:
                                        saldo_num = saldo_num.replace('.', '').replace(',', '.')
                                    elif ',' in saldo_num:
                                        saldo_num = saldo_num.replace(',', '.')
                                    saldo = float(saldo_num)
                                except:
                                    pass
                        
                        # Adiciona transação com info da página atual
                        transaction = {
                            'arquivo': Path(pdf_path).name,
                            'data_movimento': date_mov.strftime('%d/%m/%Y'),
                            'historico': historico,
                            'documento': documento,
                            'valor': valor,
                            'saldo': saldo,
                            'tipo': tipo,
                            'conta': page_info.get('conta', ''),
                            'nome_conta': page_info.get('nome_conta', ''),
                            'agencia': page_info.get('agencia', ''),
                            'periodo': page_info.get('periodo', ''),
                            'banco': page_info.get('banco', '')
                        }
                        
                        all_transactions.append(transaction)
                        
                    except Exception as e:
                        continue
    
    return pd.DataFrame(all_transactions), contas_info

def process_all_pdfs(input_folder):
    """Processa todos os PDFs da pasta"""
    
    pdf_files = list(Path(input_folder).glob("*.pdf"))
    
    if not pdf_files:
        print(f"Nenhum arquivo PDF encontrado em: {input_folder}")
        return
    
    print(f"Encontrados {len(pdf_files)} arquivos PDF:")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    all_transactions = []
    all_contas = {}
    
    for pdf_file in pdf_files:
        print(f"\nProcessando: {pdf_file.name}")
        
        try:
            df, contas_info = extract_bb_statement(str(pdf_file))
            
            if not df.empty:
                all_transactions.append(df)
                all_contas.update(contas_info)
                print(f"  ✓ {len(df)} transações extraídas")
            else:
                print(f"  ✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"  ✗ Erro: {e}")
    
    if not all_transactions:
        print("\nNenhuma transação foi extraída dos arquivos.")
        return
    
    # Combina todos os DataFrames
    final_df = pd.concat(all_transactions, ignore_index=True)
    
    # Remove duplicatas
    final_df = final_df.drop_duplicates()
    
    # Ordena por arquivo e data
    final_df['data_obj'] = pd.to_datetime(final_df['data_movimento'], format='%d/%m/%Y')
    final_df = final_df.sort_values(['arquivo', 'data_obj']).drop('data_obj', axis=1)
    
    return final_df, all_contas

def main():
    input_folder = "data/input"
    
    print("=== EXTRATOR BB - PASTA COMPLETA ===\n")
    
    final_df, all_contas = process_all_pdfs(input_folder)
    
    if final_df is None or final_df.empty:
        return
    
    print(f"\n=== RESUMO FINAL ===")
    print(f"Total de transações: {len(final_df)}")
    
    # Salva resultado
    output_file = "data/output/extratos_completos.xlsx"
    final_df.to_excel(output_file, index=False)
    print(f"✓ Salvo em: {output_file}")
    
    # Estatísticas por arquivo
    print(f"\nPOR ARQUIVO:")
    for arquivo in final_df['arquivo'].unique():
        df_arquivo = final_df[final_df['arquivo'] == arquivo]
        creditos = df_arquivo[df_arquivo['tipo'] == 'credit']['valor'].sum()
        debitos = abs(df_arquivo[df_arquivo['tipo'] == 'debit']['valor'].sum())
        
        print(f"\n{arquivo}:")
        print(f"  - Transações: {len(df_arquivo)}")
        print(f"  - Créditos: R$ {creditos:,.2f}")
        print(f"  - Débitos: R$ {debitos:,.2f}")
    
    # Estatísticas por conta
    print(f"\nPOR CONTA:")
    for conta in final_df['conta'].unique():
        if pd.isna(conta) or conta == '':
            continue
        df_conta = final_df[final_df['conta'] == conta]
        creditos = df_conta[df_conta['tipo'] == 'credit']['valor'].sum()
        debitos = abs(df_conta[df_conta['tipo'] == 'debit']['valor'].sum())
        
        print(f"\n{conta} - {df_conta['nome_conta'].iloc[0] if not df_conta.empty else ''}:")
        print(f"  - Transações: {len(df_conta)}")
        print(f"  - Créditos: R$ {creditos:,.2f}")
        print(f"  - Débitos: R$ {debitos:,.2f}")

if __name__ == "__main__":
    main()