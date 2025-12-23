#!/usr/bin/env python3
"""Extrator genérico melhorado - preparado para novos bancos"""

import pdfplumber
import pandas as pd
import re
import sys
from pathlib import Path
from datetime import datetime

def concatenate_description_lines(lines, start_index):
    """Concatena linhas de descrição que foram quebradas - versão corrigida"""
    description_parts = []
    i = start_index
    
    while i >= 0:
        line = lines[i].strip()
        
        # Para se encontrar linha com números (valores/documentos) ou data
        if (re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', line) or 
            re.search(r'\d{2}/\d{2}/\d{4}', line) or
            line.isdigit() or
            not line or
            len(line) < 3):
            break
            
        # Adiciona a linha à descrição
        description_parts.insert(0, line)
        i -= 1
        
        # Limita a 3 linhas para evitar pegar dados irrelevantes
        if len(description_parts) >= 3:
            break
    
    return ' '.join(description_parts) if description_parts else "Operação Bancária"

def detect_bank(text, filename=""):
    """Detecta o banco - preparado para novos bancos"""
    text_upper = text.upper()
    filename_upper = filename.upper()
    
    bank_keywords = {
        'Banco Bradesco S/A': {
            'file': ['BRADESCO'],
            'text': ['BRADESCO', 'BANCO BRADESCO', '237', 'AG:', 'CC:', 'EXTRATO DE:']
        },
        'Banco Itaú': {
            'file': ['ITAU', 'ITAÚ'],
            'text': ['ITAU', 'ITAÚ', 'BANCO ITAU', '341', 'AGENCIA/CONTA:']
        },
        'Caixa Econômica Federal': {
            'file': ['CEF', 'CAIXA'],
            'text': ['CAIXA ECONOMICA', 'CEF', '104', 'CONTA REFERENCIA']
        },
        'Banco Safra': {
            'file': ['SAFRA'],
            'text': ['BANCO SAFRA', 'SAFRA', '422', 'SALDO TOTAL']
        },
        'Banco Daycoval': {
            'file': ['DAYCOVAL'],
            'text': ['DAYCOVAL', '707', 'BANCO DAYCOVAL']
        },
        'Banco ABC Brasil': {
            'file': ['ABC'],
            'text': ['ABC BRASIL', 'BANCO ABC', '246']
        },
        'Banco BV': {
            'file': ['VOTORANTIM', 'BV'],
            'text': ['BANCO VOTORANTIM', 'BV', '655', 'CONTA VINCULADA']
        },
        'Citibank': {
            'file': ['CITI'],
            'text': ['CITIBANK', 'CITI', '745']
        },
        'Oliveira Trust': {
            'file': ['OT'],
            'text': ['OLIVEIRA TRUST', 'DISTRIBUIDORA DE TITULOS', 'CONTA CORRENTE EM REAIS']
        },
        'Vortx': {
            'file': ['VORTX'],
            'text': ['VORTX', 'ULTIMOS LANCAMENTOS', 'REMETENTE/FAVORECIDO']
        },
        # Preparado para novos bancos
        'Banco Santander': {
            'file': ['SANTANDER'],
            'text': ['SANTANDER', 'BANCO SANTANDER', '033']
        },
        'Nubank': {
            'file': ['NUBANK', 'NU'],
            'text': ['NUBANK', 'NU PAGAMENTOS', '260']
        },
        'Banco Inter': {
            'file': ['INTER'],
            'text': ['BANCO INTER', 'INTER', '077']
        },
        'C6 Bank': {
            'file': ['C6'],
            'text': ['C6 BANK', 'BANCO C6', '336']
        },
        'Banco do Brasil': {
            'file': ['BB'],
            'text': ['BANCO DO BRASIL', 'BB', '001', 'AGENCIA:', 'CONTA CORRENTE']
        }
    }
    
    # Verificar pelo nome do arquivo primeiro
    for bank_name, keywords in bank_keywords.items():
        if any(keyword in filename_upper for keyword in keywords['file']):
            return bank_name
    
    # Verificar pelo conteúdo do texto
    for bank_name, keywords in bank_keywords.items():
        if any(keyword in text_upper for keyword in keywords['text']):
            return bank_name
    
    return 'Banco Genérico'

def extract_metadata(text, bank_name):
    """Extrai metadados específicos por banco"""
    metadata = {
        'banco': bank_name,
        'codigo_banco': '',
        'agencia': '',
        'conta': '',
        'periodo': ''
    }
    
    bank_codes = {
        'Banco do Brasil': '001',
        'Banco Bradesco S/A': '237',
        'Banco Itaú': '341',
        'Caixa Econômica Federal': '104',
        'Banco Safra': '422',
        'Banco Daycoval': '707',
        'Banco ABC Brasil': '246',
        'Banco BV': '655',
        'Citibank': '745',
        'Oliveira Trust': '999',
        'Vortx': '998',
        'Banco Santander': '033',
        'Nubank': '260',
        'Banco Inter': '077',
        'C6 Bank': '336'
    }
    
    metadata['codigo_banco'] = bank_codes.get(bank_name, '')
    
    # Padrões específicos por banco
    if 'Bradesco' in bank_name:
        agencia_match = re.search(r'Ag:\s*(\d+)', text)
        conta_match = re.search(r'CC:\s*(\d+-\d+)', text)
        periodo_match = re.search(r'Entre\s+(\d{2}/\d{2}/\d{4})\s+e\s+(\d{2}/\d{2}/\d{4})', text)
    elif 'Itaú' in bank_name:
        agencia_conta_match = re.search(r'Agência/Conta:\s*(\d+)/(\d+-\d+)', text)
        if agencia_conta_match:
            metadata['agencia'] = agencia_conta_match.group(1)
            metadata['conta'] = agencia_conta_match.group(2)
        # Padrão mensal: ag XXXX cc XXXXX-X
        if not metadata['agencia']:
            mensal_match = re.search(r'ag\s+(\d+)\s+cc\s+(\d+-\d+)', text)
            if mensal_match:
                metadata['agencia'] = mensal_match.group(1)
                metadata['conta'] = mensal_match.group(2)
        periodo_match = re.search(r'Extrato de\s+(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})', text)
        # Período mensal
        if not 'periodo_match' in locals() or not periodo_match:
            mes_match = re.search(r'(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s+(\d{4})', text, re.IGNORECASE)
            if mes_match:
                metadata['periodo'] = f"{mes_match.group(1).title()} {mes_match.group(2)}"
    elif 'BV' in bank_name or 'Votorantim' in bank_name:
        conta_match = re.search(r'Conta:\s*([\d.-]+)', text)
        periodo_match = re.search(r'Período:\s*(\d{2}/\d{2}/\d{4})\s+à\s+(\d{2}/\d{2}/\d{4})', text)
    elif 'Oliveira Trust' in bank_name:
        conta_match = re.search(r'Conta:\s*(\d+\s*-\s*\d+)', text)
        periodo_match = re.search(r'Data de Início\s+(\d{2}/\d{2}/\d{4})\s+Data de Fim\s+(\d{2}/\d{2}/\d{4})', text)
    elif 'Vortx' in bank_name:
        conta_match = re.search(r'Conta:(\d+\s*-\s*\d+)', text)
        periodo_match = None
    else:
        # Padrões genéricos
        agencia_match = re.search(r'Ag[eê]ncia[:\s]*(\d+[-]?\d*)', text)
        conta_match = re.search(r'Conta[:\s]*(\d+[-]?\d*)', text)
        periodo_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+[ae]\s+(\d{2}/\d{2}/\d{4})', text)
    
    if 'agencia_match' in locals() and agencia_match:
        metadata['agencia'] = agencia_match.group(1)
    if 'conta_match' in locals() and conta_match:
        metadata['conta'] = conta_match.group(1).replace(' ', '')
    if 'periodo_match' in locals() and periodo_match:
        metadata['periodo'] = f"{periodo_match.group(1)} a {periodo_match.group(2)}"
    
    return metadata

def extract_transactions_all_pages(pdf, bank_name):
    """Extrai transações de TODAS as páginas - melhorado para novos bancos"""
    transactions = []
    current_date = None
    
    print(f"Processando {len(pdf.pages)} páginas...")
    
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue
        
        lines = text.split('\n')
        print(f"Página {page_num + 1}: {len(lines)} linhas")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith(('Data', 'Página', 'Extrato')):
                continue
            
            # Padrões específicos por banco
            if 'Bradesco' in bank_name:
                # Padrão principal: DOCUMENTO VALOR SALDO (linha com números)
                transaction_match = re.search(r'^(\d+)\s+(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})$', line)
                if transaction_match:
                    doc = transaction_match.group(1)
                    valor_str = transaction_match.group(2).replace('.', '').replace(',', '.')
                    saldo_str = transaction_match.group(3).replace('.', '').replace(',', '.')
                    
                    # Concatenar descrição das linhas anteriores
                    descricao = concatenate_description_lines(lines, i - 1)
                    
                    # Usar data atual ou tentar extrair da linha
                    data_transacao = current_date if current_date else "01/01/2024"
                    
                    transactions.append({
                        'Data': data_transacao,
                        'Documento': doc,
                        'Descrição': descricao,
                        'Valor': float(valor_str),
                        'Tipo': 'C',
                        'Saldo': float(saldo_str)
                    })
                    continue
                
                # Padrão de data: captura nova data de transação
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                if date_match and not re.search(r'\d{1,3}(?:\.\d{3})*,\d{2}', line):
                    current_date = date_match.group(1)
                    continue
            
            elif 'Itaú' in bank_name:
                # Layout 1: DD/MM DESCRIÇÃO AGENCIA.CONTA-DIGITO VALOR
                itau_layout1 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+(\d{4}\.\d{5}-\d)\s+([+-]?[\d.,]+)$', line)
                if itau_layout1:
                    data = itau_layout1.group(1)
                    descricao = itau_layout1.group(2).strip()
                    documento = itau_layout1.group(3)
                    valor_str = itau_layout1.group(4).replace('.', '').replace(',', '.')
                    tipo = 'D' if valor_str.startswith('-') else 'C'
                    valor = float(valor_str.replace('-', ''))
                    
                    transactions.append({
                        'Data': data,
                        'Documento': documento,
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
                        'Data': data,
                        'Documento': documento,
                        'Descrição': descricao,
                        'Valor': valor,
                        'Tipo': tipo,
                        'Saldo': 0.0
                    })
                    continue
                
                # Layout 3: DD/MM DESCRIÇÃO VALOR (sem documento)
                itau_layout3 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+([+-]?[\d.,]+)$', line)
                if itau_layout3:
                    data = itau_layout3.group(1)
                    descricao = itau_layout3.group(2).strip()
                    valor_str = itau_layout3.group(3).replace('.', '').replace(',', '.')
                    
                    # Filtrar linhas inválidas
                    if (len(descricao) < 5 or 
                        any(word in descricao.upper() for word in ['SALDO', 'TOTAL', 'EXTRATO'])):
                        continue
                    
                    tipo = 'D' if valor_str.startswith('-') else 'C'
                    valor = float(valor_str.replace('-', ''))
                    
                    transactions.append({
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
                        'Data': data,
                        'Documento': '',
                        'Descrição': descricao,
                        'Valor': valor,
                        'Tipo': tipo,
                        'Saldo': 0.0
                    })
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
                        'Data': data_completa,
                        'Documento': 'PIX',
                        'Descrição': f'PIX QRS {nome}',
                        'Valor': float(valor_str),
                        'Tipo': 'C',
                        'Saldo': 0.0
                    })
                    continue
            
            elif 'Vortx' in bank_name:
                # DD/MM/YYYY DESCRIÇÃO TED Recebida R$ VALOR R$ SALDO
                vortx_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+TED\s+Recebida\s+R\$\s+([\d.,]+)\s+R\$\s+([\d.,]+)', line)
                if vortx_match:
                    data = vortx_match.group(1)
                    descricao = vortx_match.group(2).strip() + " TED Recebida"
                    valor_str = vortx_match.group(3).replace('.', '').replace(',', '.')
                    saldo_str = vortx_match.group(4).replace('.', '').replace(',', '.')
                    
                    transactions.append({
                        'Data': data,
                        'Documento': '',
                        'Descrição': descricao,
                        'Valor': float(valor_str),
                        'Tipo': 'C',
                        'Saldo': float(saldo_str)
                    })
                
                # DD/MM/YYYY DESCRIÇÃO -R$ VALOR R$ SALDO
                else:
                    vortx_debit = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+-R\$\s+([\d.,]+)\s+R\$\s+([\d.,]+)', line)
                    if vortx_debit:
                        data = vortx_debit.group(1)
                        descricao = vortx_debit.group(2).strip()
                        valor_str = vortx_debit.group(3).replace('.', '').replace(',', '.')
                        saldo_str = vortx_debit.group(4).replace('.', '').replace(',', '.')
                        
                        transactions.append({
                            'Data': data,
                            'Documento': '',
                            'Descrição': descricao,
                            'Valor': float(valor_str),
                            'Tipo': 'D',
                            'Saldo': float(saldo_str)
                        })
            
            elif 'Oliveira Trust' in bank_name:
                # DD/MM/YYYY DOCUMENTO VALOR SALDO
                ot_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d+)\s+([\d.,]+)\s+([\d.,]+)', line)
                if ot_match:
                    data = ot_match.group(1)
                    documento = ot_match.group(2)
                    valor_str = ot_match.group(3).replace('.', '').replace(',', '.')
                    saldo_str = ot_match.group(4).replace('.', '').replace(',', '.')
                    
                    # Procurar descrição na próxima linha
                    descricao = "Operação Financeira"
                    
                    transactions.append({
                        'Data': data,
                        'Documento': documento,
                        'Descrição': descricao,
                        'Valor': float(valor_str),
                        'Tipo': 'C',
                        'Saldo': float(saldo_str)
                    })
            
            elif 'Banco do Brasil' in bank_name:
                # Padrão BB flexível: qualquer linha com data
                bb_flex = re.search(r'(\d{2}/\d{2}/\d{4})\s+(.+)', line)
                if bb_flex:
                    data = bb_flex.group(1)
                    resto = bb_flex.group(2).strip()
                    
                    # Tentar extrair valor e tipo do final
                    valor_match = re.search(r'([\d.,]+)\s+([CD])\s*$', resto)
                    if valor_match:
                        valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
                        tipo = valor_match.group(2)
                        descricao = resto[:valor_match.start()].strip()
                        
                        # Procurar descrição adicional na próxima linha
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not re.search(r'\d{2}/\d{2}/\d{4}', next_line) and len(next_line) > 5:
                                descricao += " " + next_line
                        
                        transactions.append({
                            'Data': data,
                            'Documento': '',
                            'Descrição': descricao,
                            'Valor': float(valor_str),
                            'Tipo': tipo,
                            'Saldo': 0.0
                        })
                        continue
            
            else:
                # Padrões genéricos para outros bancos (Santander, Nubank, etc.)
                # Detectar nova data
                date_only = re.search(r'^(\d{2}/\d{2}/\d{4})', line)
                if date_only:
                    current_date = date_only.group(1)
                    continue
                
                date_short = re.search(r'^(\d{2}/\d{2})\s', line)
                if date_short:
                    current_date = date_short.group(1)
                
                # Transações genéricas
                if current_date:
                    generic_match = re.search(r'^(.+?)\s+([\d.,]+)\s*([DC]?)$', line)
                    if generic_match and len(generic_match.group(1)) > 3:
                        descricao = generic_match.group(1).strip()
                        valor_str = generic_match.group(2).replace('.', '').replace(',', '.')
                        tipo = generic_match.group(3) if generic_match.group(3) else 'C'
                        
                        try:
                            transactions.append({
                                'Data': current_date,
                                'Documento': '',
                                'Descrição': descricao,
                                'Valor': float(valor_str),
                                'Tipo': tipo,
                                'Saldo': 0.0
                            })
                        except:
                            continue
    
    print(f"Total de transações encontradas: {len(transactions)}")
    return transactions

def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir.parent / "data" / "input"
    output_dir = script_dir.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF encontrado em data/input/")
        return
    
    print(f"Encontrados {len(pdf_files)} PDFs para processar")
    
    for pdf_path in pdf_files:
        print(f"\n{'='*60}")
        print(f"Processando: {pdf_path.name}")
        print(f"{'='*60}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Detectar banco
                first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""
                bank_name = detect_bank(first_page_text, pdf_path.name)
                
                # Se não detectou, tentar padrões específicos
                if bank_name == 'Banco Genérico' and 'AGENCIA' in first_page_text and 'CONTA' in first_page_text:
                    bank_name = 'Banco Santander'
                
                # Extrair metadados
                metadata = extract_metadata(first_page_text, bank_name)
                
                # Extrair transações de TODAS as páginas
                transactions = extract_transactions_all_pages(pdf, bank_name)
                
                if not transactions:
                    print("Nenhuma transação encontrada")
                    continue
                
                # Remover duplicatas
                seen = set()
                unique_transactions = []
                for t in transactions:
                    key = (t['Data'], t['Descrição'], t['Valor'])
                    if key not in seen:
                        seen.add(key)
                        # Adicionar metadados
                        t['Banco'] = metadata['banco']
                        t['Código Banco'] = metadata['codigo_banco']
                        t['Agência'] = metadata['agencia']
                        t['Conta'] = metadata['conta']
                        unique_transactions.append(t)
                
                # Ordenar
                df = pd.DataFrame(unique_transactions)
                df['Data_Sort'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
                df['Data_Sort'] = df['Data_Sort'].fillna(pd.to_datetime(df['Data'], format='%d/%m', errors='coerce'))
                df = df.sort_values(['Data_Sort', 'Documento', 'Descrição'], na_position='last')
                df = df.drop('Data_Sort', axis=1)
                
                # Reorganizar colunas
                cols = ['Banco', 'Código Banco', 'Agência', 'Conta', 'Data', 'Documento', 'Descrição', 'Valor', 'Tipo', 'Saldo']
                df = df.reindex(columns=[col for col in cols if col in df.columns])
                
                # Salvar
                output_path = output_dir / (pdf_path.stem + "_generico_extraido.xlsx")
                df.to_excel(output_path, index=False)
                
                print(f"Banco detectado: {metadata['banco']}")
                print(f"Agência: {metadata['agencia']}")
                print(f"Conta: {metadata['conta']}")
                print(f"Dados extraídos salvos em: {output_path}")
                print(f"Total de transações: {len(unique_transactions)}")
                print("\nPrimeiras 3 transações:")
                print(df.head(3).to_string(index=False))
                
        except Exception as e:
            print(f"Erro ao processar {pdf_path.name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Processamento concluído para {len(pdf_files)} arquivos")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()