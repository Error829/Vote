from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from utils import convert_pdf_to_images
from datetime import datetime
import uuid
import imghdr

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 修改数据文件路径为绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'notes.json')
VOTES_FILE = os.path.join(BASE_DIR, 'data', 'votes.json')
RANKING_FILE = os.path.join(BASE_DIR, 'data', 'ranking.json')  # 新增排行榜文件

# 确保数据目录存在
os.makedirs('data', exist_ok=True)

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

def update_ranking():
    """更新排行榜数据"""
    try:
        # 计算排行榜（所有项目）
        sorted_notes = sorted(
            [{'id': note['id'], 
              'title': note['title'], 
              'votes': votes.get(note['id'], 0)} 
             for note in notes],
            key=lambda x: x['votes'],
            reverse=True
        )
        
        # 添加排名信息
        for i, note in enumerate(sorted_notes, 1):
            note['rank'] = i
        
        # 保存完整排行榜数据
        with open(RANKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_notes, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"更新排行榜失败: {e}")

@app.route('/')
def index():
    sorted_notes = sorted(notes, key=lambda x: votes.get(x['id'], 0), reverse=True)
    return render_template('index.html', notes=sorted_notes, votes=votes)

def get_client_ip():
    """获取真实的客户端 IP 地址"""
    # 先尝试获取 X-Forwarded-For 头信息
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
    # 然后尝试获取 X-Real-IP 头信息
    elif request.headers.get("X-Real-IP"):
        ip = request.headers.get("X-Real-IP")
    # 最后使用远程地址
    else:
        ip = request.remote_addr
    return ip

@app.route('/vote/<note_id>')
def vote(note_id):
    # 使用新的函数获取 IP
    ip = get_client_ip()
    
    # 检查 IP 是否达到投票限制
    if ip not in ip_votes:
        ip_votes[ip] = 0
    
    if ip_votes[ip] >= MAX_VOTES_PER_IP:
        return jsonify({
            'error': '您已达到最大投票次数限制',
            'votes': votes.get(note_id, 0),
            'remaining_votes': 0
        }), 403
    
    try:
        # 更新投票
        if note_id not in votes:
            votes[note_id] = 0
        votes[note_id] += 1
        ip_votes[ip] += 1
        
        # 保存数据
        save_data()
        
        # 更新排行榜
        update_ranking()
        
        # 返回更新后的信息
        return jsonify({
            'votes': votes[note_id],
            'remaining_votes': MAX_VOTES_PER_IP - ip_votes[ip]
        })
        
    except Exception as e:
        print(f"投票更新失败: {str(e)}")
        return jsonify({
            'error': '投票失败，请稍后重试',
            'votes': votes.get(note_id, 0)
        }), 500

# 添加允许的图片类型
ALLOWED_IMAGE_TYPES = {'png', 'jpeg', 'jpg', 'gif'}

def allowed_image(filename):
    """检查文件是否为允许的图片类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_TYPES

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            pdf_file = request.files.get('pdf')
            image_files = request.files.getlist('images')  # 获取多个图片文件
            
            if not all([title, description]):
                flash('请填写标题和描述')
                return redirect(url_for('index'))
            
            # 检查是否至少上传了一个文件（PDF或图片）
            has_pdf = pdf_file and pdf_file.filename != ''
            has_images = any(img and img.filename != '' for img in image_files)
            
            if not (has_pdf or has_images):
                flash('请至少上传一个PDF文件或图片文件')
                return redirect(url_for('index'))
            
            # 处理图片上传
            image_paths = []
            if has_images:
                for image in image_files:
                    if image and image.filename != '' and allowed_image(image.filename):
                        filename = secure_filename(image.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        image_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images', timestamp)
                        os.makedirs(image_dir, exist_ok=True)
                        
                        image_path = os.path.join(image_dir, filename)
                        image.save(image_path)
                        relative_path = os.path.join('uploads', 'images', timestamp, filename)
                        image_paths.append(relative_path)
            
            # PDF文件处理（如果有）
            pdf_filename = None
            if has_pdf:
                filename = secure_filename(pdf_file.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs', filename)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                pdf_file.save(pdf_path)
                pdf_filename = filename
                
                # 如果有PDF，转换为图片
                pdf_images = convert_pdf_to_images(pdf_path)
                image_paths.extend(pdf_images)
            
            # 生成唯一ID
            note_id = generate_unique_id()
            
            # 创建新笔记
            note = {
                'id': note_id,
                'title': title,
                'description': description,
                'images': image_paths,
                'pdf_file': pdf_filename,
                'created_at': datetime.now().isoformat()
            }
            
            notes.append(note)
            votes[note_id] = 0
            save_data()
            
            flash('笔记添加成功！')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"上传错误: {e}")
            flash(f'上传失败: {str(e)}')
            return redirect(url_for('index'))
            
    return render_template('admin/dashboard.html', notes=notes, votes=votes)

@app.route('/ranking')
def ranking():
    try:
        if os.path.exists(RANKING_FILE):
            with open(RANKING_FILE, 'r', encoding='utf-8') as f:
                ranking_data = json.load(f)
        else:
            ranking_data = []
            update_ranking()  # 如果文件不存在，创建排行榜数据
        
        return render_template('ranking.html', rankings=ranking_data)
    except Exception as e:
        print(f"获取排行榜失败: {e}")
        return render_template('ranking.html', rankings=[])

def generate_unique_id():
    """生成一个完整的 UUID"""
    return str(uuid.uuid4())

@app.route('/submit', methods=['POST'])
def submit():
    # 使用新的 generate_unique_id() 函数替换原来的时间戳生成方式
    unique_id = generate_unique_id()
    # ...

if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # 初始化数据
    load_data()
    
    # 初始化排行榜
    update_ranking()
    
    app.run(debug=True) 