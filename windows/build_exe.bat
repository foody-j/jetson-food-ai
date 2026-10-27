@echo off
setlocal

cd /d %~dp0

if not exist .venv (
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

pyinstaller --noconfirm --clean --windowed --onefile ^
  --name FryingDataAnalyzer ^
  app.py

echo.
echo Build complete: %cd%\dist\FryingDataAnalyzer.exe
pause
