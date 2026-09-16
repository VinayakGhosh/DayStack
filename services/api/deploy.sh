#!/bin/bash
set -e

ECR_REGISTRY="017601971158.dkr.ecr.ap-south-1.amazonaws.com"
IMAGE_NAME="proj_task_backend"
FULL_IMAGE="$ECR_REGISTRY/$IMAGE_NAME"
EC2_USER="ubuntu"
EC2_HOST="65.2.144.240"          # we'll fill this in after Step 4


echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ap-south-1 | \
    docker login --username AWS --password-stdin $ECR_REGISTRY

echo "🏗️ Building image..."
docker build -t $IMAGE_NAME .

echo "🏷️ Tagging image..."
docker tag $IMAGE_NAME:latest $FULL_IMAGE:latest

echo "📤 Pushing to ECR..."
docker push $FULL_IMAGE:latest

echo "🚀 Deploying on EC2..."
ssh $EC2_USER@$EC2_HOST << 'EOF'
    aws ecr get-login-password --region ap-south-1 | \
        docker login --username AWS --password-stdin 017601971158.dkr.ecr.ap-south-1.amazonaws.com
    
    cd ~/infra
    docker compose pull backend
    docker compose up -d --no-deps backend
    
    echo "✅ Backend deployed!"
    docker compose ps
EOF