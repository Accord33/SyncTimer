# Python 3.13の公式イメージを使用
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt pyproject.toml ./

# Pythonの依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# アプリケーションを起動
CMD ["python", "app.py"]
