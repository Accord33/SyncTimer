#!/bin/bash

# Docker環境でのタイマーアプリ起動スクリプト

echo "SyncTimer Dockerアプリケーションを起動しています..."
echo "アプリケーションはポート8001で起動します: http://localhost:8001"

# Docker Composeが利用可能かチェック
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "エラー: Docker ComposeまたはDocker Compose V2が見つかりません。"
    echo "Dockerがインストールされていることを確認してください。"
    exit 1
fi

# 本番環境で起動
echo "本番環境モードで起動中..."
$COMPOSE_CMD up --build synctimer
