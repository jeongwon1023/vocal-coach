# Vocal Coach AI - Deploy prep (PowerShell)
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$gitExe = "git"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $fallback = "C:\Program Files\Git\bin\git.exe"
    if (Test-Path $fallback) { $gitExe = $fallback }
}

Write-Host "========================================"
Write-Host "  Vocal Coach AI - Deploy Prep"
Write-Host "========================================"
Write-Host ""

# Git
if (Get-Command $gitExe -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Git installed"
    & $gitExe --version
} else {
    Write-Host "[X] Git not found"
    Write-Host "    Install: winget install --id Git.Git -e"
    Write-Host "    Then open a NEW PowerShell window."
}
Write-Host ""

# Smoke test
Write-Host "--- Smoke test ---"
$py = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (Test-Path $py) {
    & $py (Join-Path $PSScriptRoot "tests\test_ui_smoke.py")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Smoke test failed"
        exit 1
    }
} else {
    Write-Host "[!] venv not found"
}
Write-Host ""

# Security checks
Write-Host "--- Security check ---"
if (Test-Path ".env") {
    Write-Host "[OK] .env exists locally (must NOT be pushed)"
} else {
    Write-Host "[!] .env not found - set secrets on Streamlit Cloud"
}

$gi = Get-Content ".gitignore" -ErrorAction SilentlyContinue
if ($gi -match "^\.env") {
    Write-Host "[OK] .env is in .gitignore"
} else {
    Write-Host "[X] .env missing from .gitignore - fix before push"
}

if (Test-Path ".git") {
    $tracked = & $gitExe ls-files --error-unmatch .env 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[X] DANGER: .env is tracked by git! Run: git rm --cached .env"
    } else {
        Write-Host "[OK] .env is not tracked by git"
    }
    Write-Host ""
    Write-Host "[OK] Git repo"
    & $gitExe status -sb
} else {
    Write-Host ""
    Write-Host "[!] No git repo. Example:"
    Write-Host "    git init"
    Write-Host "    git add ."
    Write-Host '    git commit -m "vocal-coach beta"'
    Write-Host "    git branch -M main"
    Write-Host "    git remote add origin https://github.com/YOUR_USERNAME/vocal-coach.git"
    Write-Host "    git push -u origin main"
}
Write-Host ""

Write-Host "--- Streamlit Cloud ---"
Write-Host "1. https://share.streamlit.io"
Write-Host "2. New app - repo - Main file: app.py"
Write-Host "3. Secrets: OPENAI_API_KEY, COACH_RAG_ENABLED (see .streamlit\secrets.toml.example)"
Write-Host "4. Deploy — push main triggers auto-redeploy"
Write-Host ""
Write-Host "Full plan: docs\DEPLOY-PLAN.md"
Write-Host "Checklist: docs\BETA-LAUNCH.md"
