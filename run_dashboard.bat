@echo off
cd /d %~dp0
python -m pip install -r requirements_dashboard.txt
python manage.py runserver
pause
