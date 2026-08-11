@echo off
cd /d "%~dp0"
echo [1/2] Building embedded data...
python build_data.py
if %errorlevel% neq 0 (echo Data build failed! && pause && exit /b %errorlevel%)
echo [2/2] Packaging exe...
python -m PyInstaller "LazyFisher计算器.spec"
echo Done! Check dist/ folder
pause
