#!/usr/bin/env python3
"""Extrator para conta corrente do Bradesco"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

def extract_bradesco_conta_corrente(pdf_path):
    """Extrai dados de conta corrente do Bradesco"""
    
    all_transactions = []
    header_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Extrai informações do cabeçalho
            for line in lines[:15]:
                if 'CNPJ:' in line:
                    # Extrai nome da empresa e CNPJ
                    parts = line.split('|')
                    if len(parts) >= 2:
                        header_info['cliente'] = parts[0].strip()
                        cnpj_part = parts[1].strip()
                        cnpj_match = re.search(r'(\d{3}\.\d{3}\.\d{3}/\d{4}-\d{2})', cnpj_part)
                        if cnpj_match:
                            header_info['cnpj'] = cnpj_match.group(1)
                
                elif 'Ag:' in line and 'CC:' in line and 'Entre' in line:
                    # Extrai agência, conta e período
                    ag_match = re.search(r'Ag:\s*(\d+)', line)
                    cc_match = re.search(r'CC:\s*([\d-]+)', line)
                    periodo_match = re.search(r'Entre\s+(\d{2}/\d{2}/\d{4})\s+e\s+(\d{2}/\d{2}/\d{4})', line)
                    
                    if ag_match:
                        header_info['agencia'] = ag_match.group(1)
                    if cc_match:
                        header_info['conta'] = cc_match.group(1)
                    if periodo_match:
                        header_info['periodo_inicio'] = periodo_match.group(1)
                        header_info['periodo_fim'] = periodo_match.group(2)
                
                elif 'Nome do usuário:' in line:
                    user_match = re.search(r'Nome do usuário:\s*(.+)', line)
                    if user_match:
                        header_info['usuario'] = user_match.group(1).strip()
            
            # Processa transações linha por linha
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Procura por linha com data no início
                date_match = re.match(r'^(\d{2}/\d{2}/\d{4})', line)
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                        
                        # Pula saldo anterior
                        if 'SALDO ANTERIOR' in line.upper():
                            i += 1
                            continue
                        
                        # Extrai resto da linha após a data
                        resto_linha = line[10:].strip()  # Remove data
                        
                        # Procura por valores na linha atual e próximas
                        historico_parts = []
                        documento = ''
                        credito = 0.0
                        debito = 0.0
                        saldo = 0.0
                        
                        # Verifica se tem valores na mesma linha
                        valores_linha = re.findall(r'([\d.,]+)', resto_linha)
                        
                        # Se não tem valores suficientes, procura nas próximas linhas
                        linhas_transacao = [resto_linha]
                        j = i + 1
                        
                        # Coleta linhas até encontrar próxima data ou valores
                        while j < len(lines) and not re.match(r'^\d{2}/\d{2}/\d{4}', lines[j]):
                            if lines[j].strip():
                                linhas_transacao.append(lines[j].strip())
                            j += 1
                        
                        # Junta todas as linhas da transação
                        texto_completo = ' '.join(linhas_transacao)
                        
                        # Procura por padrões de valores
                        # Formato: documento credito debito saldo ou documento valor saldo
                        valores = re.findall(r'([\d.,]+)', texto_completo)
                        
                        if len(valores) >= 2:
                            # Últimos valores são saldo
                            saldo_str = valores[-1].replace('.', '').replace(',', '.')
                            saldo = float(saldo_str)
                            
                            # Penúltimo pode ser crédito ou débito
                            valor_str = valores[-2].replace('.', '').replace(',', '.')
                            valor = float(valor_str)
                            
                            # Determina se é crédito ou débito pela presença de sinal negativo
                            if '-' in texto_completo or 'CHEQUE' in texto_completo.upper():
                                debito = valor
                                tipo = 'debit'
                            else:
                                credito = valor
                                tipo = 'credit'
                            
                            # Documento pode ser o primeiro número
                            if len(valores) >= 3:
                                documento = valores[0]
                            
                            # Histórico é o texto sem os números
                            historico = re.sub(r'[\d.,]+', '', texto_completo).strip()
                            historico = re.sub(r'\s+', ' ', historico)  # Remove espaços extras
                            
                            # Remove caracteres especiais do histórico
                            historico = historico.replace('-', '').strip()
                            
                            # Cria transação
                            transaction = {
                                'arquivo': Path(pdf_path).name,
                                'data_movimento': date_obj.strftime('%d/%m/%Y'),
                                'historico': historico,
                                'documento': documento,
                                'credito': credito if tipo == 'credit' else 0.0,
                                'debito': debito if tipo == 'debit' else 0.0,
                                'saldo': saldo,
                                'tipo': tipo,
                                'cliente': header_info.get('cliente', ''),
                                'cnpj': header_info.get('cnpj', ''),
                                'agencia': header_info.get('agencia', ''),
                                'conta': header_info.get('conta', ''),
                                'periodo_inicio': header_info.get('periodo_inicio', ''),
                                'periodo_fim': header_info.get('periodo_fim', ''),
                                'banco': 'BRADESCO'
                            }
                            
                            all_transactions.append(transaction)
                        
                        # Pula para próxima linha após a transação
                        i = j - 1
                        
                    except Exception as e:
                        pass
                
                i += 1
    
    return pd.DataFrame(all_transactions), header_info

def main():
    input_folder = "data/input"
    
    pdf_files = list(Path(input_folder).glob("*radesco*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF do Bradesco encontrado")
        return
    
    print("=== EXTRATOR BRADESCO CONTA CORRENTE ===\n")
    
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file.name}")
        
        try:
            df, header = extract_bradesco_conta_corrente(str(pdf_file))
            
            if not df.empty:
                # Remove duplicatas e ordena
                df = df.drop_duplicates()
                df['data_obj'] = pd.to_datetime(df['data_movimento'], format='%d/%m/%Y')
                df = df.sort_values('data_obj').drop('data_obj', axis=1)
                
                # Salva resultado
                output_file = f"data/output/bradesco_cc_{pdf_file.stem}.xlsx"
                df.to_excel(output_file, index=False)
                
                print(f"✓ {len(df)} transações extraídas")
                print(f"✓ Salvo em: {output_file}")
                
                # Informações do cabeçalho
                print(f"\nINFORMAÇÕES:")
                print(f"- Cliente: {header.get('cliente', 'N/A')}")
                print(f"- CNPJ: {header.get('cnpj', 'N/A')}")
                print(f"- Agência: {header.get('agencia', 'N/A')}")
                print(f"- Conta: {header.get('conta', 'N/A')}")
                print(f"- Período: {header.get('periodo_inicio', '')} a {header.get('periodo_fim', '')}")
                
                # Estatísticas
                total_creditos = df['credito'].sum()
                total_debitos = df['debito'].sum()
                
                print(f"\nESTATÍSTICAS:")
                print(f"- Total créditos: R$ {total_creditos:,.2f}")
                print(f"- Total débitos: R$ {total_debitos:,.2f}")
                print(f"- Saldo final: R$ {df['saldo'].iloc[-1] if not df.empty else 0:,.2f}")
                
                print(f"\nPreview:")
                print(df[['data_movimento', 'historico', 'documento', 'credito', 'debito', 'saldo']].head())
                
            else:
                print("✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"✗ Erro: {e}")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()