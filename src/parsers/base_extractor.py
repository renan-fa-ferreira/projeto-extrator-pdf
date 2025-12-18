#!/usr/bin/env python3
"""Interface base para todos os extractors"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseExtractor(ABC):
    """Classe base para todos os extractors de banco"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
    
    @abstractmethod
    def extract_statement(self) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extrai dados do extrato
        
        Returns:
            tuple: (DataFrame com transações, Dict com informações do cabeçalho)
        """
        pass
    
    def standardize_output(self, df: pd.DataFrame, header_info: Dict[str, Any]) -> pd.DataFrame:
        """Padroniza saída para formato comum"""
        
        # Colunas padrão esperadas
        standard_columns = [
            'arquivo', 'data_movimento', 'historico', 'documento', 
            'valor', 'saldo', 'tipo', 'conta', 'agencia', 'banco'
        ]
        
        # Adiciona colunas faltantes
        for col in standard_columns:
            if col not in df.columns:
                df[col] = None
        
        # Padroniza tipos
        if 'data_movimento' in df.columns:
            df['data_movimento'] = pd.to_datetime(df['data_movimento'], format='%d/%m/%Y', errors='coerce')
        
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        if 'saldo' in df.columns:
            df['saldo'] = pd.to_numeric(df['saldo'], errors='coerce')
        
        # Ordena colunas
        df = df[standard_columns + [col for col in df.columns if col not in standard_columns]]
        
        return df
    
    def get_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera resumo das transações"""
        
        if df.empty:
            return {}
        
        summary = {
            'total_transacoes': len(df),
            'periodo_inicio': df['data_movimento'].min() if 'data_movimento' in df.columns else None,
            'periodo_fim': df['data_movimento'].max() if 'data_movimento' in df.columns else None,
            'total_creditos': df[df['tipo'] == 'credit']['valor'].sum() if 'valor' in df.columns else 0,
            'total_debitos': abs(df[df['tipo'] == 'debit']['valor'].sum()) if 'valor' in df.columns else 0,
            'saldo_final': df['saldo'].iloc[-1] if 'saldo' in df.columns and not df.empty else 0
        }
        
        return summary