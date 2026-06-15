Set-Location $PSScriptRoot
python -m pip install -r requirements_dashboard.txt
python manage.py runserver
