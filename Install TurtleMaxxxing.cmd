@echo off
rem Double-click this file to install TurtleMaxxxing.
rem It runs scripts\setup.ps1. "-ExecutionPolicy Bypass" applies to this one run only
rem and changes no settings on your computer. Read setup.ps1 first if you like.
title TurtleMaxxxing setup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1" %*
echo.
pause
