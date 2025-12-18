#!/usr/bin/env python3
"""Extrator específico para GovConta Caixa"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

def extract_caixa_govconta(pdf_path):
    """Extrai dados do formato GovConta Caixa"""
    
    all_transactions = []
    header_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Extrai cabeçalho (só primeira página)
            if page_num == 1:
                for line in lines[:10]:
                    if 'GovConta CAIXA:' in line:
                        match = re.search(r'GovConta CAIXA:\s*(\d+)', line)
                        if match:
                            header_info['govconta'] = match.group(1)
                    
                    elif 'Conta Referência:' in line:
                        match = re.search(r'Conta Referência:\s*([\d/\-]+)', line)
                        if match:
                            header_info['conta_referencia'] = match.group(1)
                    
                    elif 'Nome:' in line:
                        match = re.search(r'Nome:\s*(.+)', line)
                        if match:
                            header_info['nome'] = match.group(1).strip()
                    
                    elif 'Período:' in line:
                        dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                        if len(dates) >= 2:
                            header_info['periodo_inicio'] = dates[0]
                            header_info['periodo_fim'] = dates[1]
            
            # Processa transações linha por linha
            for line in lines:
                # Padrão: DD/MM/AAAA NNNNNN DESCRIÇÃO VALOR SALDO
                match = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+([\d.,]+[CD])\s+([\d.,]+[CD])$', line)
                
                if match:
                    try:
                        date_str = match.group(1)
                        documento = match.group(2)
                        historico = match.group(3).strip()
                        valor_str = match.group(4)
                        saldo_str = match.group(5)
                        
                        # Pula saldo atualizado
                        if 'Saldo Atualizado' in historico:
                            continue
                        
                        # Converte data
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                        
                        # Processa valor
                        valor_num = re.sub(r'[^\d.,]', '', valor_str)
                        valor = float(valor_num.replace('.', '').replace(',', '.'))
                        
                        # Determina tipo (D=débito, C=crédito)
                        if valor_str.endswith('D'):
                            tipo = 'debit'
                            valor = -valor
                        else:
                            tipo = 'credit'
                        
                        # Processa saldo
                        saldo_num = re.sub(r'[^\d.,]', '', saldo_str)
                        saldo = float(saldo_num.replace('.', '').replace(',', '.'))
                        
                        # Cria transação
                        transaction = {
                            'arquivo': Path(pdf_path).name,
                            'data_movimento': date_obj.strftime('%d/%m/%Y'),
                            'historico': historico,
                            'documento': documento,
                            'valor': valor,
                            'saldo': saldo,
                            'tipo': tipo,
                            'govconta': header_info.get('govconta', ''),
                            'conta_referencia': header_info.get('conta_referencia', ''),
                            'nome': header_info.get('nome', ''),
                            'banco': 'CAIXA ECONÔMICA FEDERAL'
                        }
                        
                        all_transactions.append(transaction)
                        
                    except Exception as e:
                        continue
    
    return pd.DataFrame(all_transactions), header_info

def main():
    input_folder = "data/input"
    
    pdf_files = [f for f in Path(input_folder).glob("*.pdf") if 'caixa' in f.name.lower()]
    
    if not pdf_files:
        print("Nenhum PDF da Caixa encontrado")
        return
    
    print("=== EXTRATOR CAIXA GOVCONTA ===\n")
    
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file.name}")
        
        try:
            df, header = extract_caixa_govconta(str(pdf_file))
            
            if not df.empty:
                output_file = f"data/output/caixa_govconta_{pdf_file.stem}.xlsx"
                df.to_excel(output_file, index=False)
                
                print(f"✓ {len(df)} transações extraídas")
                print(f"✓ Salvo em: {output_file}")
                
                # Informações
                print(f"\nINFORMAÇÕES:")
                print(f"- Nome: {header.get('nome', 'N/A')}")
                print(f"- GovConta: {header.get('govconta', 'N/A')}")
                print(f"- Conta Ref: {header.get('conta_referencia', 'N/A')}")
                print(f"- Período: {header.get('periodo_inicio', '')} a {header.get('periodo_fim', '')}")
                
                # Estatísticas
                creditos = df[df['tipo'] == 'credit']['valor'].sum()
                debitos = abs(df[df['tipo'] == 'debit']['valor'].sum())
                
                print(f"\nESTATÍSTICAS:")
                print(f"- Créditos: R$ {creditos:,.2f}")
                print(f"- Débitos: R$ {debitos:,.2f}")
                print(f"- Saldo final: R$ {df['saldo'].iloc[-1]:,.2f}")
                
                print(f"\nPreview:")
                print(df[['data_movimento', 'historico', 'documento', 'valor', 'saldo']].head())
                
            else:
                print("✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"✗ Erro: {e}")

if __name__ == "__main__":
    main()