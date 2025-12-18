import argparse
import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractors.pdfplumber_extractor import PDFPlumberExtractor
from extractors.pymupdf_extractor import PyMuPDFExtractor
from extractors.tabula_extractor import TabulaExtractor

def main():
    parser = argparse.ArgumentParser(description='Extrator de dados de extratos bancários PDF')
    parser.add_argument('--input', required=True, help='Caminho do arquivo PDF')
    parser.add_argument('--output', required=True, help='Pasta de saída')
    parser.add_argument('--method', choices=['pdfplumber', 'pymupdf', 'tabula', 'all'], 
                       default='all', help='Método de extração')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Arquivo não encontrado: {args.input}")
        return
    
    os.makedirs(args.output, exist_ok=True)
    
    filename = Path(args.input).stem
    
    extractors = {
        'pdfplumber': PDFPlumberExtractor,
        'pymupdf': PyMuPDFExtractor,
        'tabula': TabulaExtractor
    }
    
    methods = [args.method] if args.method != 'all' else list(extractors.keys())
    
    for method in methods:
        print(f"\n=== Extraindo com {method.upper()} ===")
        
        try:
            extractor = extractors[method](args.input)
            df = extractor.to_dataframe()
            
            if not df.empty:
                output_file = os.path.join(args.output, f"{filename}_{method}.xlsx")
                df.to_excel(output_file, index=False)
                print(f"✓ {len(df)} transações extraídas")
                print(f"✓ Salvo em: {output_file}")
            else:
                print("✗ Nenhuma transação encontrada")
                
        except Exception as e:
            print(f"✗ Erro: {e}")

if __name__ == "__main__":
    main()