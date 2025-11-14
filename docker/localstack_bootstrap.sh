#!/bin/bash
# Shebang: indica que este é um script Bash (linguagem de script do Linux)

# Script de inicialização do LocalStack
# Objetivo: Criar bucket S3 e configurar ambiente automaticamente quando o LocalStack iniciar

# set -e: Se qualquer comando der erro, o script para imediatamente (fail-fast)
set -e

echo "Iniciando configuração do LocalStack..."

# ============================================
# PASSO 1: Aguardar LocalStack estar pronto
# ============================================
echo "Aguardando LocalStack ficar disponível..."

# Loop até que o LocalStack responda OK
# until = "repita até que..."
# curl -s = faz requisição HTTP silenciosa (sem mostrar progresso)
# /health = endpoint que retorna status do LocalStack
# > /dev/null = joga a resposta no "lixo" (não mostra na tela)
until curl -s http://localhost:4566/health > /dev/null; do
  echo "LocalStack ainda não está pronto, aguardando..."
  sleep 2  # Espera 2 segundos antes de tentar novamente
done

echo "LocalStack está pronto! Configurando recursos..."

# ============================================
# PASSO 2: Configurar credenciais AWS fake
# ============================================
# export = torna a variável disponível para todos os comandos subsequentes
export AWS_ACCESS_KEY_ID=test           # Credencial fake (pode ser qualquer valor)
export AWS_SECRET_ACCESS_KEY=test       # Credencial fake (pode ser qualquer valor)
export AWS_DEFAULT_REGION=us-east-1     # Região AWS padrão

# ============================================
# PASSO 3: Verificar/Instalar AWS CLI
# ============================================
# AWS CLI = ferramenta de linha de comando para interagir com AWS (e LocalStack)
# if ! command -v aws = "se o comando 'aws' não existir..."
if ! command -v aws &> /dev/null; then
    echo "Instalando AWS CLI..."
    pip install awscli  # Instala o AWS CLI usando pip (Python)
fi

# Configura credenciais no AWS CLI
aws configure set aws_access_key_id test
aws configure set aws_secret_access_key test
aws configure set default.region us-east-1

# ============================================
# PASSO 4: Criar função helper para LocalStack
# ============================================
# awslocal(): função que adiciona automaticamente o endpoint do LocalStack
# "$@" = passa todos os argumentos para o comando aws
# Exemplo: awslocal s3 ls  →  aws --endpoint-url=http://localhost:4566 s3 ls
awslocal() {
    aws --endpoint-url=http://localhost:4566 "$@"
}

echo "Criando bucket S3 para modelos..."

# ============================================
# PASSO 5: Criar bucket S3
# ============================================
# Bucket = "pasta" no S3 onde você guarda arquivos
BUCKET_NAME="fake-news-models"

# s3 mb = make bucket (criar bucket)
# s3:// = protocolo do S3
awslocal s3 mb s3://$BUCKET_NAME

# ============================================
# PASSO 6: Verificar se bucket foi criado
# ============================================
# s3 ls = list (listar buckets ou objetos)
# > /dev/null 2>&1 = não mostra nada na tela (nem saída normal nem erros)
if awslocal s3 ls s3://$BUCKET_NAME > /dev/null 2>&1; then
    echo "Bucket '$BUCKET_NAME' criado com sucesso!"
else
    echo "Erro ao criar bucket '$BUCKET_NAME'"
    exit 1  # Sai do script com código de erro
fi

# ============================================
# PASSO 7: Criar estrutura de pastas no bucket
# ============================================
echo "Criando estrutura de pastas no bucket..."

# s3api put-object = cria um "objeto" (arquivo ou pasta) no S3
# --key = caminho/nome do objeto (terminar com / indica pasta)
awslocal s3api put-object --bucket $BUCKET_NAME --key models/
awslocal s3api put-object --bucket $BUCKET_NAME --key experiments/
awslocal s3api put-object --bucket $BUCKET_NAME --key data/

# ============================================
# PASSO 8: Fazer upload de modelos existentes
# ============================================
MODEL_DIR="/tmp/localstack/models"

# [ -d "$MODEL_DIR" ] = testa se o diretório existe
if [ -d "$MODEL_DIR" ]; then
    echo "Fazendo upload de modelos locais..."
    
    # Loop por todos os arquivos .joblib no diretório
    for model_file in "$MODEL_DIR"/*.joblib; do
        # [ -f "$model_file" ] = testa se é um arquivo (não pasta)
        if [ -f "$model_file" ]; then
            # basename = pega só o nome do arquivo (sem o caminho)
            filename=$(basename "$model_file")
            echo "Uploading $filename..."
            
            # s3 cp = copy (copiar arquivo para S3)
            awslocal s3 cp "$model_file" s3://$BUCKET_NAME/models/
        fi
    done
fi

# ============================================
# PASSO 9: Verificar se há modelos no bucket
# ============================================
echo "Verificando se existem modelos no bucket..."

# s3 ls --recursive = lista TODOS os arquivos recursivamente (em todas as subpastas)
# grep -c ".joblib" = conta quantas linhas contêm ".joblib"
# || echo "0" = se der erro (nenhum arquivo), retorna "0"
MODEL_COUNT=$(awslocal s3 ls s3://$BUCKET_NAME/models/ --recursive | grep -c ".joblib" || echo "0")

# ============================================
# PASSO 10: Criar modelos dummy (se não existir)
# ============================================
# [ "$MODEL_COUNT" -eq "0" ] = testa se a contagem é igual a zero
if [ "$MODEL_COUNT" -eq "0" ]; then
    echo "Nenhum modelo encontrado. Criando modelos dummy..."
    
    # cat > arquivo << 'EOF' = cria um arquivo com o conteúdo entre EOF e EOF
    # Aqui cria um script Python temporário
    cat > /tmp/create_dummy_model.py << 'EOF'
# ============================================
# Script Python: Criar modelo ML dummy
# ============================================
import os
import sys
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer

# Dados dummy para treinamento (notícias fake e reais de exemplo)
dummy_texts = [
    "This is a real news article about politics",
    "Breaking: Scientists discover new species",
    "FAKE: Aliens invade Earth tomorrow",
    "Economic growth shows positive trends", 
    "HOAX: Celebrities endorse miracle cure",
    "Sports team wins championship game",
    "FALSE: Government announces fake policy"
]

# Labels: 0 = real (verdadeira), 1 = fake (falsa)
dummy_labels = [0, 0, 1, 0, 1, 0, 1]

# TfidfVectorizer: converte texto em números (vetores) que o ML entende
# max_features=1000: usa no máximo 1000 palavras mais importantes
# stop_words='english': remove palavras comuns como "the", "is", "a"
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
X = vectorizer.fit_transform(dummy_texts)  # Transforma textos em matriz numérica

# LogisticRegression: algoritmo de ML para classificação (fake/real)
model = LogisticRegression(random_state=42)
model.fit(X, dummy_labels)  # Treina o modelo com os dados dummy

# Cria diretório para salvar os modelos
model_dir = '/tmp/dummy_models'
os.makedirs(model_dir, exist_ok=True)  # exist_ok=True: não dá erro se já existir

# joblib.dump: salva o modelo em arquivo .joblib (formato compactado)
joblib.dump(model, os.path.join(model_dir, 'best_model.joblib'))
joblib.dump(vectorizer, os.path.join(model_dir, 'vectorizer.joblib'))

print("Modelos dummy criados com sucesso!")
print(f"Acurácia no conjunto de treino: {model.score(X, dummy_labels):.2f}")
EOF

    # ============================================
    # Executar script Python e fazer upload
    # ============================================
    # python3 = executa o script Python criado acima
    python3 /tmp/create_dummy_model.py
    
    # Upload dos modelos dummy para o S3
    awslocal s3 cp /tmp/dummy_models/best_model.joblib s3://$BUCKET_NAME/models/
    awslocal s3 cp /tmp/dummy_models/vectorizer.joblib s3://$BUCKET_NAME/models/
    
    echo "Modelos dummy criados e enviados para S3!"
fi

# ============================================
# PASSO 11: Listar conteúdo do bucket
# ============================================
echo "Conteúdo do bucket '$BUCKET_NAME':"
# --recursive = mostra TODOS os arquivos, incluindo em subpastas
awslocal s3 ls s3://$BUCKET_NAME --recursive

# ============================================
# PASSO 12: Configurar política de acesso
# ============================================
echo "Configurando política de acesso do bucket..."

# Cria arquivo JSON com política de acesso público
# Esta política permite que qualquer um LEIA os arquivos (mas não escreva)
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

# s3api put-bucket-policy: aplica a política de acesso ao bucket
awslocal s3api put-bucket-policy --bucket $BUCKET_NAME --policy file:///tmp/bucket-policy.json

# ============================================
# FINALIZAÇÃO
# ============================================
echo "Configuração do LocalStack concluída com sucesso!"
echo "Bucket S3: s3://$BUCKET_NAME"
echo "Endpoint: http://localhost:4566"
echo ""
echo "Para testar o acesso:"
echo "aws --endpoint-url=http://localhost:4566 s3 ls s3://$BUCKET_NAME --recursive"