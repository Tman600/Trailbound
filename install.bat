@echo off
setlocal

where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYCMD=python
) else (
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        set PYCMD=python3
    ) else (
        echo Python was not found on PATH.
        echo Install it from https://www.python.org/downloads/windows/ and try again.
        pause
        exit /b 1
    )
)

%PYCMD% "%~dp0install.py"
pause
