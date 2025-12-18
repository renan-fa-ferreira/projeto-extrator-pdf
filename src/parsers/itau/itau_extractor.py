#!/usr/bin/env python3
"""Extrator específico para extratos do Itaú"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

def extract_itau_statement(pdf_path):
    """Extrai dados específicos do formato Itaú"""
    
    all_transactions = []
    header_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Extrai info do cabeçalho
            for line in lines[:15]:
                if 'ITAÚ' in line.upper() or 'ITAU' in line.upper():
                    header_info['banco'] = line.strip()
                elif 'AGÊNCIA' in line.upper() or 'AG.' in line.upper():
                    match = re.search(r'(\d{4})', line)
                    if match:
                        header_info['agencia'] = match.group(1)
                elif 'CONTA' in line.upper():
                    match = re.search(r'(\d+[-.]?\d*)', line)
                    if match:
                        header_info['conta'] = match.group(1)
            
            # Processa transações linha por linha
            current_year = datetime.now().year
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Procura por padrão: DD/MM + descrição + valores
                date_match = re.match(r'^(\d{2}/\d{2})', line)
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        
                        # Pula saldo anterior e saldo final
                        if any(x in line.upper() for x in ['SALDO ANTERIOR', 'S A L D O']):
                            continue
                        
                        # Adiciona ano atual
                        full_date = f"{date_str}/{current_year}"
                        date_obj = datetime.strptime(full_date, '%d/%m/%Y')
                        
                        # Remove data da linha
                        resto_linha = line[5:].strip()
                        
                        # Procura por valores na linha
                        # Padrão Itaú: descrição + documento + valor + saldo
                        valores = re.findall(r'([\d.,]+)', resto_linha)
                        
                        if len(valores) >= 1:
                            # Último valor antes do hífen é o valor da transação
                            valor_str = valores[-1] if valores else '0'
                            
                            # Remove valores da descrição
                            historico = resto_linha
                            for val in valores:
                                historico = historico.replace(val, '')
                            
                            # Remove caracteres extras
                            historico = re.sub(r'[-\s]+$', '', historico).strip()
                            
                            # Extrai documento se houver
                            documento = ''
                            doc_match = re.search(r'(\d{7,})', resto_linha)
                            if doc_match:
                                documento = doc_match.group(1)
                                historico = historico.replace(documento, '').strip()
                            
                            # Converte valor
                            try:
                                valor_clean = valor_str.replace('.', '').replace(',', '.')
                                valor = float(valor_clean)
                                
                                # Determina tipo baseado no contexto
                                tipo = 'debit'  # Itaú geralmente mostra débitos
                                if any(x in historico.upper() for x in ['CREDITO', 'DEPOSITO', 'VENDA']):
                                    tipo = 'credit'
                                
                                if tipo == 'debit':
                                    valor = -valor
                                
                            except:
                                continue
                            
                            # Procura saldo na próxima linha ou mesma linha
                            saldo = None
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                saldo_match = re.search(r'([\d.,]+)$', next_line)
                                if saldo_match:
                                    try:
                                        saldo_str = saldo_match.group(1).replace('.', '').replace(',', '.')
                                        saldo = float(saldo_str)
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
                                'banco': 'ITAÚ',
                                'periodo': f"{date_str}/{current_year}"
                            }
                            
                            all_transactions.append(transaction)
                            
                    except Exception as e:
                        continue
    
    return pd.DataFrame(all_transactions), header_info

def main():
    input_folder = "data/input"
    
    pdf_files = list(Path(input_folder).glob("*tau*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF do Itaú encontrado")
        return
    
    print("=== EXTRATOR ITAÚ ===\n")
    
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file.name}")
        
        try:
            df, header = extract_itau_statement(str(pdf_file))
            
            if not df.empty:
                # Remove duplicatas e ordena
                df = df.drop_duplicates()
                df['data_obj'] = pd.to_datetime(df['data_movimento'], format='%d/%m/%Y')
                df = df.sort_values('data_obj').drop('data_obj', axis=1)
                
                # Salva resultado
                output_file = f"data/output/itau_{pdf_file.stem}.xlsx"
                df.to_excel(output_file, index=False)
                
                print(f"✓ {len(df)} transações extraídas")
                print(f"✓ Salvo em: {output_file}")
                
                # Estatísticas
                creditos = df[df['tipo'] == 'credit']['valor'].sum()
                debitos = abs(df[df['tipo'] == 'debit']['valor'].sum())
                
                print(f"- Créditos: R$ {creditos:,.2f}")
                print(f"- Débitos: R$ {debitos:,.2f}")
                print(f"- Saldo final: R$ {df['saldo'].iloc[-1] if not df.empty and df['saldo'].notna().any() else 0:,.2f}")
                
                print(f"\nPreview:")
                print(df[['data_movimento', 'historico', 'documento', 'valor', 'tipo']].head())
                
            else:
                print("✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"✗ Erro: {e}")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()