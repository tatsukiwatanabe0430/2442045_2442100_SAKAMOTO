from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Book, Review, Comment

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# ------------------- ユーザー認証 -------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('ユーザー名が既に存在します')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('登録成功！ログインしてください')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('books_page'))
        flash('ユーザー名かパスワードが違います')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ------------------- 蔵書管理 -------------------
@app.route('/books')
def books_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    books = Book.query.filter_by(user_id=session['user_id']).all()
    return render_template('books.html', books=books)

@app.route('/books/add', methods=['GET','POST'])
def add_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            genre=request.form.get('genre'),
            status=request.form['status'],
            user_id=session['user_id']
        )
        db.session.add(book)
        db.session.commit()
        return redirect(url_for('books_page'))
    return render_template('add_book.html')

@app.route('/books/edit/<int:book_id>', methods=['GET','POST'])
def edit_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get_or_404(book_id)
    if request.method=='POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.genre = request.form.get('genre')
        book.status = request.form['status']
        book.rating = int(request.form['rating'])
        db.session.commit()
        return redirect(url_for('books_page'))
    return render_template('edit_book.html', book=book)

@app.route('/books/delete/<int:book_id>')
def delete_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('books_page'))

# ------------------- レビュー -------------------
@app.route('/reviews')
def reviews_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    reviews = Review.query.order_by(Review.review_date.desc()).all()
    return render_template('reviews.html', reviews=reviews)

@app.route('/reviews/add/<int:book_id>', methods=['GET','POST'])
def add_review(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get_or_404(book_id)
    if request.method=='POST':
        review = Review(
            book_id=book.id,
            user_id=session['user_id'],
            rating=int(request.form['rating']),
            review_text=request.form['review_text']
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('reviews_page'))
    return render_template('add_review.html', book=book)

@app.route('/reviews/delete/<int:review_id>')
def delete_review(review_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    review = Review.query.get_or_404(review_id)
    if review.user_id != session['user_id']:
        flash("他人のレビューは削除できません")
        return redirect(url_for('reviews_page'))
    for comment in review.comments:
        db.session.delete(comment)
    db.session.delete(review)
    db.session.commit()
    flash("レビューを削除しました")
    return redirect(url_for('reviews_page'))

# ------------------- コメント -------------------
@app.route('/comments/add/<int:review_id>', methods=['GET','POST'])
def add_comment(review_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    review = Review.query.get_or_404(review_id)
    if request.method=='POST':
        comment = Comment(
            review_id=review.id,
            user_id=session['user_id'],
            comment_text=request.form['comment_text']
        )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('reviews_page'))
    return render_template('add_comment.html', review=review)

@app.route('/comments/delete/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != session['user_id']:
        flash("他人のコメントは削除できません")
        return redirect(url_for('reviews_page'))
    db.session.delete(comment)
    db.session.commit()
    flash("コメントを削除しました")
    return redirect(url_for('reviews_page'))

# ------------------- 起動 -------------------
if __name__ == '__main__':
    app.run(debug=True)
