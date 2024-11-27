from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from utils import convert_pdf_to_images

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# 模拟数据存储
notes = []
votes = {}

@app.route('/')
def index():
    sorted_notes = sorted(notes, key=lambda x: votes.get(x['id'], 0), reverse=True)
    return render_template('index.html', notes=sorted_notes, votes=votes)

@app.route('/vote/<note_id>')
def vote(note_id):
    if note_id not in votes:
        votes[note_id] = 0
    votes[note_id] += 1
    return {'votes': votes[note_id]}

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            login_user(User(1))
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials')
    return render_template('admin/login.html', votes=votes)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        pdf_file = request.files['pdf']
        
        if pdf_file:
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', filename)
            pdf_file.save(pdf_path)
            
            # 转换PDF为图片
            images = convert_pdf_to_images(pdf_path)
            note_id = str(len(notes))
            note = {
                'id': note_id,
                'title': title,
                'description': description,
                'images': images
            }
            notes.append(note)
            votes[note_id] = 0
            flash('笔记添加成功！')
            
    return render_template('admin/dashboard.html', notes=notes, votes=votes)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

if __name__ == '__main__':
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
    app.run(debug=True) 