@echo off
REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Run tests
python -m unittest test_migration.py

REM Deactivate virtual environment
deactivate
