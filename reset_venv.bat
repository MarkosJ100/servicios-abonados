@echo off
REM Reset virtual environment and reinstall dependencies

REM Remove existing virtual environment
if exist venv (
    rmdir /s /q venv
)

REM Create new virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

REM Install dependencies
pip install -r requirements.txt

REM Deactivate virtual environment
deactivate

echo Virtual environment reset and dependencies reinstalled successfully!
