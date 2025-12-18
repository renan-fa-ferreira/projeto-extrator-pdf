#!/usr/bin/env python3
"""Extrator específico para extratos de investimentos do Bradesco"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

def extract_bradesco_investments(pdf_path):
    """Extrai dados de investimentos do Bradesco"""
    
    all_data = []
    header_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Extrai info do cabeçalho
            for line in lines[:10]:
                if 'MUNICIPIO' in line.upper() or 'PREFEITURA' in line.upper():
                    header_info['cliente'] = line.strip()
                elif 'Período:' in line:
                    dates = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                    if len(dates) >= 2:
                        header_info['periodo_inicio'] = dates[0]
                        header_info['periodo_fim'] = dates[1]
                elif 'BANCO BRADESCO' in line:
                    header_info['banco'] = 'BANCO BRADESCO S.A'
            
            # Processa tabelas
            tables = page.extract_tables()
            
            for table in tables:
                if not table or len(table) < 2:
                    continue
                
                # Procura por tabela de movimentação
                for i, row in enumerate(table):
                    if any('Data' in str(cell) and 'Histórico' in str(cell) for cell in row if cell):
                        # Encontrou header de movimentação
                        header_row = i
                        
                        # Mapeia colunas
                        header = row
                        col_map = {}
                        
                        for j, col in enumerate(header):
                            if not col:
                                continue
                            col_str = str(col).upper()
                            
                            if 'DATA' in col_str:
                                col_map['data'] = j
                            elif 'HISTÓRICO' in col_str or 'HISTORICO' in col_str:
                                col_map['historico'] = j
                            elif 'VALOR' in col_str and 'BRUTO' in col_str:
                                col_map['valor_bruto'] = j
                            elif 'VALOR' in col_str and 'LÍQUIDO' in col_str:
                                col_map['valor_liquido'] = j
                            elif 'QUANTIDADE' in col_str:
                                col_map['quantidade'] = j
                            elif 'COTA' in col_str and 'VALOR' in col_str:
                                col_map['valor_cota'] = j
                        
                        # Processa linhas de dados
                        for data_row in table[header_row + 1:]:
                            if not data_row or len(data_row) < 3:
                                continue
                            
                            try:
                                # Data
                                if 'data' not in col_map:
                                    continue
                                
                                date_str = str(data_row[col_map['data']] or '').strip()
                                if not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                                    continue
                                
                                # Histórico
                                historico = ''
                                if 'historico' in col_map:
                                    historico = str(data_row[col_map['historico']] or '').strip()
                                
                                # Valores
                                valor_bruto = 0.0
                                valor_liquido = 0.0
                                quantidade = 0.0
                                valor_cota = 0.0
                                
                                if 'valor_bruto' in col_map and data_row[col_map['valor_bruto']]:
                                    valor_str = str(data_row[col_map['valor_bruto']]).replace(',', '.')
                                    try:
                                        valor_bruto = float(re.sub(r'[^\d.-]', '', valor_str))
                                    except:
                                        pass
                                
                                if 'valor_liquido' in col_map and data_row[col_map['valor_liquido']]:
                                    valor_str = str(data_row[col_map['valor_liquido']]).replace(',', '.')
                                    try:
                                        valor_liquido = float(re.sub(r'[^\d.-]', '', valor_str))
                                    except:
                                        pass
                                
                                if 'quantidade' in col_map and data_row[col_map['quantidade']]:
                                    qtd_str = str(data_row[col_map['quantidade']]).replace(',', '.')
                                    try:
                                        quantidade = float(re.sub(r'[^\d.-]', '', qtd_str))
                                    except:
                                        pass
                                
                                if 'valor_cota' in col_map and data_row[col_map['valor_cota']]:
                                    cota_str = str(data_row[col_map['valor_cota']]).replace(',', '.')
                                    try:
                                        valor_cota = float(re.sub(r'[^\d.-]', '', cota_str))
                                    except:
                                        pass
                                
                                # Determina tipo de operação
                                tipo = 'aplicacao' if valor_bruto > 0 else 'resgate'
                                
                                # Adiciona registro
                                record = {
                                    'arquivo': Path(pdf_path).name,
                                    'data': datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y'),
                                    'historico': historico,
                                    'valor_bruto': valor_bruto,
                                    'valor_liquido': valor_liquido,
                                    'quantidade_cotas': quantidade,
                                    'valor_cota': valor_cota,
                                    'tipo_operacao': tipo,
                                    'cliente': header_info.get('cliente', ''),
                                    'periodo_inicio': header_info.get('periodo_inicio', ''),
                                    'periodo_fim': header_info.get('periodo_fim', ''),
                                    'banco': header_info.get('banco', 'BRADESCO')
                                }
                                
                                all_data.append(record)
                                
                            except Exception as e:
                                continue
            
            # Extrai resumo de investimentos da primeira página
            if page_num == 1:
                for i, line in enumerate(lines):
                    if 'Produto' in line and 'C.N.P.J' in line:
                        # Próximas linhas têm os produtos
                        for j in range(i+1, min(i+10, len(lines))):
                            if 'Total' in lines[j]:
                                break
                            
                            # Procura por linha de produto
                            if re.search(r'BRADESCO.*\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', lines[j]):
                                parts = lines[j].split()
                                if len(parts) >= 3:
                                    produto = ' '.join(parts[:-3])  # Nome do produto
                                    try:
                                        saldo_inicial = float(parts[-3].replace('.', '').replace(',', '.'))
                                        saldo_final = float(parts[-2].replace('.', '').replace(',', '.'))
                                        percentual = parts[-1].replace('%', '')
                                        
                                        resumo = {
                                            'arquivo': Path(pdf_path).name,
                                            'produto': produto,
                                            'saldo_inicial': saldo_inicial,
                                            'saldo_final': saldo_final,
                                            'percentual': percentual,
                                            'tipo': 'resumo_investimento',
                                            'cliente': header_info.get('cliente', ''),
                                            'periodo_inicio': header_info.get('periodo_inicio', ''),
                                            'periodo_fim': header_info.get('periodo_fim', ''),
                                            'banco': header_info.get('banco', 'BRADESCO')
                                        }
                                        
                                        all_data.append(resumo)
                                    except:
                                        continue
    
    return pd.DataFrame(all_data), header_info

def main():
    input_folder = "data/input"
    
    pdf_files = list(Path(input_folder).glob("*radesco*.pdf"))
    
    if not pdf_files:
        print("Nenhum PDF do Bradesco encontrado")
        return
    
    print("=== EXTRATOR BRADESCO INVESTIMENTOS ===\n")
    
    for pdf_file in pdf_files:
        print(f"Processando: {pdf_file.name}")
        
        try:
            df, header = extract_bradesco_investments(str(pdf_file))
            
            if not df.empty:
                # Separa movimentações e resumos
                movimentacoes = df[df.get('tipo', '') != 'resumo_investimento']
                resumos = df[df.get('tipo', '') == 'resumo_investimento']
                
                # Salva movimentações
                if not movimentacoes.empty:
                    output_mov = f"data/output/bradesco_movimentacoes_{pdf_file.stem}.xlsx"
                    movimentacoes.to_excel(output_mov, index=False)
                    print(f"✓ {len(movimentacoes)} movimentações salvas em: {output_mov}")
                
                # Salva resumos
                if not resumos.empty:
                    output_res = f"data/output/bradesco_resumo_{pdf_file.stem}.xlsx"
                    resumos.to_excel(output_res, index=False)
                    print(f"✓ {len(resumos)} produtos no resumo: {output_res}")
                
                # Estatísticas
                print(f"\nINFORMAÇÕES:")
                print(f"- Cliente: {header.get('cliente', 'N/A')}")
                print(f"- Período: {header.get('periodo_inicio', '')} a {header.get('periodo_fim', '')}")
                
                if not resumos.empty:
                    total_inicial = resumos['saldo_inicial'].sum()
                    total_final = resumos['saldo_final'].sum()
                    print(f"- Saldo inicial: R$ {total_inicial:,.2f}")
                    print(f"- Saldo final: R$ {total_final:,.2f}")
                    print(f"- Variação: R$ {total_final - total_inicial:,.2f}")
                
                print(f"\nPreview movimentações:")
                if not movimentacoes.empty:
                    print(movimentacoes[['data', 'historico', 'valor_bruto', 'valor_liquido']].head())
                
            else:
                print("✗ Nenhum dado encontrado")
                
        except Exception as e:
            print(f"✗ Erro: {e}")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()