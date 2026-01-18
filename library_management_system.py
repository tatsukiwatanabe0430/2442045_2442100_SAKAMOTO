import sqlite3
import streamlit as st
import pandas as pd
import os

DB_PATH = os.path.abspath("my_bookshelf.db")

# =========================
# DB初期化
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # テーブル作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            status TEXT DEFAULT '未読',
            finished_date DATE,
            reread BOOLEAN DEFAULT 0,
            rating INTEGER DEFAULT 0
        )
    ''')

    # ratingカラム追加（既存DB用）
    c.execute("PRAGMA table_info(books)")
    columns = [info[1] for info in c.fetchall()]
    if "rating" not in columns:
        c.execute("ALTER TABLE books ADD COLUMN rating INTEGER DEFAULT 0")

    # 初期データ
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        books = [
            ("ハリーポッターと賢者の石", "J.K.ローリング"),
            ("ノルウェイの森", "村上春樹"),
            ("星の王子さま", "サン＝テグジュペリ")
        ]
        for b in books:
            c.execute("INSERT INTO books (title, author) VALUES (?,?)", b)
        conn.commit()
    conn.close()

# =========================
# メイン
# =========================
def main():
    st.set_page_config(page_title="マイライブラリ", layout="wide")
    st.title("📚 マイライブラリ")

    if "init" not in st.session_state:
        init_db()
        st.session_state["init"] = True

    if "user_name" not in st.session_state:
        login()
        return

    menu = st.sidebar.selectbox("メニュー", ["蔵書一覧", "蔵書管理", "蔵書追加"])

    if menu == "蔵書一覧":
        display_books_card()
    elif menu == "蔵書管理":
        manage_books()
    elif menu == "蔵書追加":
        add_book()

# =========================
# ログイン
# =========================
def login():
    st.subheader("ユーザー名を入力してください")
    name = st.text_input("ユーザー名")
    if st.button("開始") and name:
        st.session_state["user_name"] = name
        st.rerun()

# =========================
# 蔵書一覧（カードUI）
# =========================
def display_books_card():
    st.header("📖 蔵書一覧")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM books ORDER BY title", conn)
    conn.close()

    if df.empty:
        st.info("蔵書がありません")
        return

    colors = {"未読": "#FFECB3", "読書中": "#B3E5FC", "読了": "#C8E6C9"}  # カード色
    icons = {"未読": "📕", "読書中": "📖", "読了": "📘"}  # ステータスアイコン

    # 3列グリッド
    cols = st.columns(3)
    for idx, row in df.iterrows():
        with cols[idx % 3]:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color:{colors.get(row['status'],'#EEE')};
                                padding:15px;
                                border-radius:15px;
                                text-align:center;
                                box-shadow: 3px 3px 10px rgba(0,0,0,0.1);">
                        <h4>{row['title']}</h4>
                        <p><i>{row['author']}</i></p>
                        <p style="font-size:1.2em;">{'⭐'*row['rating']}{'☆'*(5-row['rating'])}</p>
                        <p style="font-size:2em;">{icons.get(row['status'],'')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# =========================
# 蔵書管理（検索・編集・削除・評価）
# =========================
def manage_books():
    st.header("🛠 蔵書管理")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM books ORDER BY title", conn)

    if df.empty:
        st.info("蔵書がありません")
        conn.close()
        return

    # 検索フォーム
    st.subheader("検索で絞り込み")
    search_title = st.text_input("タイトルで検索")
    search_author = st.text_input("著者で検索")

    filtered_df = df[
        df["title"].str.contains(search_title, case=False) &
        df["author"].str.contains(search_author, case=False)
    ] if (search_title or search_author) else df

    if filtered_df.empty:
        st.info("該当する蔵書がありません")
        conn.close()
        return

    # 編集選択
    title_list = filtered_df["title"].tolist()
    selected_title = st.selectbox("編集する本", title_list)
    book = filtered_df[filtered_df["title"] == selected_title].iloc[0]

    with st.form("edit_book"):
        new_title = st.text_input("タイトル", book["title"])
        author = st.text_input("著者", book["author"])
        status = st.selectbox("ステータス", ["未読", "読書中", "読了"],
                              index=["未読", "読書中", "読了"].index(book["status"]))
        reread = st.checkbox("再読したい", bool(book["reread"]))
        rating = st.slider("評価（⭐1-5）", 0, 5, int(book["rating"]))

        col1, col2 = st.columns(2)
        if col1.form_submit_button("更新"):
            conn.execute(
                "UPDATE books SET title=?, author=?, status=?, reread=?, rating=? WHERE id=?",
                (new_title, author, status, int(reread), int(rating), int(book["id"]))
            )
            conn.commit()
            st.success("更新しました")
            st.rerun()

        if col2.form_submit_button("削除"):
            conn.execute("DELETE FROM books WHERE id=?", (int(book["id"]),))
            conn.commit()
            st.warning("削除しました")
            st.rerun()

    conn.close()

# =========================
# 蔵書追加
# =========================
def add_book():
    st.header("➕ 蔵書追加")

    with st.form("add_book_form"):
        title = st.text_input("タイトル")
        author = st.text_input("著者")
        status = st.selectbox("ステータス", ["未読", "読書中", "読了"])
        reread = st.checkbox("再読したい")
        rating = st.slider("評価（⭐1-5）", 0, 5, 0)

        if st.form_submit_button("追加"):
            if not title or not author:
                st.warning("タイトルと著者は必須です")
                return

            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT INTO books (title, author, status, reread, rating) VALUES (?,?,?,?,?)",
                (title, author, status, int(reread), int(rating))
            )
            conn.commit()
            conn.close()
            st.success(f"「{title}」を追加しました")
            st.rerun()

# =========================
if __name__ == "__main__":
    main()
