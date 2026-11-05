@echo off
setlocal
title HoYoLAB Easy Check-In Hub

:: Check if python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [!] Python 3 was not found on your system!
        echo Please install Python from https://www.python.org/ or the Microsoft Store.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

:: Run interactive checkin hub
%PYTHON_CMD% "%~dp0checkin.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Exited with code %ERRORLEVEL%.
    pause
)
