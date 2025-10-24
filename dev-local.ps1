# Script PowerShell para desenvolvimento local (sem Docker)
# Uso: .\dev-local.ps1

Write-Host "🔧 Configurando ambiente de desenvolvimento local" -ForegroundColor Green

# Cria virtual environment se não existir
if (!(Test-Path ".venv")) {
    Write-Host "📦 Criando virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "✅ Virtual environment já existe" -ForegroundColor Green
}

# Ativa virtual environment
Write-Host "🔄 Ativando virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Instala dependências mínimas
Write-Host "📚 Instalando dependências mínimas..." -ForegroundColor Yellow
pip install --upgrade pip
pip install fastapi uvicorn scikit-learn pandas numpy joblib pytest pytest-asyncio pytest-mock flake8 black isort matplotlib seaborn

Write-Host ""
Write-Host "🧪 Executando testes de qualidade do código..." -ForegroundColor Cyan

# Lint com flake8
Write-Host "🔍 Executando flake8..." -ForegroundColor Yellow
flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ flake8: Sem erros críticos" -ForegroundColor Green
} else {
    Write-Host "⚠️  flake8: Encontrados erros" -ForegroundColor Red
}

# Verifica formatação com black
Write-Host "🎨 Verificando formatação com black..." -ForegroundColor Yellow
black --check src
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ black: Código bem formatado" -ForegroundColor Green
} else {
    Write-Host "⚠️  black: Precisa formatação (execute: black src)" -ForegroundColor Yellow
}

# Verifica imports com isort
Write-Host "📋 Verificando imports com isort..." -ForegroundColor Yellow  
isort --check-only src
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ isort: Imports organizados" -ForegroundColor Green
} else {
    Write-Host "⚠️  isort: Precisa organizar imports (execute: isort src)" -ForegroundColor Yellow
}

# Executa testes
Write-Host "🧪 Executando testes..." -ForegroundColor Yellow
pytest tests/ -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Todos os testes passaram!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Alguns testes falharam" -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 Para iniciar a API localmente:" -ForegroundColor Cyan
Write-Host "   uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "📓 Para iniciar Jupyter:" -ForegroundColor Cyan
Write-Host "   jupyter lab --port 8888" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   black src          # Formatar código" -ForegroundColor White
Write-Host "   isort src          # Organizar imports" -ForegroundColor White  
Write-Host "   pytest tests/ -v   # Rodar testes" -ForegroundColor White