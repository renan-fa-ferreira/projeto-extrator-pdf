# Extrator de Dados de Extratos Bancários PDF

Sistema para extração automatizada de dados de extratos bancários em formato PDF.

## Estrutura do Projeto

```
projeto-extrator-pdf/
├── src/                    # Código fonte principal
│   ├── extractors/         # Módulos de extração de dados
│   ├── parsers/           # Parsers específicos por banco
│   ├── models/            # Modelos de dados
│   └── utils/             # Utilitários e helpers
├── tests/                 # Testes automatizados
│   ├── unit/              # Testes unitários
│   └── integration/       # Testes de integração
├── config/                # Arquivos de configuração
├── data/                  # Dados do projeto
│   ├── input/             # PDFs de entrada
│   ├── output/            # Dados extraídos
│   └── temp/              # Arquivos temporários
├── docs/                  # Documentação
├── logs/                  # Logs da aplicação
└── requirements/          # Dependências
```

## Instalação

```bash
pip install -r requirements/requirements.txt
```

## Uso

```bash
python src/main.py --input data/input/extrato.pdf --output data/output/
```