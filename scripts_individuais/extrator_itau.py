#!/usr/bin/env python3
"""Extrator individual melhorado para Itaú - formato correto"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def extract_itau_data(pdf_path):
    """Extrai dados do extrato do Itaú - melhorado para múltiplos layouts"""
    transactions = []
    metadata = {
        'banco': 'Banco Itaú',
        'codigo_banco': '341',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processando {len(pdf.pages)} páginas...")
            
            # Extrair metadados da primeira página
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    # Padrão 1: Agência/Conta: XXXX/XXXXX-X
                    agencia_conta_match = re.search(r'Agência/Conta:\s*(\d+)/(\d+-\d+)', first_page_text)
                    if agencia_conta_match:
                        metadata['agencia'] = agencia_conta_match.group(1)
                        metadata['conta'] = agencia_conta_match.group(2)
                    
                    # Padrão 2: Ag: XXXX Conta: XXXXX-X
                    if not metadata['agencia']:
                        ag_match = re.search(r'Ag:\s*(\d+)', first_page_text)
                        conta_match = re.search(r'Conta:\s*(\d+-\d+)', first_page_text)
                        if ag_match:
                            metadata['agencia'] = ag_match.group(1)
                        if conta_match:
                            metadata['conta'] = conta_match.group(1)
                    
                    # Padrão 3: ag XXXX cc XXXXX-X (extrato mensal)
                    if not metadata['agencia']:
                        mensal_match = re.search(r'ag\s+(\d+)\s+cc\s+(\d+-\d+)', first_page_text)
                        if mensal_match:
                            metadata['agencia'] = mensal_match.group(1)
                            metadata['conta'] = mensal_match.group(2)
                    
                    # Extrair período
                    periodo_match = re.search(r'Extrato de\s+(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    if not periodo_match:
                        periodo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+[ae]\s+(\d{2}/\d{2}/\d{4})', first_page_text)
                    # Padrão mensal: mês YYYY
                    if not periodo_match:
                        mes_match = re.search(r'(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s+(\d{4})', first_page_text, re.IGNORECASE)
                        if mes_match:
                            metadata['periodo'] = f"{mes_match.group(1).title()} {mes_match.group(2)}"
                    if periodo_match:
                        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
            
            # Processar todas as páginas
            current_date = None
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                print(f"Página {page_num + 1}: {len(lines)} linhas")
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith(('Data', 'Itaú', 'Página', 'Extrato')):
                        continue
                    
                    # Layout 1: DD/MM DESCRIÇÃO AGENCIA.CONTA-DIGITO VALOR
                    itau_layout1 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d{4}\.\d{5}-\d)\s+([+-]?[\d.,]+)$', line)
                    if itau_layout1:
                        data = itau_layout1.group(1)
                        descricao = itau_layout1.group(2).strip()
                        agencia_origem = itau_layout1.group(3)
                        valor_str = itau_layout1.group(4).replace('.', '').replace(',', '.')
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': agencia_origem,
                            'Descrição': descricao,
                            'Valor': valor,
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Layout 2: DD/MM DESCRIÇÃO DOCUMENTO VALOR
                    itau_layout2 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d+)\s+([+-]?[\d.,]+)$', line)
                    if itau_layout2:
                        data = itau_layout2.group(1)
                        descricao = itau_layout2.group(2).strip()
                        documento = itau_layout2.group(3)
                        valor_str = itau_layout2.group(4).replace('.', '').replace(',', '.')
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Codigo Banco': metadata['codigo_banco'],
                            'Agencia': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': documento,
                            'Descricao': descricao,
                            'Valor': f"{valor:.2f}".replace('.', ','),
                            'Tipo': tipo,
                            'Saldo': '0,00'
                        })
                        continue
                    
                    # Layout 3: DD/MM DESCRIÇÃO VALOR (sem documento)
                    itau_layout3 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+([+-]?[\d.,]+)$', line)
                    if itau_layout3:
                        data = itau_layout3.group(1)
                        descricao = itau_layout3.group(2).strip()
                        valor_str = itau_layout3.group(3).replace('.', '').replace(',', '.')
                        
                        # Filtrar linhas que não são transações
                        if (len(descricao) < 5 or 
                            any(word in descricao.upper() for word in ['SALDO', 'TOTAL', 'EXTRATO', 'PÁGINA'])):
                            continue
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': '',
                            'Descrição': descricao,
                            'Valor': valor,
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Layout 4: DD/MM/YYYY DESCRIÇÃO VALOR (data completa)
                    itau_layout4 = re.search(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([+-]?[\d.,]+)$', line)
                    if itau_layout4:
                        data = itau_layout4.group(1)
                        descricao = itau_layout4.group(2).strip()
                        valor_str = itau_layout4.group(3).replace('.', '').replace(',', '.')
                        
                        if len(descricao) < 5:
                            continue
                        
                        tipo = 'D' if valor_str.startswith('-') else 'C'
                        valor = float(valor_str.replace('-', ''))
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data,
                            'Documento': '',
                            'Descrição': descricao,
                            'Valor': valor,
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Capturar data atual para transações sem data
                    date_only = re.search(r'^(\d{2}/\d{2}/\d{4})', line)
                    if date_only:
                        current_date = date_only.group(1)
                        continue
                    
                    # Layout 5: PIX QRS NOME DD/MM VALOR (extrato mensal)
                    pix_match = re.search(r'^PIX QRS\s+(.+?)(\d{2}/\d{2})\s+([\d.,]+)$', line)
                    if pix_match:
                        nome = pix_match.group(1).strip()
                        data = pix_match.group(2)
                        valor_str = pix_match.group(3).replace('.', '').replace(',', '.')
                        
                        # Assumir ano atual se não especificado
                        current_year = datetime.now().year
                        data_completa = f"{data}/{current_year}"
                        
                        transactions.append({
                            'Banco': metadata['banco'],
                            'Código Banco': metadata['codigo_banco'],
                            'Agência': metadata['agencia'],
                            'Conta': metadata['conta'],
                            'Data': data_completa,
                            'Documento': 'PIX',
                            'Descrição': f'PIX QRS {nome}',
                            'Valor': float(valor_str),
                            'Tipo': 'C',
                            'Saldo': 0.0
                        })
                        continue
                    
                    # Layout 6: Transações sem data (usar current_date)
                    if current_date:
                        no_date_match = re.search(r'^(.+?)\s+([+-]?[\d.,]+)$', line)
                        if (no_date_match and 
                            len(no_date_match.group(1)) > 10 and
                            not line.startswith(tuple('0123456789'))):
                            
                            descricao = no_date_match.group(1).strip()
                            valor_str = no_date_match.group(2).replace('.', '').replace(',', '.')
                            
                            if any(word in descricao.upper() for word in ['SALDO', 'TOTAL', 'EXTRATO']):
                                continue
                            
                            tipo = 'D' if valor_str.startswith('-') else 'C'
                            valor = float(valor_str.replace('-', ''))
                            
                            transactions.append({
                                'Banco': metadata['banco'],
                                'Código Banco': metadata['codigo_banco'],
                                'Agência': metadata['agencia'],
                                'Conta': metadata['conta'],
                                'Data': current_date,
                                'Documento': '',
                                'Descrição': descricao,
                                'Valor': valor,
                                'Tipo': tipo,
                                'Saldo': 0.0
                            })
            
            print(f"Total de transações encontradas: {len(transactions)}")
    
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return [], metadata
    
    return transactions, metadata

def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    output_dir = script_dir.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Procurar TODOS os PDFs do Itaú na pasta input
    itau_files = []
    for pdf_file in input_dir.glob("*.pdf"):
        if any(word in pdf_file.name.upper() for word in ["ITAU", "ITAÚ", "341"]):
            itau_files.append(pdf_file)
    
    if not itau_files:
        print("Nenhum PDF do Itaú encontrado em data/input/")
        return
    
    print(f"Encontrados {len(itau_files)} PDFs do Itaú:")
    for i, pdf_file in enumerate(itau_files):
        print(f"  {i+1}. {pdf_file.name}")
    
    # Processar TODOS os arquivos do Itaú
    total_transactions = 0
    successful_files = 0
    
    for i, pdf_path in enumerate(itau_files):
        print(f"\n[{i+1}/{len(itau_files)}] Processando: {pdf_path.name}")
        print("=" * 60)
        
        transactions, metadata = extract_itau_data(pdf_path)
        
        if not transactions:
            print("Nenhuma transação encontrada")
            continue
        
        # Criar DataFrame
        df = pd.DataFrame(transactions)
        
        # Ordenar por data, documento, descrição
        df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Data_Sort'] = df['Data_Sort'].fillna(pd.to_datetime(df['Data'], format='%d/%m', errors='coerce'))
        df = df.sort_values(['Data_Sort', 'Documento', 'Descrição'], na_position='last')
        df = df.drop('Data_Sort', axis=1)
        
        # Salvar em CSV na pasta output
        output_path = output_dir / (pdf_path.stem + "_itau_extraido.csv")
        try:
            df.to_csv(output_path, index=False, encoding='utf-8', sep=';')
            print(f"Dados extraidos salvos em: {output_path}")
            successful_files += 1
        except PermissionError:
            print(f"Aviso: Não foi possível salvar o arquivo (pode estar aberto)")
        
        print(f"Metadados extraídos:")
        print(f"  Banco: {metadata['banco']}")
        print(f"  Código: {metadata['codigo_banco']}")
        print(f"  Agência: {metadata['agencia']}")
        print(f"  Conta: {metadata['conta']}")
        print(f"  Período: {metadata['periodo']}")
        print(f"Total de transações: {len(transactions)}")
        
        total_transactions += len(transactions)
        
        print("\nPrimeiras 3 transações:")
        print(df.head(3).to_string(index=False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL - PROCESSAMENTO ITAÚ")
    print("=" * 60)
    print(f"Arquivos processados: {successful_files}/{len(itau_files)}")
    print(f"Total de transações extraídas: {total_transactions}")
    print(f"Taxa de sucesso: {successful_files/len(itau_files)*100:.1f}%")

if __name__ == "__main__":
    main()