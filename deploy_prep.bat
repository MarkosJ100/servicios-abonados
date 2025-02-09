@echo off
REM Deployment Preparation Script

echo Preparing for deployment...

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

REM Install or upgrade dependencies
pip install -r requirements.txt --upgrade

REM Run compatibility check
python compatibility_check.py

REM Run tests
python -m unittest test_migration.py

REM Deactivate virtual environment
deactivate

echo Deployment preparation complete!
