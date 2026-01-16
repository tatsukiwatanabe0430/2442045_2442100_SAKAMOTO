import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

DB_PATH = os.path.abspath("library.db")

# Database setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Books table
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            available BOOLEAN DEFAULT 1
        )
    ''')

    # Reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            book_id INTEGER,
            user_name TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            review_text TEXT,
            review_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')

    # Book history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS book_history (
            id INTEGER PRIMARY KEY,
            action TEXT NOT NULL,
            book_title TEXT NOT NULL,
            book_author TEXT NOT NULL,
            action_date DATE DEFAULT CURRENT_DATE
        )
    ''')



    conn.commit()
    conn.close()



# Streamlit app
def main():
    st.info(f"Using DB: {DB_PATH}")

    if 'db_initialized' not in st.session_state:
        init_db()
        st.session_state['db_initialized'] = True

    # ユーザー名入力（アプリ起動時に1回だけ）
    if 'current_user_name' not in st.session_state or not st.session_state['current_user_name']:
        st.title('図書館管理システム')
        st.header('ユーザー名を入力してください')
        user_name = st.text_input('ユーザー名')
        if st.button('確定'):
            if user_name.strip():
                # 識別子と表示名を分離
                st.session_state['current_user_name'] = user_name.strip()
                st.session_state['current_user_id'] = user_name.strip().lower()
                st.success(f'ユーザー名を {user_name} に設定しました。')
                st.rerun()
            else:
                st.error('ユーザー名を入力してください。')
        return  # ユーザー名が設定されるまで他の機能を表示しない

    # 改善5: 管理機能を管理者限定にする
    current_user_id = st.session_state.get('current_user_id', '')
    if current_user_id == 'admin':
        menu = ['登録されている本の一覧', '本の検索', 'ランキング', '本の管理']
    else:
        menu = ['登録されている本の一覧', '本の検索', 'ランキング']
    choice = st.sidebar.selectbox('メニュー', menu)

    if choice == '登録されている本の一覧':
        display_books()
    elif choice == '本の検索':
        search_books()
    elif choice == 'ランキング':
        display_ranking()
    elif choice == '本の管理':
        manage_books()

def display_books():
    st.header('登録されている本の一覧')

    # 改善3: 本の一覧画面に絞り込み機能を追加 - フィルタ追加
    author_filter = st.text_input('著者名で検索')

    # 不具合修正: display_books 関数の SQL を修正 - books 単体 SELECT
    query = '''
        SELECT books.id, books.title, books.author, books.isbn, books.available
        FROM books
    '''
    params = []

    conditions = []
    if author_filter:
        conditions.append('books.author LIKE ?')
        params.append(f'%{author_filter}%')

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    st.dataframe(df)

    # CRUD operations
    st.subheader('本の操作')

    # Create: Add new book
    with st.expander('新しい本を追加'):
        with st.form('add_book_display'):
            title = st.text_input('タイトル')
            author = st.text_input('著者')
            isbn = st.text_input('ISBN')
            submitted = st.form_submit_button('追加')
            if submitted:
                if not title.strip() or not author.strip():
                    st.error('タイトルと著者は必須です。')
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)', (title.strip(), author.strip(), isbn.strip()))
                        # Record history
                        c.execute('INSERT INTO book_history (action, book_title, book_author) VALUES (?, ?, ?)', ('add', title.strip(), author.strip()))
                        conn.commit()
                        st.success('本を追加しました')
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error('このISBNの本は既に登録されています。')
                    conn.close()

    # Update: Edit existing book
    with st.expander('本を編集'):
        book_options_update = df['title'].tolist()
        selected_book_update = st.selectbox('編集する本を選択', [''] + book_options_update, key='update_select')
        if selected_book_update:
            book_row = df[df['title'] == selected_book_update]
            if not book_row.empty:
                book_id = book_row['id'].iloc[0]
                current_title = book_row['title'].iloc[0]
                current_author = book_row['author'].iloc[0]
                current_isbn = book_row['isbn'].iloc[0]
                with st.form('update_book_display'):
                    new_title = st.text_input('タイトル', value=current_title)
                    new_author = st.text_input('著者', value=current_author)
                    new_isbn = st.text_input('ISBN', value=current_isbn)
                    submitted_update = st.form_submit_button('更新')
                    if submitted_update:
                        if not new_title.strip() or not new_author.strip():
                            st.error('タイトルと著者は必須です。')
                        else:
                            conn = sqlite3.connect(DB_PATH)
                            c = conn.cursor()
                            try:
                                c.execute('UPDATE books SET title=?, author=?, isbn=? WHERE id=?', (new_title.strip(), new_author.strip(), new_isbn.strip(), book_id))
                                conn.commit()
                                st.success('本を更新しました')
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error('このISBNの本は既に存在します。')
                            conn.close()

    # Delete: Remove book
    with st.expander('本を削除'):
        book_options_delete = df['title'].tolist()
        selected_book_delete = st.selectbox('削除する本を選択', [''] + book_options_delete, key='delete_select')
        if selected_book_delete:
            book_row = df[df['title'] == selected_book_delete]
            if not book_row.empty:
                book_id = book_row['id'].iloc[0]
                confirm_delete = st.checkbox('本当に削除しますか？', key='delete_confirm')
                if st.button('削除', key='delete_button'):
                    if confirm_delete:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute('SELECT title, author FROM books WHERE id=?', (book_id,))
                        book = c.fetchone()
                        if book:
                            title, author = book
                            c.execute('DELETE FROM books WHERE id=?', (book_id,))
                            # Record history
                            c.execute('INSERT INTO book_history (action, book_title, book_author) VALUES (?, ?, ?)', ('delete', title, author))
                            conn.commit()
                            st.success('本を削除しました')
                            st.rerun()
                        else:
                            st.error('指定された本が見つかりません。')
                        conn.close()
                    else:
                        st.error('削除を確認してください。')

    # Select book for reviews
    book_options = df['title'].tolist()
    selected_book = st.selectbox('レビューを表示する本を選択', [''] + book_options)
    if selected_book:
        book_row = df[df['title'] == selected_book]
        if not book_row.empty:
            book_id = book_row['id'].iloc[0]
            display_reviews(book_id)
            add_review(book_id)
        else:
            st.error('選択された本が見つかりません。')

def manage_books():
    st.header('本の管理')

    display_history()

    # CRUD operations
    operation = st.selectbox('操作', ['追加', '更新', '削除'])

    if operation == '追加':
        with st.form('add_book'):
            title = st.text_input('タイトル')
            author = st.text_input('著者')
            isbn = st.text_input('ISBN')
            submitted = st.form_submit_button('追加')
            if submitted:
                # 改善7: UX改善 - 必須入力検証
                if not title.strip() or not author.strip():
                    st.error('タイトルと著者は必須です。')
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)', (title.strip(), author.strip(), isbn.strip()))
                        # Record history
                        c.execute('INSERT INTO book_history (action, book_title, book_author) VALUES (?, ?, ?)', ('add', title.strip(), author.strip()))
                        conn.commit()
                        st.success('本を追加しました')
                    except sqlite3.IntegrityError:
                        st.error('このISBNの本は既に登録されています。')
                    conn.close()

    elif operation == '更新':
        book_id = st.number_input('本のID', min_value=1, step=1)
        with st.form('update_book'):
            title = st.text_input('新しいタイトル')
            author = st.text_input('新しい著者')
            isbn = st.text_input('新しいISBN')
            submitted = st.form_submit_button('更新')
            if submitted:
                # 改善7: UX改善 - 必須入力検証
                if not title.strip() or not author.strip():
                    st.error('タイトルと著者は必須です。')
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('SELECT id FROM books WHERE id=?', (book_id,))
                    if c.fetchone():
                        try:
                            c.execute('UPDATE books SET title=?, author=?, isbn=? WHERE id=?', (title.strip(), author.strip(), isbn.strip(), book_id))
                            conn.commit()
                            st.success('本を更新しました')
                        except sqlite3.IntegrityError:
                            st.error('このISBNの本は既に存在します。')
                    else:
                        st.error('指定されたIDの本が見つかりません。')
                    conn.close()

    elif operation == '削除':
        # 改善6: 本の削除時に確認操作を追加 - 確認チェック追加
        book_id = st.number_input('本のID', min_value=1, step=1)
        confirm_delete = st.checkbox('本当に削除しますか？')
        if st.button('削除'):
            if confirm_delete:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT title, author FROM books WHERE id=?', (book_id,))
                book = c.fetchone()
                if book:
                    title, author = book
                    c.execute('DELETE FROM books WHERE id=?', (book_id,))
                    # Record history
                    c.execute('INSERT INTO book_history (action, book_title, book_author) VALUES (?, ?, ?)', ('delete', title, author))
                    conn.commit()
                    st.success('本を削除しました')
                else:
                    st.error('指定されたIDの本が見つかりません。')
                conn.close()
            else:
                st.error('削除を確認してください。')



def display_reviews(book_id):
    st.subheader('レビュー')
    conn = sqlite3.connect(DB_PATH)
    df_reviews = pd.read_sql_query('''
        SELECT reviews.rating, reviews.review_text, reviews.review_date, reviews.user_name
        FROM reviews
        WHERE reviews.book_id = ?
        ORDER BY reviews.review_date DESC
    ''', conn, params=(book_id,))
    conn.close()
    if not df_reviews.empty:
        st.dataframe(df_reviews)
        avg_rating = df_reviews['rating'].mean()
        # 改善4: 評価の表示を星で表現 - 星表示追加
        stars = '★' * int(round(avg_rating)) + '☆' * (5 - int(round(avg_rating)))
        st.write(f'平均評価: {avg_rating:.1f} / 5 ({stars})')
    else:
        st.write('まだレビューがありません。')

def search_books():
    st.header('本の検索')

    query = st.text_input('本のタイトルで検索')
    if query:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query('''
            SELECT books.id, books.title, books.author, books.isbn, books.available
            FROM books
            WHERE title LIKE ?
        ''', conn, params=(f'%{query}%',))
        conn.close()
        st.dataframe(df)
        if not df.empty:
            selected_book = st.selectbox('詳細を表示する本を選択', [''] + df['title'].tolist())
            if selected_book:
                book_row = df[df['title'] == selected_book]
                if not book_row.empty:
                    book_id = book_row['id'].iloc[0]
                    display_reviews(book_id)
                    add_review(book_id)
                else:
                    st.error('選択された本が見つかりません。')
    else:
        st.write('検索キーワードを入力してください。')

def display_history():
    st.subheader('本の追加・削除履歴')
    conn = sqlite3.connect(DB_PATH)
    df_history = pd.read_sql_query('SELECT * FROM book_history ORDER BY action_date DESC', conn)
    conn.close()
    if not df_history.empty:
        st.dataframe(df_history)
    else:
        st.write('履歴がありません。')

def add_review(book_id):
    # 不具合修正: add_review 関数 - user_name 正規化
    # 改善2: レビュー追加フォームの折りたたみ - st.expander で囲む
    with st.expander('レビューを書く'):
        with st.form('add_review'):
            rating = st.slider('評価 (1-5)', 1, 5, 3)
            review_text = st.text_area('レビュー')
            submitted = st.form_submit_button('レビューを追加')
            if submitted:
                user_name = st.session_state['current_user_name']
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('INSERT INTO reviews (book_id, user_name, rating, review_text) VALUES (?, ?, ?, ?)', (book_id, user_name, rating, review_text))
                conn.commit()
                conn.close()
                st.success('レビューを追加しました')



def display_ranking():
    st.header('本のランキング (評価順)')
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT books.id, books.title, books.author,
               COALESCE(ROUND(AVG(reviews.rating), 1), 0.0) AS avg_rating
        FROM books
        LEFT JOIN reviews ON books.id = reviews.book_id
        GROUP BY books.id, books.title, books.author
        ORDER BY AVG(reviews.rating) DESC, books.title
    ''', conn)
    conn.close()
    st.dataframe(df)



if __name__ == '__main__':
    main()
