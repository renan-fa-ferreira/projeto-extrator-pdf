@echo off
echo === EXTRATOR DE PDF BANCARIO ===
echo.

echo Instalando dependencias...
pip install -r requirements/requirements.txt

echo.
echo === TESTE SIMPLES ===
python extract_simple.py

echo.
echo === TESTE AVANCADO ===
python extract_advanced.py

echo.
echo === TESTE COMPLETO ===
python src/main.py --input data/input/2018_11_extrato_movimento.pdf --output data/output --method all

echo.
echo Extração concluída! Verifique a pasta data/output/
pause