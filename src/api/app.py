"""
FastAPI application para servir o modelo de detecção de fake news.
Esta API fornece endpoints para predição de fake news usando modelos
armazenados no S3 (LocalStack).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from typing import Dict, Any
import os
import sys

# Adiciona o diretório src ao path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from storage.s3_client import S3Client
    from api.model_loader import ModelLoader
except ImportError as e:
    logging.warning(f"Erro ao importar módulos locais: {e}")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="Fake News Detector API",
    description="API para detecção de fake news usando machine learning",
    version="1.0.0"
)

# Modelos de dados para API
class NewsText(BaseModel):
    text: str

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    probabilities: Dict[str, float]

class HealthResponse(BaseModel):
    status: str
    message: str

# Variáveis globais
model_loader = None

@app.on_event("startup")
async def startup_event():
    """Inicializa o carregador de modelos na inicialização da API."""
    global model_loader
    try:
        # Configuração do S3 (LocalStack)
        s3_config = {
            'endpoint_url': os.getenv('S3_ENDPOINT', 'http://localhost:4566'),
            'bucket_name': os.getenv('S3_BUCKET', 'fake-news-models'),
            'model_key': os.getenv('MODEL_KEY', 'models/best_model.joblib'),
            'vectorizer_key': os.getenv('VECTORIZER_KEY', 'models/vectorizer.joblib')
        }
        
        model_loader = ModelLoader(s3_config)
        await model_loader.load_model()
        logger.info("Modelo carregado com sucesso na inicialização")
        
    except Exception as e:
        logger.error(f"Erro ao carregar modelo na inicialização: {e}")
        # A API ainda pode iniciar, mas as predições falharão


@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raiz para verificação de saúde da API."""
    return HealthResponse(
        status="ok",
        message="Fake News Detector API está funcionando"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint detalhado de verificação de saúde."""
    try:
        if model_loader and model_loader.is_model_loaded():
            return HealthResponse(
                status="healthy",
                message="API e modelo estão funcionando corretamente"
            )
        else:
            return HealthResponse(
                status="degraded",
                message="API funcionando, mas modelo não carregado"
            )
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/predict", response_model=PredictionResponse)
async def predict_fake_news(news: NewsText):
    """
    Endpoint principal para predição de fake news.
    
    Args:
        news: Objeto contendo o texto da notícia
        
    Returns:
        Predição com confiança e probabilidades
    """
    try:
        if not model_loader or not model_loader.is_model_loaded():
            raise HTTPException(
                status_code=503,
                detail="Modelo não está disponível. Tente novamente mais tarde."
            )
        
        if not news.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Texto da notícia não pode estar vazio"
            )
        
        # Fazer predição
        result = model_loader.predict(news.text)
        
        return PredictionResponse(
            prediction=result['prediction'],
            confidence=result['confidence'],
            probabilities=result['probabilities']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        raise HTTPException(status_code=500, detail="Erro interno na predição")


@app.post("/batch_predict")
async def batch_predict(texts: list[str]):
    """
    Endpoint para predição em lote.
    
    Args:
        texts: Lista de textos para análise
        
    Returns:
        Lista de predições
    """
    try:
        if not model_loader or not model_loader.is_model_loaded():
            raise HTTPException(
                status_code=503,
                detail="Modelo não está disponível"
            )
        
        if len(texts) > 100:  # Limite de segurança
            raise HTTPException(
                status_code=400,
                detail="Máximo de 100 textos por requisição"
            )
        
        results = []
        for text in texts:
            if text.strip():
                result = model_loader.predict(text)
                results.append(result)
            else:
                results.append({
                    "prediction": "error",
                    "confidence": 0.0,
                    "probabilities": {"real": 0.0, "fake": 0.0},
                    "error": "Texto vazio"
                })
        
        return {"predictions": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na predição em lote: {e}")
        raise HTTPException(status_code=500, detail="Erro interno na predição em lote")


@app.get("/model/info")
async def get_model_info():
    """Retorna informações sobre o modelo carregado."""
    try:
        if not model_loader or not model_loader.is_model_loaded():
            return {"status": "no_model", "message": "Nenhum modelo carregado"}
        
        info = model_loader.get_model_info()
        return {"status": "loaded", "model_info": info}
        
    except Exception as e:
        logger.error(f"Erro ao obter info do modelo: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter informações do modelo")


@app.post("/model/reload")
async def reload_model():
    """Recarrega o modelo do S3."""
    try:
        if not model_loader:
            raise HTTPException(status_code=503, detail="Model loader não inicializado")
        
        await model_loader.load_model()
        return {"message": "Modelo recarregado com sucesso"}
        
    except Exception as e:
        logger.error(f"Erro ao recarregar modelo: {e}")
        raise HTTPException(status_code=500, detail="Erro ao recarregar modelo")


if __name__ == "__main__":
    # Configuração para desenvolvimento
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )