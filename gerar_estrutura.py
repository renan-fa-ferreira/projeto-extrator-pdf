#!/usr/bin/env python3
"""
Script para gerar toda a estrutura do projeto em outra máquina
Execute: python gerar_estrutura.py
"""

import os
from pathlib import Path

# Estrutura de pastas
FOLDERS = [
    "src/core",
    "src/parsers/bb",
    "src/parsers/bradesco",
    "src/parsers/itau",
    "src/parsers/caixa",
    "src/models",
    "data/input",
    "data/output",
    "data/temp",
    "requirements"
]

# Arquivos e seus conteúdos
FILES = {
    "requirements/requirements.txt": """PyPDF2==3.0.1
pdfplumber==0.10.3
pymupdf==1.23.8
pandas==2.1.4
openpyxl==3.1.2
python-dateutil==2.8.2
regex==2023.10.3
numpy==1.24.3""",

    "extract_universal.py": """#!/usr/bin/env python3
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from core.universal_extractor import main
if __name__ == "__main__":
    main()""",

    "src/__init__.py": "",
    "src/core/__init__.py": "",
    "src/parsers/__init__.py": "",
    "src/parsers/bb/__init__.py": "",
    "src/parsers/bradesco/__init__.py": "",
    "src/parsers/itau/__init__.py": "",
    "src/parsers/caixa/__init__.py": "",
    "src/models/__init__.py": "",
    "data/input/.gitkeep": "",
    "data/output/.gitkeep": "",
}

def criar_estrutura():
    """Cria toda a estrutura de pastas e arquivos"""
    
    print("🚀 Criando estrutura do projeto...\n")
    
    # Cria pastas
    for folder in FOLDERS:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"📁 {folder}/")
    
    # Cria arquivos
    print("\n📄 Criando arquivos...")
    for filepath, content in FILES.items():
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ {filepath}")
    
    print("\n✅ Estrutura básica criada!")
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Copie os arquivos .py da pasta src/ do projeto original")
    print("2. Instale dependências: pip install -r requirements/requirements.txt")
    print("3. Coloque PDFs em data/input/")
    print("4. Execute: python extract_universal.py")

if __name__ == "__main__":
    criar_estrutura()
