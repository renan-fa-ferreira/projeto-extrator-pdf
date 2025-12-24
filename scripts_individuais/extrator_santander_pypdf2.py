#!/usr/bin/env python3
"""Extrator Santander usando PyPDF2 - versão final"""

import PyPDF2
import pandas as pd
import re
from pathlib import Path

def extract_santander_pypdf2(pdf_path):
    """Extrai transações do Santander usando PyPDF2"""
    transactions = []
    total_lines_with_date = 0
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        # Metadados
        first_page_text = reader.pages[0].extract_text()
        agencia_match = re.search(r'AGENCIA\s+(\d+)', first_page_text)
        conta_match = re.search(r'CONTA\s+(\d+)', first_page_text)
        
        agencia = agencia_match.group(1) if agencia_match else ""
        conta = conta_match.group(1) if conta_match else ""
        
        for page in reader.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or "SALDO ANTERIOR" in line:
                    continue
                
                date_match = re.match(r'^(\d{2}/\d{2}/\d{4})\s+(.+)', line)
                if date_match:
                    total_lines_with_date += 1
                    data = date_match.group(1)
                    resto = date_match.group(2)
                    
                    # Padrão: DESCRIÇÃO VALOR SALDO (valores com 1 ou 2 casas decimais)
                    valores_match = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{1,2})', resto)
                    
                    if len(valores_match) >= 1:
                        # Primeiro valor sempre é o valor da transação
                        valor_str = valores_match[0]
                        saldo_str = valores_match[1] if len(valores_match) >= 2 else '0,00'
                        # Descrição é tudo antes do primeiro valor
                        desc_end = resto.find(valor_str)
                        descricao = resto[:desc_end].strip()
                    else:
                        continue
                    
                    descricao = re.sub(r'\s+', ' ', descricao)
                    
                    if len(descricao) >= 3:
                        try:
                            valor = float(valor_str.replace('.', '').replace(',', '.'))
                            tipo = 'D' if '-' in descricao else 'C'
                            
                            # Ajuste: Pagamentos de cartão são sempre tipo C
                            if 'PAGAMENTO CARTAO' in descricao.upper():
                                tipo = 'C'
                            
                            transactions.append({
                                'Banco': 'Banco Santander',
                                'Codigo Banco': '033',
                                'Agencia': agencia,
                                'Conta': conta,
                                'Data': data,
                                'Documento': '',
                                'Descricao': descricao.replace('-', '').strip(),
                                'Valor': f"{valor:.2f}".replace('.', ','),
                                'Tipo': tipo,
                                'Saldo': saldo_str,
                                'Arquivo': pdf_path.name
                            })
                        except ValueError:
                            continue
    
    return transactions, len(reader.pages), total_lines_with_date

def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    output_dir = script_dir.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF encontrado em data/input/")
        return
    
    all_transactions = []
    logs = []
    
    for pdf_path in pdf_files:
        print(f"Processando: {pdf_path.name}")
        try:
            transactions, total_pages, total_lines_with_date = extract_santander_pypdf2(pdf_path)
            
            logs.append({
                'arquivo': pdf_path.name,
                'paginas': total_pages,
                'total_lido': total_lines_with_date,
                'total_extraido': len(transactions),
                'total_creditos': len([t for t in transactions if t['Tipo'] == 'C']),
                'total_debitos': len([t for t in transactions if t['Tipo'] == 'D']),
                'status': 'sucesso'
            })
            
            if transactions:
                all_transactions.extend(transactions)
                print(f"  OK: {len(transactions)} transações ({total_pages} páginas)")
            else:
                print(f"  Nenhuma transação encontrada ({total_pages} páginas)")
                
        except Exception as e:
            print(f"  ERRO: {e}")
            logs.append({
                'arquivo': pdf_path.name,
                'paginas': 0,
                'total_lido': 0,
                'total_extraido': 0,
                'total_creditos': 0,
                'total_debitos': 0,
                'status': f'erro: {e}'
            })
    
    if all_transactions:
        # Gerar arquivos separados por PDF
        relatorio = []
        
        for pdf_path in pdf_files:
            pdf_transactions = [t for t in all_transactions if t['Arquivo'] == pdf_path.name]
            
            if pdf_transactions:
                df = pd.DataFrame(pdf_transactions)
                df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
                df = df.sort_values('Data_Sort', na_position='last')
                df = df.drop('Data_Sort', axis=1)
                
                # Salvar arquivo individual
                output_path = output_dir / f"{pdf_path.stem}_santander_extraido.csv"
                df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
                
                # Calcular totais
                total_c = len(df[df['Tipo'] == 'C'])
                total_d = len(df[df['Tipo'] == 'D'])
                
                relatorio.append({
                    'arquivo': pdf_path.name,
                    'total_transacoes': len(pdf_transactions),
                    'total_creditos': total_c,
                    'total_debitos': total_d,
                    'arquivo_gerado': output_path.name
                })
                
                print(f"Salvo: {output_path.name} ({len(pdf_transactions)} transações)")
        
        # Gerar relatório
        if relatorio:
            relatorio_df = pd.DataFrame(relatorio)
            relatorio_path = output_dir / "relatorio_santander_pypdf2.csv"
            relatorio_df.to_csv(relatorio_path, index=False, encoding='utf-8', sep=';')
            
            print(f"\nRelatório:")
            print(f"Arquivo: {relatorio_path}")
            for _, row in relatorio_df.iterrows():
                print(f"  {row['arquivo']}: {row['total_transacoes']} trans ({row['total_creditos']}C + {row['total_debitos']}D)")
    
    # Salvar logs
    if logs:
        logs_df = pd.DataFrame(logs)
        logs_path = output_dir / "santander_pypdf2_logs.csv"
        logs_df.to_csv(logs_path, index=False, encoding='utf-8', sep=';')
        print(f"Logs: {logs_path}")

if __name__ == "__main__":
    main()