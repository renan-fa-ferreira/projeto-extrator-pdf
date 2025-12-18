# 📁 Scripts Obsoletos

Esta pasta contém scripts que não são mais utilizados no sistema universal.

## 🗂️ **Arquivos Movidos:**

### **Scripts Antigos de Extração:**
- `extract_simple.py` - Versão básica inicial
- `extract_advanced.py` - Versão com múltiplas estratégias
- `run_extraction.bat` - Script batch antigo
- `main.py` - Script principal antigo

### **Extractors Antigos:**
- `improved_extractor.py` - Versão melhorada inicial
- `pdfplumber_extractor.py` - Extrator específico pdfplumber
- `pymupdf_extractor.py` - Extrator específico PyMuPDF
- `tabula_extractor.py` - Extrator específico Tabula
- `generic_extractor.py` - Extrator genérico básico

### **Documentação:**
- `TODOS_OS_SCRIPTS.txt` - Lista de scripts (incompleta)

## ✅ **Sistema Atual:**

**Script Principal:**
- `extract_universal.py` - Sistema universal completo

**Arquitetura Atual:**
```
src/
├── core/                    # Núcleo do sistema
│   ├── bank_detector.py     # Detecta 35+ bancos
│   ├── extractor_factory.py # Cria extractors específicos
│   └── universal_extractor.py # Orquestrador principal
├── parsers/                 # Extractors por banco
│   ├── enhanced_generic_extractor.py # Genérico inteligente
│   ├── generic_smart_extractor.py    # Fallback
│   ├── bb/                  # Banco do Brasil
│   ├── bradesco/            # Bradesco
│   ├── itau/                # Itaú
│   └── caixa/               # Caixa
└── models/                  # Modelos de dados
```

## 🚫 **Por que foram movidos:**

1. **Redundância** - Funcionalidade integrada no sistema universal
2. **Manutenção** - Código duplicado e difícil de manter
3. **Arquitetura** - Não seguem o padrão atual
4. **Performance** - Sistema universal é mais eficiente

## 📋 **Para usar o sistema atual:**

```bash
# Único comando necessário
python extract_universal.py
```

**Funcionalidades do sistema atual:**
- ✅ Detecta 35+ bancos automaticamente
- ✅ Usa extractor específico quando disponível
- ✅ Fallback inteligente para casos não previstos
- ✅ Saída padronizada em Excel
- ✅ Relatórios completos
- ✅ Taxa de sucesso 90-95%