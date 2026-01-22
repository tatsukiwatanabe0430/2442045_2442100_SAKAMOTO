📚 My Library App

Flask と PostgreSQL を用いて作成した 蔵書管理・レビュー共有 Web アプリ です。
ユーザーごとに本を管理でき、レビュー投稿・他ユーザーのレビュー閲覧・コメント（レビュー交換）が可能です。

🔧 使用技術

Python 3.x

Flask

Flask-SQLAlchemy

PostgreSQL

HTML / CSS (Jinja2)

Werkzeug (パスワードハッシュ)

✨ 主な機能
👤 ユーザー機能

ユーザー登録

ログイン / ログアウト

セッション管理

📖 蔵書管理

本の追加・編集・削除

読書状態管理（未読 / 読書中 / 読了）

ジャンル設定

評価（★1〜5）

📝 レビュー機能

本に対するレビュー投稿

他ユーザーのレビュー閲覧

レビュー一覧表示（新着順）

💬 レビュー交換（コメント）

他ユーザーのレビューにコメント投稿

レビューに紐づいたコメント閲覧

📂 ディレクトリ構成
│
├─ app.py              # Flaskアプリ本体
├─ models.py           # DBモデル定義
├─ config.py           # DB設定
├─ .env                # 環境変数（DB接続情報）
│
├─ templates/
│   ├─ base.html
│   ├─ login.html
│   ├─ register.html
│   ├─ books.html
│   ├─ add_book.html
│   ├─ edit_book.html
│   ├─ reviews.html
│   ├─ add_review.html
│   └─ comments.html
│
└─ static/
    └─ style.css

🗄️ データベース設計（正規化）

本アプリは 第3正規形（3NF） を意識して設計されています。

主なテーブル

users（ユーザー）

books（蔵書）

reviews（レビュー）

comments（コメント）

関係

users 1 ── * books

users 1 ── * reviews

books 1 ── * reviews

reviews 1 ── * comments

冗長なデータを持たず、外部キーで関連付けています。

⚙️ セットアップ手順
1️⃣ 仮想環境作成 & 有効化
python -m venv venv
venv\Scripts\activate   # Windows

2️⃣ 必要ライブラリをインストール
pip install flask flask-sqlalchemy psycopg2-binary python-dotenv

3️⃣ .env を作成
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=my_library_db
SECRET_KEY=supersecretkey

4️⃣ PostgreSQL にデータベース作成
CREATE DATABASE my_library_db;

5️⃣ アプリ起動
python app.py


ブラウザで以下にアクセス：

http://127.0.0.1:5000

デモ動画に関して要領の関係上アップデートできないため、以下のリンクより閲覧いただきたいです。よろしくお願いいたします。

https://drive.google.com/file/d/1gfbv99k5_mcSwyAingK_ffEHEzCCJjwe/view?usp=sharing
