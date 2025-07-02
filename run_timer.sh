#!/bin/bash

# 仮想環境の作成（存在しない場合）
if [ ! -d "venv" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
echo "仮想環境をアクティベート中..."
source venv/bin/activate

# パッケージのインストール
echo "必要なパッケージをインストール中..."
pip install -r requirements.txt

# アプリケーションの起動
echo "タイマーアプリを起動中..."
echo "ブラウザで http://localhost:5000 にアクセスしてください"
echo "複数のブラウザタブやデバイスで同じURLを開くと、タイマーが同期されます"
python app.py
