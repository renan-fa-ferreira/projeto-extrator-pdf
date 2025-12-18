#!/usr/bin/env python3
"""Factory para criar extractors específicos"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bank_detector import BankType, BankDetector
from parsers.base_extractor import BaseExtractor

class ExtractorFactory:
    """Factory para criar extractors baseado no tipo de banco"""
    
    @staticmethod
    def create_extractor(bank_type: BankType, pdf_path: str) -> BaseExtractor:
        """Cria extractor específico para o banco"""
        
        if bank_type == BankType.BANCO_DO_BRASIL:
            from parsers.bb.bb_extractor_adapter import BBExtractorAdapter
            return BBExtractorAdapter(pdf_path)
        
        elif bank_type == BankType.BRADESCO:
            from parsers.bradesco.bradesco_cc_adapter import BradescoCCAdapter
            return BradescoCCAdapter(pdf_path)
        
        elif bank_type == BankType.BRADESCO_INVESTIMENTOS:
            from parsers.bradesco.bradesco_inv_adapter import BradescoInvAdapter
            return BradescoInvAdapter(pdf_path)
        
        elif bank_type == BankType.ITAU:
            from parsers.itau.itau_adapter import ItauAdapter
            return ItauAdapter(pdf_path)
        
        elif bank_type == BankType.CAIXA:
            from parsers.caixa.caixa_adapter import CaixaAdapter
            return CaixaAdapter(pdf_path)
        
        elif bank_type in [BankType.SAFRA, BankType.DAYCOVAL, BankType.BV, BankType.CITI]:
            from parsers.enhanced_generic_extractor import EnhancedGenericExtractor
            bank_info = BankDetector.get_bank_info(bank_type)
            return EnhancedGenericExtractor(pdf_path, bank_info['name'])
        
        else:
            from parsers.generic_smart_extractor import GenericSmartExtractor
            return GenericSmartExtractor(pdf_path)