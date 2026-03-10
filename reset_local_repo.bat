@echo off
:: This script performs a HARD RESET of the local repository to match the remote.
:: It must be run from within the repository structure.

cd /d "%~dp0..\.."

:: Get the current branch name so we don't accidentally reset to main
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i

echo ========================================================
echo  GODLESS MUD: HARD RESET PROTOCOL
echo  Target: %CD%
echo ========================================================
echo.
echo  [WARNING] This will PERMANENTLY DELETE:
echo   - All uncommitted changes
echo   - All new files (including ignored files like .env or venv)
echo   - All local saves/databases not in git
echo   - Target Branch: %CURRENT_BRANCH%
echo.
set /p "confirm=Type 'yes' to confirm you want to wipe everything and reset: "
if /i not "%confirm%"=="yes" goto :cancelled

echo.
echo [1/3] Fetching latest from Google Cloud/GitHub...
git fetch origin

echo [2/3] Resetting files to match remote (%CURRENT_BRANCH%)...
git reset --hard origin/%CURRENT_BRANCH%

echo [3/3] Scrubbing untracked files...
git clean -fdx

echo.
echo [SUCCESS] Repository has been reset to the last committed push.
pause
exit /b

:cancelled
echo.
echo [CANCELLED] No changes were made.
pause