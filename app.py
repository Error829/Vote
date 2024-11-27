from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from utils import convert_pdf_to_images

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 数据文件路径
DATA_FILE = 'data/notes.json'
VOTES_FILE = 'data/votes.json'

# 确保数据目录存在
os.makedirs('data', exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# 添加 IP 投票记录
ip_votes = {}  # 格式: {'ip': vote_count}
MAX_VOTES_PER_IP = 10  # 每个IP最大投票数

# 加载数据
def load_data():
    global notes, votes, ip_votes
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                notes = json.load(f)
            
        if os.path.exists(VOTES_FILE):
            with open(VOTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                votes = data.get('votes', {})
                ip_votes = data.get('ip_votes', {})
        else:
            notes = []
            votes = {}
            ip_votes = {}
    except Exception as e:
        print(f"加载数据出错: {e}")
        notes = []
        votes = {}
        ip_votes = {}

# 保存数据
def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        with open(VOTES_FILE, 'w', encoding='utf-8') as f:
            data = {
                'votes': votes,
                'ip_votes': ip_votes
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存数据出错: {e}")

# 初始化数据
load_data()

@app.route('/')
def index():
    sorted_notes = sorted(notes, key=lambda x: votes.get(x['id'], 0), reverse=True)
    return render_template('index.html', notes=sorted_notes, votes=votes)

@app.route('/vote/<note_id>')
def vote(note_id):
    ip = request.remote_addr
    
    # 检查 IP 是否达到投票限制
    if ip not in ip_votes:
        ip_votes[ip] = 0
    
    if ip_votes[ip] >= MAX_VOTES_PER_IP:
        return jsonify({
            'error': '您已达到最大投票次数限制',
            'votes': votes.get(note_id, 0),
            'remaining_votes': 0
        }), 403
    
    # 更新投票
    if note_id not in votes:
        votes[note_id] = 0
    votes[note_id] += 1
    ip_votes[ip] += 1
    
    # 保存数据
    save_data()
    
    # 返回更新后的信息
    remaining_votes = MAX_VOTES_PER_IP - ip_votes[ip]
    return jsonify({
        'votes': votes[note_id],
        'remaining_votes': remaining_votes
    })

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
            
            # 检查文件是否已存在
            if not os.path.exists(pdf_path):
                pdf_file.save(pdf_path)
            
            # 转换PDF为图片
            images = convert_pdf_to_images(pdf_path)
            note_id = str(len(notes))
            note = {
                'id': note_id,
                'title': title,
                'description': description,
                'images': images,
                'pdf_file': filename  # 保存PDF文件名
            }
            notes.append(note)
            votes[note_id] = 0
            save_data()  # 保存笔记数据
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

@app.route('/get_ranking')
def get_ranking():
    # 按投票数排序笔记
    sorted_notes = sorted(
        [{'id': note['id'], 'title': note['title'], 'votes': votes.get(note['id'], 0)} 
         for note in notes],
        key=lambda x: x['votes'],
        reverse=True
    )
    # 只返回前10个
    return jsonify(sorted_notes[:10])

if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # 初始化数据
    load_data()
    
    app.run(debug=True) 