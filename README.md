![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green?logo=flask)
![SocketIO](https://img.shields.io/badge/SocketIO-5.3.6-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow)

# SyncTimer

リアルタイム共有タイマーアプリケーション - 複数のユーザーが同じタイマーを同期して利用できるWebアプリケーション

## 目次

- [プロジェクト概要](#プロジェクト概要)
- [使用技術](#使用技術)
- [開発環境構築方法](#開発環境構築方法)
- [環境変数とコマンド一覧](#環境変数とコマンド一覧)
- [ディレクトリ構成](#ディレクトリ構成)
- [トラブルシューティング](#トラブルシューティング)

## プロジェクト概要

SyncTimerは、WebSocketを使用したリアルタイム共有タイマーアプリケーションです。複数のユーザーが同じタイマーを同期して使用でき、以下の機能を提供します：

### 主要機能
- ⏰ **リアルタイム同期**: 全ユーザー間でタイマー状態が即座に同期
- ⏯️ **タイマー制御**: 開始、停止、一時停止、再開機能
- 📱 **レスポンシブデザイン**: デスクトップ・モバイル対応
- 🔄 **自動接続管理**: 接続時に現在のタイマー状態を自動取得
- 🚀 **軽量アーキテクチャ**: Flask + SocketIOによるシンプルな構成

### 使用シーン
- チーム作業でのポモドーロタイマー
- オンライン会議のタイムキーピング
- 勉強会やワークショップでの時間管理

## 使用技術

| カテゴリ | 技術 | バージョン |
|---------|------|-----------|
| **Backend** | Python | 3.13 |
| | Flask | 2.3.3 |
| | Flask-SocketIO | 5.3.6 |
| **Frontend** | HTML5/CSS3 | - |
| | JavaScript (ES6+) | - |
| | Socket.IO Client | 4.7.2 |
| **インフラ** | Docker | - |
| | Docker Compose | - |

## 開発環境構築方法

### 前提条件
- Docker & Docker Compose がインストール済み
- Git がインストール済み

### セットアップ手順

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/Accord33/SyncTimer.git
   cd SyncTimer
   ```

2. **Docker環境での起動**
   ```bash
   # コンテナのビルドと起動
   docker-compose up --build
   
   # バックグラウンドで起動する場合
   docker-compose up -d --build
   ```

3. **アプリケーションへのアクセス**
   ```
   http://localhost:8000
   ```

4. **開発モードでの起動（ローカル環境）**
   ```bash
   # 依存関係のインストール
   pip install -r requirements.txt
   
   # アプリケーションの起動
   cd app
   python app.py
   ```

## 環境変数とコマンド一覧

### 環境変数

現在、環境変数による設定は使用していませんが、本番環境では以下の設定を推奨します：

| 変数名 | 説明 | デフォルト値 |
|--------|------|------------|
| `FLASK_ENV` | Flask実行環境 | `production` |
| `SECRET_KEY` | Flask秘密鍵 | `timer_secret_key` |
| `PORT` | アプリケーションポート | `8000` |

### Docker Compose コマンド

```bash
# アプリケーションの起動
docker-compose up

# バックグラウンドで起動
docker-compose up -d

# ログの確認
docker-compose logs -f

# コンテナの停止
docker-compose down

# コンテナの再ビルド
docker-compose up --build

# コンテナの削除（データも削除）
docker-compose down -v
```

### 開発用コマンド

```bash
# 依存関係の追加
pip install [package-name]
pip freeze > requirements.txt

# Dockerイメージのビルド
docker build -t synctimer .

# 単体でコンテナ実行
docker run -p 8000:8000 synctimer
```

## ディレクトリ構成

```
SyncTimer/
│
├── app/                    # アプリケーションコード
│   ├── app.py             # メインアプリケーション
│   ├── pyproject.toml     # Python プロジェクト設定
│   ├── uv.lock           # 依存関係ロックファイル
│   └── templates/         # HTMLテンプレート
│       └── index.html     # メインページ
│
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile            # Dockerイメージ定義
├── requirements.txt      # Python依存関係
├── synctimer.yaml       # Kubernetes設定
└── README.md            # プロジェクト説明書
```

### 主要ファイルの説明

- **`app/app.py`**: FlaskアプリケーションとSocketIOイベントハンドラー
- **`app/templates/index.html`**: フロントエンドUI（HTML/CSS/JavaScript）
- **`docker-compose.yml`**: 開発環境用のコンテナ設定
- **`synctimer.yaml`**: Kubernetes本番環境用の設定

## トラブルシューティング

### よくある問題と解決策

#### 1. ポート8000が既に使用されている
```bash
# 使用中のポートを確認
lsof -i :8000

# プロセスを停止
kill -9 [PID]

# または別のポートを使用
docker-compose run -p 8001:8000 synctimer
```

#### 2. WebSocketの接続エラー
- **症状**: タイマーの同期が動作しない
- **解決策**: 
  - ブラウザのコンソールでエラーを確認
  - ネットワーク設定でWebSocketが許可されているか確認
  - CORS設定を確認（`cors_allowed_origins="*"`）

#### 3. Dockerビルドエラー
```bash
# キャッシュをクリアして再ビルド
docker-compose build --no-cache

# Dockerの全体クリーンアップ
docker system prune -a
```

#### 4. 依存関係のエラー
```bash
# requirements.txtの再生成
pip freeze > requirements.txt

# 仮想環境の再作成
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

#### 5. タイマーの動作が不安定
- **症状**: タイマーが正確に動作しない
- **解決策**:
  - ブラウザの開発者ツールでJavaScriptエラーを確認
  - 複数のブラウザタブで同時実行していないか確認
  - サーバーの時刻同期を確認

### ログの確認方法

```bash
# Docker Composeログ
docker-compose logs -f synctimer

# Dockerコンテナ内でのデバッグ
docker-compose exec synctimer /bin/bash
```

### デバッグモードでの実行

```bash
# 開発モードで起動（詳細ログ出力）
cd app
FLASK_DEBUG=1 python app.py
```