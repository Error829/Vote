from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from utils import convert_pdf_to_images
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 修改数据文件路径为绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'notes.json')
VOTES_FILE = os.path.join(BASE_DIR, 'data', 'votes.json')

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
        # 加载笔记数据
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                notes = json.load(f)
        else:
            notes = []
            # 创建空的笔记文件
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
        
        # 加载投票数据
        if os.path.exists(VOTES_FILE):
            with open(VOTES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                votes = data.get('votes', {})
                ip_votes = data.get('ip_votes', {})
        else:
            votes = {}
            ip_votes = {}
            # 创建空的投票文件
            with open(VOTES_FILE, 'w', encoding='utf-8') as f:
                json.dump({'votes': votes, 'ip_votes': ip_votes}, f, ensure_ascii=False, indent=2)
            
        print(f"Loaded {len(notes)} notes")  # 调试日志
        print(f"Loaded votes: {votes}")      # 调试日志
            
    except Exception as e:
        print(f"加载数据出错: {e}")
        notes = []
        votes = {}
        ip_votes = {}

# 保存数据
def save_data():
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        
        # 保存笔记数据
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        
        # 保存投票数据
        with open(VOTES_FILE, 'w', encoding='utf-8') as f:
            vote_data = {
                'votes': votes,
                'ip_votes': ip_votes
            }
            json.dump(vote_data, f, ensure_ascii=False, indent=2)
            
        print(f"Saved {len(notes)} notes")  # 调试日志
        print(f"Saved votes: {votes}")      # 调试日志
            
    except Exception as e:
        print(f"保存数据出错: {e}")
        raise  # 抛出异常以便调试

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
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            pdf_file = request.files.get('pdf')
            
            if not all([title, description, pdf_file]):
                flash('请填写所有必要信息并上传PDF文件')
                return redirect(url_for('admin_dashboard'))
            
            filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', filename)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            
            # 保存PDF文件
            pdf_file.save(pdf_path)
            print(f"PDF saved to: {pdf_path}")  # 调试日志
            
            try:
                # 转换PDF为图片
                images = convert_pdf_to_images(pdf_path)
                print(f"Converted images: {images}")  # 调试日志
                
                # 生成唯一ID
                note_id = str(len(notes))
                while any(note['id'] == note_id for note in notes):
                    note_id = str(int(note_id) + 1)
                
                # 创建新笔记
                note = {
                    'id': note_id,
                    'title': title,
                    'description': description,
                    'images': images,
                    'pdf_file': filename,
                    'created_at': datetime.now().isoformat()
                }
                
                # 添加到笔记列表
                notes.append(note)
                votes[note_id] = 0  # 初始化票数
                
                # 保存数据
                save_data()
                print(f"New note added: {note}")  # 调试日志
                
                flash('笔记添加成功！')
                
            except Exception as e:
                print(f"PDF处理错误: {e}")  # 调试日志
                flash(f'PDF处理失败: {str(e)}')
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                raise  # 抛出异常以便调试
                
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            print(f"上传错误: {e}")  # 调试日志
            flash(f'上传失败: {str(e)}')
            raise  # 抛出异常以便调试
            
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