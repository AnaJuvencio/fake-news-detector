#!/bin/bash

# Script de inicialização do LocalStack para criar bucket S3 e configurar ambiente

set -e

echo "Iniciando configuração do LocalStack..."

# Aguarda LocalStack estar pronto
echo "Aguardando LocalStack ficar disponível..."
until curl -s http://localhost:4566/health > /dev/null; do
  echo "LocalStack ainda não está pronto, aguardando..."
  sleep 2
done

echo "LocalStack está pronto! Configurando recursos..."

# Configuração do cliente AWS para LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Instala AWS CLI se não estiver disponível
if ! command -v aws &> /dev/null; then
    echo "Instalando AWS CLI..."
    pip install awscli
fi

# Configura endpoint do LocalStack
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set default.region us-east-1

# Função para executar comandos AWS com endpoint LocalStack
awslocal() {
    aws --endpoint-url=http://localhost:4566 "$@"
}

echo "Criando bucket S3 para modelos..."

# Cria bucket para armazenar modelos
BUCKET_NAME="fake-news-models"
awslocal s3 mb s3://$BUCKET_NAME

# Verifica se o bucket foi criado
if awslocal s3 ls s3://$BUCKET_NAME > /dev/null 2>&1; then
    echo "Bucket '$BUCKET_NAME' criado com sucesso!"
else
    echo "Erro ao criar bucket '$BUCKET_NAME'"
    exit 1
fi

# Cria estrutura de pastas no bucket
echo "Criando estrutura de pastas no bucket..."
awslocal s3api put-object --bucket $BUCKET_NAME --key models/
awslocal s3api put-object --bucket $BUCKET_NAME --key experiments/
awslocal s3api put-object --bucket $BUCKET_NAME --key data/

# Se existir um modelo local, faz upload
MODEL_DIR="/tmp/localstack/models"
if [ -d "$MODEL_DIR" ]; then
    echo "Fazendo upload de modelos locais..."
    for model_file in "$MODEL_DIR"/*.joblib; do
        if [ -f "$model_file" ]; then
            filename=$(basename "$model_file")
            echo "Uploading $filename..."
            awslocal s3 cp "$model_file" s3://$BUCKET_NAME/models/
        fi
    done
fi

# Cria um modelo dummy se não existir nenhum
echo "Verificando se existem modelos no bucket..."
MODEL_COUNT=$(awslocal s3 ls s3://$BUCKET_NAME/models/ --recursive | grep -c ".joblib" || echo "0")

if [ "$MODEL_COUNT" -eq "0" ]; then
    echo "Nenhum modelo encontrado. Criando modelos dummy..."
    
    # Cria script Python temporário para gerar modelo dummy
    cat > /tmp/create_dummy_model.py << 'EOF'
import os
import sys
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer

# Dados dummy para treinamento
dummy_texts = [
    "This is a real news article about politics",
    "Breaking: Scientists discover new species",
    "FAKE: Aliens invade Earth tomorrow",
    "Economic growth shows positive trends", 
    "HOAX: Celebrities endorse miracle cure",
    "Sports team wins championship game",
    "FALSE: Government announces fake policy"
]

dummy_labels = [0, 0, 1, 0, 1, 0, 1]  # 0 = real, 1 = fake

# Cria e treina vectorizer
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
X = vectorizer.fit_transform(dummy_texts)

# Cria e treina modelo
model = LogisticRegression(random_state=42)
model.fit(X, dummy_labels)

# Salva modelo e vectorizer
model_dir = '/tmp/dummy_models'
os.makedirs(model_dir, exist_ok=True)

joblib.dump(model, os.path.join(model_dir, 'best_model.joblib'))
joblib.dump(vectorizer, os.path.join(model_dir, 'vectorizer.joblib'))

print("Modelos dummy criados com sucesso!")
print(f"Acurácia no conjunto de treino: {model.score(X, dummy_labels):.2f}")
EOF

    # Executa script Python
    python3 /tmp/create_dummy_model.py
    
    # Upload dos modelos dummy
    awslocal s3 cp /tmp/dummy_models/best_model.joblib s3://$BUCKET_NAME/models/
    awslocal s3 cp /tmp/dummy_models/vectorizer.joblib s3://$BUCKET_NAME/models/
    
    echo "Modelos dummy criados e enviados para S3!"
fi

# Lista conteúdo final do bucket
echo "Conteúdo do bucket '$BUCKET_NAME':"
awslocal s3 ls s3://$BUCKET_NAME --recursive

# Configura políticas de acesso do bucket (opcional)
echo "Configurando política de acesso do bucket..."
cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

awslocal s3api put-bucket-policy --bucket $BUCKET_NAME --policy file:///tmp/bucket-policy.json

echo "Configuração do LocalStack concluída com sucesso!"
echo "Bucket S3: s3://$BUCKET_NAME"
echo "Endpoint: http://localhost:4566"
echo ""
echo "Para testar o acesso:"
echo "aws --endpoint-url=http://localhost:4566 s3 ls s3://$BUCKET_NAME --recursive"