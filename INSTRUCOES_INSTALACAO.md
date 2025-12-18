# 📦 Instalação do Sistema Universal de Extração

## 🎯 Arquivos Necessários (26 arquivos Python)

### **Copie TODOS estes arquivos mantendo a estrutura:**

```
projeto-extrator-pdf/
├── extract_universal.py
├── requirements/
│   └── requirements.txt
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bank_detector.py
│   │   ├── extractor_factory.py
│   │   └── universal_extractor.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── transaction.py
│   │   └── bank_statement.py
│   └── parsers/
│       ├── __init__.py
│       ├── base_extractor.py
│       ├── generic_smart_extractor.py
│       ├── bb/
│       │   ├── __init__.py
│       │   ├── bb_folder_extractor.py
│       │   └── bb_extractor_adapter.py
│       ├── bradesco/
│       │   ├── __init__.py
│       │   ├── bradesco_conta_corrente.py
│       │   ├── bradesco_investimentos_extractor.py
│       │   ├── bradesco_cc_adapter.py
│       │   └── bradesco_inv_adapter.py
│       ├── itau/
│       │   ├── __init__.py
│       │   ├── itau_extractor.py
│       │   └── itau_adapter.py
│       └── caixa/
│           ├── __init__.py
│           ├── caixa_govconta_extractor.py
│           └── caixa_adapter.py
└── data/
    ├── input/
    ├── output/
    └── temp/
```

## 🚀 Instalação Rápida

### **Opção 1: Copiar Pasta Completa**
```bash
# Copie toda a pasta projeto-extrator-pdf para a nova máquina
# Mantenha TODA a estrutura de pastas
```

### **Opção 2: Usar Script Gerador**
```bash
# 1. Copie apenas o arquivo gerar_estrutura.py
# 2. Execute:
python gerar_estrutura.py

# 3. Depois copie manualmente os arquivos .py de src/
```

## 📥 Instalação de Dependências

```bash
# Crie ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements/requirements.txt
```

## ✅ Verificação

```bash
# Teste se está funcionando
python extract_universal.py
```

## 📋 Dependências Principais

- pdfplumber==0.10.3
- pandas==2.1.4
- openpyxl==3.1.2
- pymupdf==1.23.8
- numpy==1.24.3

## 🎯 Uso

1. Coloque PDFs em `data/input/`
2. Execute: `python extract_universal.py`
3. Resultado em: `data/output/extratos_consolidados.xlsx`

## 🏦 Bancos Suportados

✅ **Implementados:** BB, Bradesco, Itaú, Caixa
🔍 **Detectados:** 35+ bancos brasileiros
🤖 **Fallback:** Extrator genérico inteligente

### **Bancos Detectados Automaticamente:**

**Grandes Bancos:**
- Banco do Brasil, Bradesco, Itaú, Caixa
- Santander, Safra, HSBC

**Bancos de Investimento:**
- BTG Pactual, Modal, Opportunity
- Daycoval, Citibank, ABC Brasil
- BV (ex-Votorantim), Original

**Bancos Digitais:**
- Nubank, Inter, C6 Bank, Next
- BMG, Fibra, Pine, PAN

**Cooperativas:**
- Sicoob, Sicredi

**Bancos Regionais:**
- Banrisul, BRB, Rural
- Sofisa, Rendimento

## 📞 Troubleshooting

**Erro de import:**
- Verifique se TODOS os `__init__.py` existem
- Confirme estrutura de pastas

**Erro de encoding:**
- Salve arquivos com UTF-8
- Use `encoding='utf-8'` ao abrir arquivos

**PDF não reconhecido:**
- Verifique se PDF não está protegido
- Teste com outro banco
- Sistema usa fallback automático
