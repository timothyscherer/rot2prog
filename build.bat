@echo off
echo Make sure the version in setup.py is up-to-date!
pause
cd /d %~dp0

python -m venv .venv
CALL .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install pdoc3
pip install build
pip install twine
pip install -r requirements.txt

cd src
pdoc rot2prog --html -f -o ../docs
cd ..
python -m build
twine upload dist/*
pause