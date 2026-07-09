@echo off
REM =====================================================
REM RefChecks Backend - Push to GitHub Script (Windows)
REM =====================================================

setlocal enabledelayedexpansion
color 0A
cls

echo.
echo ======================================================
echo   RefChecks Backend - GitHub Push Script (Windows)
echo ======================================================
echo.
echo Checking requirements...
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    color 0C
    echo.
    echo ERROR: requirements.txt not found!
    echo.
    echo Please make sure:
    echo   1. You extracted refchecks-backend.zip
    echo   2. This script is in the refchecks-backend folder
    echo.
    pause
    exit /b 1
)

color 0A
echo [OK] Found requirements.txt
echo [OK] Ready to push to GitHub
echo.

git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: Git is not installed
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

echo Configuring Git user...
git config user.email "somnath@example.com" >nul 2>&1
git config user.name "Somnath" >nul 2>&1
echo [OK] Git configured
echo.

if not exist ".git" (
    echo Initializing git repository...
    git init
    echo [OK] Git repository initialized
    echo.
) else (
    echo [OK] Git repository already exists
    echo.
)

echo Adding files to git...
git add .
echo [OK] Files added
echo.

echo Creating commit...
git commit -m "RefChecks Backend Phase 1 - FastAPI + Statsbomb + Bias Analysis" >nul 2>&1
echo [OK] Commit created
echo.

git remote remove origin >nul 2>&1

echo Setting up GitHub remote...
git remote add origin https://github.com/chakrabortysomnath/Refchecks.git
echo [OK] GitHub remote added
echo.

echo Setting up main branch...
git branch -M main
echo [OK] Main branch set
echo.

echo.
echo ======================================================
echo Pushing code to GitHub...
echo ======================================================
echo.
echo When prompted, enter your GitHub credentials:
echo   Username: your GitHub username
echo   Password: Your GitHub Personal Access Token
echo.
echo To create a token:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Click "Generate new token" (classic)
echo   3. Select 'repo' scope
echo   4. Copy and paste the token as password
echo.

git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo ERROR: Push failed!
    echo.
    pause
    exit /b 1
)

color 0A
echo.
echo ======================================================
echo SUCCESS! Code pushed to GitHub
echo ======================================================
echo.
echo Your code is now at:
echo   https://github.com/chakrabortysomnath/Refchecks
echo.
echo Next steps:
echo   1. Visit GitHub to verify code
echo   2. Deploy to Render using RENDER_DEPLOYMENT_GUIDE.md
echo.

pause