@echo off
chcp 65001 >nul
powershell -ExecutionPolicy Bypass -File "%~dp0tools\tout-faire.ps1"
