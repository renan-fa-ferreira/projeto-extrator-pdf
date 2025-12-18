# Scripts Individuais por Banco

Esta pasta contém scripts independentes para extração de dados de extratos bancários específicos por banco.

## Scripts Disponíveis

- `extrator_bb.py` - Banco do Brasil
- `extrator_bradesco.py` - Bradesco
- `extrator_itau.py` - Itaú
- `extrator_caixa.py` - Caixa Econômica Federal
- `extrator_safra.py` - Banco Safra
- `extrator_daycoval.py` - Banco Daycoval
- `extrator_bv.py` - Banco BV (ex-Votorantim)
- `extrator_abc.py` - Banco ABC Brasil
- `extrator_generico.py` - Extrator genérico para outros bancos

## Como Usar

### Preparação
1. Coloque os PDFs na pasta `data/input/`
2. Execute os scripts da pasta `scripts_individuais/`
3. Os resultados serão salvos em `data/output/`

### Uso Individual

```bash
# Coloque o PDF na pasta data/input/ e execute:
cd scripts_individuais
python extrator_bb.py
python extrator_bradesco.py
python extrator_safra.py
```

**Os scripts procuram automaticamente PDFs do banco correspondente na pasta data/input/**

### Estrutura de Pastas

```
projeto-extrator-pdf/
├── data/
│   ├── input/          # Coloque os PDFs aqui
│   └── output/         # Resultados são salvos aqui
└── scripts_individuais/
    ├── extrator_bb.py
    ├── extrator_bradesco.py
    └── ...
```

### Requisitos

Certifique-se de ter as dependências instaladas:

```bash
pip install pdfplumber pandas openpyxl
```

## Saída

Cada script gera:
- Um arquivo Excel com os dados extraídos (`nome_arquivo_banco_extraido.xlsx`)
- Relatório no console com estatísticas da extração
- Visualização das primeiras 5 transações

## Características dos Scripts

### Banco do Brasil (`extrator_bb.py`)
- Extrai: Data Movimento, Data Balancete, Histórico, Documento, Valor, Tipo, Saldo
- Formato de data: DD/MM
- Identifica débitos/créditos automaticamente

### Bradesco (`extrator_bradesco.py`)
- Extrai: Data, Descrição, Valor, Tipo, Saldo
- Formato de data: DD/MM
- Separa débitos e créditos em colunas

### Itaú (`extrator_itau.py`)
- Extrai: Data, Descrição, Valor, Tipo, Saldo
- Formato de data: DD/MM
- Usa indicadores D/C para tipo de transação

### Caixa (`extrator_caixa.py`)
- Extrai: Data, Descrição, Valor, Tipo, Saldo
- Formato de data: DD/MM/YYYY
- Específico para formato GovConta

### Safra (`extrator_safra.py`)
- Extrai: Data, Descrição, Valor, Tipo
- Múltiplos padrões de extração
- Identifica tipo por palavras-chave

### Daycoval (`extrator_daycoval.py`)
- Extrai: Data, Descrição, Valor, Tipo
- Suporte a múltiplos formatos
- Formato de data flexível

### BV (`extrator_bv.py`)
- Extrai: Data, Descrição, Valor, Tipo, Saldo
- Suporte a valores positivos/negativos
- Formato de data: DD/MM/YYYY

### ABC Brasil (`extrator_abc.py`)
- Extrai: Data, Descrição, Valor, Tipo, Saldo
- Padrão similar ao formato padrão
- Múltiplas estratégias de extração

### Genérico (`extrator_generico.py`)
- 4 estratégias diferentes de extração
- Suporte a tabelas estruturadas
- Remove duplicatas automaticamente
- Funciona com a maioria dos formatos

## Dicas de Uso

1. **Teste primeiro**: Use o extrator genérico se não souber o banco
2. **Qualidade do PDF**: PDFs escaneados podem ter menor taxa de sucesso
3. **Múltiplas páginas**: Todos os scripts processam PDFs com múltiplas páginas
4. **Formatos de data**: Cada banco tem seu formato específico
5. **Validação**: Sempre verifique os resultados no arquivo Excel gerado

## Solução de Problemas

- **Nenhuma transação encontrada**: Tente o extrator genérico
- **Dados incompletos**: Verifique se o PDF não está corrompido
- **Erro de formato**: Confirme se está usando o script correto para o banco
- **Valores incorretos**: Alguns PDFs podem ter formatação especial

## Integração

Estes scripts podem ser integrados ao sistema principal ou usados independentemente conforme a necessidade.