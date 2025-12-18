#!/usr/bin/env python3
"""Script simples para extração rápida de PDF bancário"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime

def extract_pdf_simple(pdf_path):
    """Extração simples usando pdfplumber"""
    transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            
            # Padrão básico: data + valor + descrição
            lines = text.split('\n')
            
            for line in lines:
                # Procura por padrão de data
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                # Procura por valor monetário
                value_match = re.search(r'([+-]?\d+[.,]\d{2})', line)
                
                if date_match and value_match:
                    try:
                        date = datetime.strptime(date_match.group(1), '%d/%m/%Y')
                        value = float(value_match.group(1).replace(',', '.'))
                        
                        # Remove data e valor da linha para pegar descrição
                        desc = line.replace(date_match.group(1), '').replace(value_match.group(1), '').strip()
                        
                        transactions.append({
                            'data': date.strftime('%d/%m/%Y'),
                            'valor': value,
                            'descricao': desc,
                            'tipo': 'credito' if value > 0 else 'debito'
                        })
                    except:
                        continue
    
    return pd.DataFrame(transactions)

if __name__ == "__main__":
    # Teste com arquivo de exemplo
    pdf_file = "data/input/2018_11_extrato_movimento.pdf"
    
    print("Extraindo dados do PDF...")
    df = extract_pdf_simple(pdf_file)
    
    if not df.empty:
        print(f"✓ {len(df)} transações encontradas")
        
        # Salva resultado
        output_file = "data/output/extrato_simples.xlsx"
        df.to_excel(output_file, index=False)
        print(f"✓ Salvo em: {output_file}")
        
        # Mostra preview
        print("\nPreview dos dados:")
        print(df.head())
    else:
        print("✗ Nenhuma transação encontrada")