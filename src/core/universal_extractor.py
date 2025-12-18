#!/usr/bin/env python3
"""Extrator universal para todos os bancos"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bank_detector import BankDetector, BankType
from core.extractor_factory import ExtractorFactory

class UniversalExtractor:
    """Extrator universal que identifica e processa qualquer banco"""
    
    def __init__(self, input_folder: str = "data/input"):
        self.input_folder = Path(input_folder)
        self.results = []
        
    def process_all_pdfs(self) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """Processa todos os PDFs da pasta automaticamente"""
        
        pdf_files = list(self.input_folder.glob("*.pdf"))
        
        if not pdf_files:
            print(f"Nenhum PDF encontrado em: {self.input_folder}")
            return pd.DataFrame(), {}
        
        print(f"🔍 Encontrados {len(pdf_files)} arquivos PDF")
        print("="*50)
        
        all_transactions = []
        processing_summary = {}
        
        for pdf_file in pdf_files:
            print(f"\n📄 Processando: {pdf_file.name}")
            
            # 1. Detecta o banco
            bank_type = BankDetector.detect_bank(str(pdf_file))
            bank_info = BankDetector.get_bank_info(bank_type)
            
            print(f"🏦 Banco detectado: {bank_info['name']} ({bank_info['code']})")
            
            # 2. Cria extractor específico
            try:
                extractor = ExtractorFactory.create_extractor(bank_type, str(pdf_file))
                
                # 3. Extrai dados
                df, header_info = extractor.extract_statement()
                
                if not df.empty:
                    # 4. Adiciona informações do banco
                    df['banco_detectado'] = bank_info['name']
                    df['codigo_banco'] = bank_info['code']
                    
                    all_transactions.append(df)
                    
                    # 5. Gera resumo
                    summary = extractor.get_summary(df)
                    processing_summary[pdf_file.name] = {
                        'banco': bank_info['name'],
                        'status': 'sucesso',
                        'transacoes': len(df),
                        'resumo': summary
                    }
                    
                    print(f"✅ {len(df)} transações extraídas")
                    print(f"💰 Créditos: R$ {summary.get('total_creditos', 0):,.2f}")
                    print(f"💸 Débitos: R$ {summary.get('total_debitos', 0):,.2f}")
                    
                else:
                    processing_summary[pdf_file.name] = {
                        'banco': bank_info['name'],
                        'status': 'sem_dados',
                        'transacoes': 0
                    }
                    print("⚠️  Nenhuma transação encontrada")
                    
            except Exception as e:
                processing_summary[pdf_file.name] = {
                    'banco': bank_info['name'],
                    'status': 'erro',
                    'erro': str(e)
                }
                print(f"❌ Erro: {e}")
        
        # 6. Consolida resultados
        if all_transactions:
            final_df = pd.concat(all_transactions, ignore_index=True)
            
            # Ordena por arquivo e data
            if 'data_movimento' in final_df.columns:
                final_df = final_df.sort_values(['arquivo', 'data_movimento'])
            
            return final_df, processing_summary
        
        return pd.DataFrame(), processing_summary
    
    def save_results(self, df: pd.DataFrame, summary: Dict[str, Any], output_folder: str = "data/output"):
        """Salva resultados consolidados"""
        
        output_path = Path(output_folder)
        output_path.mkdir(exist_ok=True)
        
        if not df.empty:
            # Salva transações consolidadas
            consolidated_file = output_path / "extratos_consolidados.xlsx"
            
            with pd.ExcelWriter(consolidated_file, engine='openpyxl') as writer:
                # Aba principal com todas as transações
                df.to_excel(writer, sheet_name='Todas_Transacoes', index=False)
                
                # Aba por banco
                for banco in df['banco_detectado'].unique():
                    if pd.notna(banco):
                        df_banco = df[df['banco_detectado'] == banco]
                        # Remove caracteres inválidos do Excel
                        sheet_name = banco.replace(' ', '_').replace('/', '_').replace('\\', '_')
                        sheet_name = ''.join(c for c in sheet_name if c.isalnum() or c == '_')[:31]
                        df_banco.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Aba de resumo
                summary_df = pd.DataFrame([
                    {
                        'arquivo': arquivo,
                        'banco': info.get('banco', ''),
                        'status': info.get('status', ''),
                        'transacoes': info.get('transacoes', 0),
                        'total_creditos': info.get('resumo', {}).get('total_creditos', 0),
                        'total_debitos': info.get('resumo', {}).get('total_debitos', 0)
                    }
                    for arquivo, info in summary.items()
                ])
                
                summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            print(f"\n💾 Resultados salvos em: {consolidated_file}")
            return consolidated_file
        
        return None
    
    def generate_report(self, summary: Dict[str, Any]):
        """Gera relatório de processamento"""
        
        print(f"\n📊 RELATÓRIO FINAL")
        print("="*50)
        
        total_files = len(summary)
        successful = len([s for s in summary.values() if s.get('status') == 'sucesso'])
        total_transactions = sum(s.get('transacoes', 0) for s in summary.values())
        
        print(f"📁 Arquivos processados: {total_files}")
        print(f"✅ Sucessos: {successful}")
        print(f"❌ Erros: {total_files - successful}")
        print(f"📋 Total de transações: {total_transactions}")
        
        # Resumo por banco
        banks = {}
        for info in summary.values():
            banco = info.get('banco', 'Desconhecido')
            if banco not in banks:
                banks[banco] = {'arquivos': 0, 'transacoes': 0}
            banks[banco]['arquivos'] += 1
            banks[banco]['transacoes'] += info.get('transacoes', 0)
        
        print(f"\n🏦 RESUMO POR BANCO:")
        for banco, stats in banks.items():
            print(f"  {banco}: {stats['arquivos']} arquivo(s), {stats['transacoes']} transação(ões)")

def main():
    """Função principal"""
    
    print("🚀 EXTRATOR UNIVERSAL DE EXTRATOS BANCÁRIOS")
    print("="*50)
    
    # Cria extrator universal
    extractor = UniversalExtractor()
    
    # Processa todos os PDFs
    df, summary = extractor.process_all_pdfs()
    
    # Salva resultados
    if not df.empty:
        output_file = extractor.save_results(df, summary)
    
    # Gera relatório
    extractor.generate_report(summary)

if __name__ == "__main__":
    main()