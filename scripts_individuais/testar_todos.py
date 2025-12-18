#!/usr/bin/env python3
"""Script para testar todos os extractors individuais"""

import os
import sys
import subprocess
from pathlib import Path

def test_all_extractors(pdf_name):
    """Testa todos os extractors com um PDF da pasta data/input"""
    
    input_dir = Path("../data/input")
    pdf_path = input_dir / pdf_name
    
    if not pdf_path.exists():
        print(f"Arquivo não encontrado: {pdf_path}")
        print(f"Certifique-se de que o arquivo está em data/input/")
        return
    
    extractors = [
        'extrator_bb.py',
        'extrator_bradesco.py',
        'extrator_itau.py',
        'extrator_caixa.py',
        'extrator_safra.py',
        'extrator_daycoval.py',
        'extrator_bv.py',
        'extrator_abc.py',
        'extrator_generico.py'
    ]
    
    results = {}
    
    for extractor in extractors:
        print(f"\n{'='*50}")
        print(f"Testando: {extractor}")
        print(f"{'='*50}")
        
        try:
            result = subprocess.run([
                sys.executable, extractor, pdf_name
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ SUCESSO")
                print(result.stdout)
                results[extractor] = "SUCESSO"
            else:
                print("❌ ERRO")
                print(result.stderr)
                results[extractor] = "ERRO"
                
        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT")
            results[extractor] = "TIMEOUT"
        except Exception as e:
            print(f"💥 EXCEÇÃO: {e}")
            results[extractor] = "EXCEÇÃO"
    
    # Resumo final
    print(f"\n{'='*60}")
    print("RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    for extractor, status in results.items():
        status_icon = {
            "SUCESSO": "✅",
            "ERRO": "❌", 
            "TIMEOUT": "⏰",
            "EXCEÇÃO": "💥"
        }.get(status, "❓")
        
        print(f"{status_icon} {extractor:<25} - {status}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python testar_todos.py <nome_do_arquivo.pdf>")
        print("\nEste script testa todos os extractors com o PDF da pasta data/input/")
        print("Exemplo: python testar_todos.py 'EXTRATO CONTA BANCO BRASIL MES 02-2024.pdf'")
        sys.exit(1)
    
    pdf_name = sys.argv[1]
    test_all_extractors(pdf_name)

if __name__ == "__main__":
    main()