@echo off
title GODLESS Command Hub
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%
echo Initializing Godless Control Nexus...
python godless_tool.py
pause
