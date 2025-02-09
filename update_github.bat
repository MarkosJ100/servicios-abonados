@echo off
REM Git update and push script with deployment preparation

REM Run deployment preparation
call deploy_prep.bat

REM Add all changes
git add .

REM Commit with a timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set year=%datetime:~0,4%
set month=%datetime:~4,2%
set day=%datetime:~6,2%
set hour=%datetime:~8,2%
set minute=%datetime:~10,2%

git commit -m "Deployment Prep: Compatibility Checks and Model Improvements (%year%-%month%-%day% %hour%:%minute%)"

REM Push to GitHub
git push origin main

echo GitHub repository updated successfully!
