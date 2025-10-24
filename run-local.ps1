# Script PowerShell para rodar o projeto fake-news-detector localmente
# Uso: .\run-local.ps1

Write-Host "🚀 Iniciando Fake News Detector - Ambiente Local" -ForegroundColor Green

# Verifica se Docker está rodando
Write-Host "📋 Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker está rodando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está rodando. Inicie o Docker Desktop primeiro." -ForegroundColor Red
    exit 1
}

# Navega para pasta docker
Write-Host "📁 Navegando para pasta docker..." -ForegroundColor Yellow
Set-Location docker

# Inicia serviços com docker-compose
Write-Host "🐳 Iniciando serviços (LocalStack, MLflow, API, Jupyter)..." -ForegroundColor Yellow
docker-compose up -d

# Aguarda serviços iniciarem
Write-Host "⏳ Aguardando serviços inicializarem..." -ForegroundColor Yellow
Start-Sleep 10

# Verifica se serviços estão rodando
Write-Host "🔍 Verificando status dos serviços..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "🎉 Ambiente iniciado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Acesse os serviços:" -ForegroundColor Cyan
Write-Host "   🌐 API FastAPI:     http://localhost:8000" -ForegroundColor White
Write-Host "   📊 MLflow:          http://localhost:5000" -ForegroundColor White  
Write-Host "   📓 Jupyter:         http://localhost:8888 (token: fake-news-dev)" -ForegroundColor White
Write-Host "   ☁️  LocalStack S3:   http://localhost:4566" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Para testar a API:" -ForegroundColor Cyan
Write-Host '   curl http://localhost:8000/health' -ForegroundColor White
Write-Host '   curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d "{\"text\":\"Exemplo de notícia\"}"' -ForegroundColor White
Write-Host ""
Write-Host "⏹️  Para parar os serviços:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "📋 Para ver logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f [nome-do-serviço]" -ForegroundColor White

# Volta para pasta raiz
Set-Location ..