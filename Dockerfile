# Python 3.13の公式イメージを使用
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール
RUN apt-get update

# 依存関係ファイルをコピー
COPY requirements.txt ./

# Pythonの依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY ./app .

# ポート8000を公開
EXPOSE 8000

# アプリケーションを起動
CMD ["python", "app.py"]
