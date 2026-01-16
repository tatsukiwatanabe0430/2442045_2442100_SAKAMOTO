import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
import os

DB_PATH = os.path.abspath("my_bookshelf.db")

# =========================
# DB初期化 + サンプル追加
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 蔵書テーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            status TEXT DEFAULT '未読',
            finished_date DATE,
            reread BOOLEAN DEFAULT 0
        )
    ''')

    # レビュー
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            book_id INTEGER,
            user_name TEXT,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            review_text TEXT,
            review_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')

    # 操作履歴
    c.execute('''
        CREATE TABLE IF NOT EXISTS book_history (
            id INTEGER PRIMARY KEY,
            action TEXT,
            book_title TEXT,
            action_date DATE DEFAULT CURRENT_DATE
        )
    ''')

    # ===== サンプル追加 =====
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ("ハリーポッターと賢者の石", "J.K.ローリング", "9780439708180"),
            ("ノルウェイの森", "村上春樹", "9784103534226"),
            ("星の王子さま", "サン＝テグジュペリ", "9782070612758")
        ]
        for title, author, isbn in sample_books:
            c.execute("INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)", (title, author, isbn))
        conn.commit()

    c.execute("SELECT COUNT(*) FROM reviews")
    if c.fetchone()[0] == 0:
        c.execute("SELECT id FROM books WHERE title=?", ("ハリーポッターと賢者の石",))
        hp_id = c.fetchone()[0]
        c.execute("SELECT id FROM books WHERE title=?", ("ノルウェイの森",))
        nor_id = c.fetchone()[0]
        sample_reviews = [
            (hp_id, "Alice", 5, "魔法の世界に夢中になった！"),
            (hp_id, "Bob", 4, "楽しいけど少し長い"),
            (nor_id, "Alice", 4, "心に残る物語")
        ]
        for book_id, user, rating, text in sample_reviews:
            c.execute("INSERT INTO reviews (book_id, user_name, rating, review_text) VALUES (?, ?, ?, ?)",
                      (book_id, user, rating, text))
        conn.commit()

    conn.close()

# =========================
# book_idカラム互換
# =========================
def get_book_id_column(conn):
    cursor = conn.execute("PRAGMA table_info(books)")
    columns = [col[1] for col in cursor.fetchall()]
    if "book_id" in columns:
        return "book_id"
    else:
        return "id"

# =========================
# メイン
# =========================
def main():
    st.set_page_config(page_title="マイライブラリ", layout="wide")
    st.title("📚 マイライブラリ")

    if "db_init" not in st.session_state:
        init_db()
        st.session_state["db_init"] = True

    if "user_name" not in st.session_state:
        login()
        return

    menu = st.sidebar.selectbox("メニュー", ["蔵書一覧", "蔵書検索", "ランキング", "蔵書管理"])

    if menu == "蔵書一覧":
        display_books()
    elif menu == "蔵書検索":
        search_books()
    elif menu == "ランキング":
        display_ranking()
    elif menu == "蔵書管理":
        manage_books()

# =========================
# ログイン
# =========================
def login():
    st.subheader("ユーザー名を入力してください")
    name = st.text_input("ユーザー名")
    if st.button("開始"):
        if name.strip():
            st.session_state["user_name"] = name.strip()
            st.rerun()
        else:
            st.error("ユーザー名を入力してください")

# =========================
# 蔵書一覧
# =========================
def display_books():
    st.header("📖 蔵書一覧")

    conn = sqlite3.connect(DB_PATH)
    book_id_col = get_book_id_column(conn)
    df = pd.read_sql_query(f"SELECT {book_id_col}, title, author, status, finished_date, reread FROM books ORDER BY title", conn)
    conn.close()

    df["再読"] = df["reread"].apply(lambda x: "✔" if x else "")
    df_display = df.rename(columns={book_id_col:"ID", "title":"タイトル", "author":"著者", "status":"ステータス", "finished_date":"読了日"})
    st.dataframe(df_display[["ID","タイトル","著者","ステータス","読了日","再読"]], use_container_width=True)

    if not df_display.empty:
        selected = st.selectbox("詳細を見る本を選択", [""] + df_display["タイトル"].tolist())
        if selected:
            book_id = df_display[df_display["タイトル"] == selected]["ID"].iloc[0]
            display_reviews(book_id)
            add_or_update_review(book_id)

# =========================
# 蔵書検索
# =========================
def search_books():
    st.header("🔍 蔵書検索")
    keyword = st.text_input("タイトルで検索")
    if keyword:
        conn = sqlite3.connect(DB_PATH)
        book_id_col = get_book_id_column(conn)
        df = pd.read_sql_query(f"SELECT {book_id_col} AS ID, title AS タイトル, author AS 著者, status AS ステータス FROM books WHERE title LIKE ?", conn, params=(f"%{keyword}%",))
        conn.close()
        st.dataframe(df, use_container_width=True)

# =========================
# レビュー表示
# =========================
def display_reviews(book_id):
    st.subheader("📝 読書メモ・評価")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, user_name, rating, review_text, review_date FROM reviews WHERE book_id=? ORDER BY review_date DESC", conn, params=(book_id,))
    conn.close()

    if not df.empty:
        df["星"] = df["rating"].apply(lambda x: "★"*x + "☆"*(5-x))
        df_display = df.rename(columns={"id":"ID","user_name":"ユーザー","rating":"評価","review_text":"感想","review_date":"日付"})
        st.dataframe(df_display[["ID","ユーザー","評価","星","感想","日付"]], use_container_width=True)
    else:
        st.write("まだレビューはありません。")

# =========================
# レビュー追加・更新・削除
# =========================
def add_or_update_review(book_id):
    with st.expander("自分のレビューを追加・更新・削除"):
        user_name = st.session_state["user_name"]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, rating, review_text FROM reviews WHERE book_id=? AND user_name=?", (book_id, user_name))
        existing = c.fetchone()

        if existing:
            review_id, rating_old, text_old = existing
            rating = st.slider("評価", 1, 5, rating_old)
            text = st.text_area("感想", text_old)
            col1, col2 = st.columns(2)
            if col1.button("更新"):
                c.execute("UPDATE reviews SET rating=?, review_text=?, review_date=? WHERE id=?", (rating, text, datetime.now().date(), review_id))
                conn.commit()
                st.success("レビューを更新しました")
            if col2.button("削除"):
                c.execute("DELETE FROM reviews WHERE id=?", (review_id,))
                conn.commit()
                st.success("レビューを削除しました")
        else:
            rating = st.slider("評価", 1, 5, 3)
            text = st.text_area("感想")
            if st.button("保存"):
                c.execute("INSERT INTO reviews (book_id, user_name, rating, review_text) VALUES (?, ?, ?, ?)", (book_id, user_name, rating, text))
                conn.commit()
                st.success("レビューを追加しました")
        conn.close()

# =========================
# ランキング
# =========================
def display_ranking():
    st.header("⭐ お気に入りランキング")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT title AS タイトル, author AS 著者, ROUND(AVG(reviews.rating),1) AS 平均評価
        FROM books
        LEFT JOIN reviews ON books.id = reviews.book_id
        GROUP BY books.id
        ORDER BY 平均評価 DESC
    ''', conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# =========================
# 蔵書管理
# =========================
def manage_books():
    st.header("🛠 蔵書管理")
    action = st.selectbox("操作", ["追加", "更新", "削除"])

    if action == "追加":
        with st.form("add_book"):
            title = st.text_input("タイトル")
            author = st.text_input("著者")
            isbn = st.text_input("ISBN")
            status = st.selectbox("読書ステータス", ["未読", "読書中", "読了"])
            reread = st.checkbox("再読したい")
            submitted = st.form_submit_button("追加")
            if submitted:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO books (title, author, isbn, status, reread) VALUES (?, ?, ?, ?, ?)", (title, author, isbn, status, int(reread)))
                    c.execute("INSERT INTO book_history (action, book_title) VALUES (?, ?)", ("追加", title))
                    conn.commit()
                    st.success("蔵書を追加しました")
                except sqlite3.IntegrityError:
                    st.error("ISBNが重複しています")
                conn.close()

    elif action == "更新":
        book_id = st.number_input("更新する本のID", min_value=1, step=1)
        new_status = st.selectbox("新しい読書ステータス", ["未読", "読書中", "読了"])
        reread = st.checkbox("再読したい")
        if st.button("更新"):
            finished_date = datetime.now().date() if new_status=="読了" else None
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE books SET status=?, finished_date=?, reread=? WHERE id=?", (new_status, finished_date, int(reread), book_id))
            conn.commit()
            conn.close()
            st.success("更新しました")

    elif action == "削除":
        book_id = st.number_input("削除する本のID", min_value=1, step=1)
        confirm = st.checkbox("本当に削除しますか？")
        if st.button("削除") and confirm:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT title FROM books WHERE id=?", (book_id,))
            book = c.fetchone()
            if book:
                c.execute("DELETE FROM books WHERE id=?", (book_id,))
                c.execute("INSERT INTO book_history (action, book_title) VALUES (?, ?)", ("削除", book[0]))
                conn.commit()
                st.success("削除しました")
            else:
                st.error("本が見つかりません")
            conn.close()

    display_history()

# =========================
# 操作履歴
# =========================
def display_history():
    st.subheader("📜 操作履歴")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM book_history ORDER BY action_date DESC", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)

# =========================
if __name__=="__main__":
    main()
