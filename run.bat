@echo off
title NanuPanda Clipper Studio
echo Starting NanuPanda Clipper Studio...
start "" "http://127.0.0.1:8765/app"
python -m studio.server
pause
