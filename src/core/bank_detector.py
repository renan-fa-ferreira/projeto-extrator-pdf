#!/usr/bin/env python3
"""Detector automático de bancos - versão corrigida"""

import pdfplumber
import re
from enum import Enum

class BankType(Enum):
    BANCO_DO_BRASIL = "bb"
    BRADESCO = "bradesco"
    BRADESCO_INVESTIMENTOS = "bradesco_investimentos"
    ITAU = "itau"
    CAIXA = "caixa"
    SANTANDER = "santander"
    NUBANK = "nubank"
    INTER = "inter"
    SICOOB = "sicoob"
    SICREDI = "sicredi"
    BANRISUL = "banrisul"
    BRB = "brb"
    SAFRA = "safra"
    VOTORANTIM = "votorantim"
    ORIGINAL = "original"
    PAN = "pan"
    PINE = "pine"
    C6 = "c6"
    NEXT = "next"
    DAYCOVAL = "daycoval"
    CITI = "citi"
    ABC = "abc"
    BV = "bv"
    HSBC = "hsbc"
    BTG = "btg"
    MODAL = "modal"
    FIBRA = "fibra"
    RURAL = "rural"
    BMG = "bmg"
    OPPORTUNITY = "opportunity"
    SOFISA = "sofisa"
    RENDIMENTO = "rendimento"
    UNKNOWN = "unknown"

class BankDetector:
    
    BANK_PATTERNS = {
        BankType.BANCO_DO_BRASIL: [
            r'BANCO DO BRASIL',
            r'001.*BANCO DO BRASIL',
            r'Dt\.\\s*movimento.*Dt\.\\s*balancete.*Histórico.*Documento.*Valor R\$.*Saldo',
            r'Ag[eê]ncia\\s*\\d+-\\d+',
            r'Conta corrente.*\\d+-\\d+'
        ],
        
        BankType.BRADESCO: [
            r'BANCO BRADESCO',
            r'BRADESCO S/A',
            r'Ag[eê]ncia.*\\|\\s*Conta',
            r'Data.*Lan[çc]amento.*D[ée]bito.*Cr[ée]dito.*Saldo',
            r'CNPJ:.*\\d{3}\\.\\d{3}\\.\\d{3}/\\d{4}-\\d{2}'
        ],
        
        BankType.BRADESCO_INVESTIMENTOS: [
            r'BRADESCO FI RF',
            r'BRADESCO FIC FI',
            r'Resumo dos Investimentos',
            r'Produto.*C\\.N\\.P\\.J',
            r'Administrador.*C\\.N\\.P\\.J'
        ],
        
        BankType.ITAU: [
            r'BANCO ITA[UÚ]',
            r'ITA[UÚ] UNIBANCO',
            r'341.*ITA[UÚ]',
            r'Ag[eê]ncia.*\\d{4}',
            r'Conta.*\\d+-\\d+'
        ],
        
        BankType.CAIXA: [
            r'CAIXA ECON[ÔO]MICA',
            r'CAIXA.*104',
            r'CEF',
            r'C\\.E\\.F\\.',
            r'104.*CAIXA',
            r'Ag[eê]ncia.*\\d{4}.*Op.*\\d+',
            r'EXTRATO.*CONTA.*CORRENTE.*CAIXA',
            r'www\\.caixa\\.gov\\.br',
            r'GOVCONTA CAIXA'
        ],
        
        BankType.SANTANDER: [
            r'BANCO SANTANDER',
            r'SANTANDER.*033',
            r'Ag[eê]ncia.*\\d{4}'
        ],
        
        BankType.SAFRA: [
            r'BANCO SAFRA',
            r'422.*SAFRA',
            r'J\\. SAFRA',
            r'SAFRA S/A',
            r'J SAFRA',
            r'SAFRA.*EXTRATOS',
            r'SAFRA.*APLICACAO',
            r'SAFRA.*INVESTIMENTOS',
            r'Data.*Lançamento.*Complemento.*Valor',
            r'\\d{2}/\\d{2}\\s+[A-Z].*\\d+,\\d{2}'
        ],
        
        BankType.DAYCOVAL: [
            r'DAYCOVAL',
            r'BANCO DAYCOVAL',
            r'707.*DAYCOVAL',
            r'DAYCOVAL S/A',
            r'DAYCOVAL.*EXTRATO',
            r'EXTRATO.*DAYCOVAL'
        ],
        
        BankType.CITI: [
            r'CITIBANK',
            r'CITI',
            r'745.*CITI',
            r'BANCO CITIBANK',
            r'CITI.*EXTRATO',
            r'EXTRATO.*CITI',
            r'Date.*Description.*Amount.*Balance'
        ],
        
        BankType.BV: [
            r'BANCO BV',
            r'BV.*FINANCEIRA',
            r'BV S/A',
            r'655.*BV',
            r'VOTORANTIM.*BV',
            r'BV.*EXTRATO',
            r'EXTRATO.*BV'
        ],
        
        BankType.NUBANK: [
            r'NUBANK',
            r'NU PAGAMENTOS',
            r'NUCONTA',
            r'Roxinho'
        ],
        
        BankType.INTER: [
            r'BANCO INTER',
            r'INTER.*077',
            r'INTERMEDIUM'
        ],
        
        BankType.SICOOB: [
            r'SICOOB',
            r'COOPERATIVA.*CREDITO',
            r'756.*SICOOB'
        ],
        
        BankType.SICREDI: [
            r'SICREDI',
            r'748.*SICREDI',
            r'COOPERATIVA.*SICREDI'
        ],
        
        BankType.BANRISUL: [
            r'BANRISUL',
            r'041.*BANRISUL',
            r'BANCO.*RIO GRANDE'
        ],
        
        BankType.BRB: [
            r'BRB.*BANCO',
            r'070.*BRB',
            r'BRASILIA'
        ],
        
        BankType.VOTORANTIM: [
            r'BANCO VOTORANTIM',
            r'655.*VOTORANTIM',
            r'VOTORANTIM S/A'
        ],
        
        BankType.ORIGINAL: [
            r'BANCO ORIGINAL',
            r'212.*ORIGINAL',
            r'ORIGINAL.*INVESTIMENTOS'
        ],
        
        BankType.PAN: [
            r'BANCO PAN',
            r'623.*PAN',
            r'PANAMERICANO'
        ],
        
        BankType.PINE: [
            r'PINE',
            r'643.*PINE',
            r'BANCO PINE'
        ],
        
        BankType.C6: [
            r'C6 BANK',
            r'336.*C6',
            r'BANCO C6'
        ],
        
        BankType.NEXT: [
            r'NEXT',
            r'237.*NEXT',
            r'BRADESCO NEXT'
        ],
        
        BankType.ABC: [
            r'BANCO ABC',
            r'ABC BRASIL',
            r'246.*ABC',
            r'ABC.*BRASIL'
        ],
        
        BankType.HSBC: [
            r'HSBC',
            r'399.*HSBC',
            r'BANCO HSBC'
        ],
        
        BankType.BTG: [
            r'BTG PACTUAL',
            r'208.*BTG',
            r'BTG.*PACTUAL'
        ],
        
        BankType.MODAL: [
            r'MODAL',
            r'746.*MODAL',
            r'BANCO MODAL'
        ],
        
        BankType.FIBRA: [
            r'FIBRA',
            r'224.*FIBRA',
            r'BANCO FIBRA'
        ],
        
        BankType.RURAL: [
            r'BANCO RURAL',
            r'453.*RURAL',
            r'RURAL S/A'
        ],
        
        BankType.BMG: [
            r'BMG',
            r'318.*BMG',
            r'BANCO BMG'
        ],
        
        BankType.OPPORTUNITY: [
            r'OPPORTUNITY',
            r'45.*OPPORTUNITY',
            r'BANCO OPPORTUNITY'
        ],
        
        BankType.SOFISA: [
            r'SOFISA',
            r'637.*SOFISA',
            r'BANCO SOFISA'
        ],
        
        BankType.RENDIMENTO: [
            r'RENDIMENTO',
            r'633.*RENDIMENTO',
            r'BANCO RENDIMENTO'
        ]
    }
    
    @classmethod
    def detect_bank(cls, pdf_path: str) -> BankType:
        """Detecta o banco baseado no conteúdo do PDF"""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_sample = ""
                for page in pdf.pages[:3]:
                    page_text = page.extract_text()
                    if page_text:
                        text_sample += page_text + "\\n"
                
                for bank_type, patterns in cls.BANK_PATTERNS.items():
                    score = 0
                    
                    for pattern in patterns:
                        try:
                            if re.search(pattern, text_sample, re.IGNORECASE):
                                score += 1
                        except:
                            continue
                    
                    if score >= 1:
                        return bank_type
                
                return BankType.UNKNOWN
                
        except Exception as e:
            print(f"Erro ao detectar banco em {pdf_path}: {e}")
            return BankType.UNKNOWN
    
    @classmethod
    def get_bank_info(cls, bank_type: BankType) -> dict:
        """Retorna informações do banco"""
        
        bank_info = {
            BankType.BANCO_DO_BRASIL: {'name': 'Banco do Brasil', 'code': '001', 'extractor': 'bb'},
            BankType.BRADESCO: {'name': 'Banco Bradesco S/A', 'code': '237', 'extractor': 'bradesco'},
            BankType.BRADESCO_INVESTIMENTOS: {'name': 'Bradesco Investimentos', 'code': '237', 'extractor': 'bradesco_investimentos'},
            BankType.ITAU: {'name': 'Banco Itaú Unibanco S/A', 'code': '341', 'extractor': 'itau'},
            BankType.CAIXA: {'name': 'Caixa Econômica Federal', 'code': '104', 'extractor': 'caixa'},
            BankType.SANTANDER: {'name': 'Banco Santander', 'code': '033', 'extractor': 'santander'},
            BankType.SAFRA: {'name': 'Banco Safra', 'code': '422', 'extractor': 'safra'},
            BankType.DAYCOVAL: {'name': 'Banco Daycoval', 'code': '707', 'extractor': 'daycoval'},
            BankType.CITI: {'name': 'Citibank', 'code': '745', 'extractor': 'citi'},
            BankType.BV: {'name': 'Banco BV (ex-Votorantim)', 'code': '655', 'extractor': 'bv'},
            BankType.NUBANK: {'name': 'Nubank', 'code': '260', 'extractor': 'nubank'},
            BankType.INTER: {'name': 'Banco Inter', 'code': '077', 'extractor': 'inter'},
            BankType.SICOOB: {'name': 'Sicoob', 'code': '756', 'extractor': 'sicoob'},
            BankType.SICREDI: {'name': 'Sicredi', 'code': '748', 'extractor': 'sicredi'},
            BankType.BANRISUL: {'name': 'Banrisul', 'code': '041', 'extractor': 'banrisul'},
            BankType.BRB: {'name': 'BRB - Banco de Brasília', 'code': '070', 'extractor': 'brb'},
            BankType.VOTORANTIM: {'name': 'Banco Votorantim', 'code': '655', 'extractor': 'votorantim'},
            BankType.ORIGINAL: {'name': 'Banco Original', 'code': '212', 'extractor': 'original'},
            BankType.PAN: {'name': 'Banco PAN', 'code': '623', 'extractor': 'pan'},
            BankType.PINE: {'name': 'Banco Pine', 'code': '643', 'extractor': 'pine'},
            BankType.C6: {'name': 'C6 Bank', 'code': '336', 'extractor': 'c6'},
            BankType.NEXT: {'name': 'Next (Bradesco)', 'code': '237', 'extractor': 'next'},
            BankType.ABC: {'name': 'Banco ABC Brasil', 'code': '246', 'extractor': 'abc'},
            BankType.HSBC: {'name': 'HSBC Brasil', 'code': '399', 'extractor': 'hsbc'},
            BankType.BTG: {'name': 'BTG Pactual', 'code': '208', 'extractor': 'btg'},
            BankType.MODAL: {'name': 'Banco Modal', 'code': '746', 'extractor': 'modal'},
            BankType.FIBRA: {'name': 'Banco Fibra', 'code': '224', 'extractor': 'fibra'},
            BankType.RURAL: {'name': 'Banco Rural', 'code': '453', 'extractor': 'rural'},
            BankType.BMG: {'name': 'Banco BMG', 'code': '318', 'extractor': 'bmg'},
            BankType.OPPORTUNITY: {'name': 'Banco Opportunity', 'code': '045', 'extractor': 'opportunity'},
            BankType.SOFISA: {'name': 'Banco Sofisa', 'code': '637', 'extractor': 'sofisa'},
            BankType.RENDIMENTO: {'name': 'Banco Rendimento', 'code': '633', 'extractor': 'rendimento'},
            BankType.UNKNOWN: {'name': 'Banco não identificado', 'code': '000', 'extractor': 'generic'}
        }
        
        return bank_info.get(bank_type, bank_info[BankType.UNKNOWN])