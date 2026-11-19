@echo off
echo ========================================
echo    MoveMouse - Criando Executavel
echo ========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado! Instale o Python primeiro.
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install -r requirements.txt

echo.
echo [2/3] Gerando executavel...
pyinstaller --noconfirm --onefile --windowed --name "MoveMouse" --icon=icon.ico move_mouse.py 2>nul || pyinstaller --noconfirm --onefile --windowed --name "MoveMouse" move_mouse.py

echo.
echo [3/3] Limpando arquivos temporarios...
rmdir /s /q build 2>nul
del /q MoveMouse.spec 2>nul

echo.
echo ========================================
echo    Concluido!
echo ========================================
echo.
echo O executavel foi criado em: dist\MoveMouse.exe
echo.
echo Voce pode copiar MoveMouse.exe para qualquer pasta
echo e fixar na barra de tarefas!
echo.
pause
