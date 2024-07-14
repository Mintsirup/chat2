from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from flask_socketio import SocketIO, send, emit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads'
socketio = SocketIO(app)

users = set()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('chat.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        if username in users:
            flash('이미 이 이름을 가진 사람이 있습니다!', 'error')
        else:
            session['username'] = username
            users.add(username)
            socketio.emit('message', {'msg': f'{username}님이 입장하셨습니다.', 'username': 'System'})
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        username = session.pop('username', None)
        if username in users:
            users.remove(username)
            socketio.emit('message', {'msg': f'{username}님이 퇴장하셨습니다.', 'username': 'System'})
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return 'Unauthorized', 401
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = os.path.join('uploads', filename)
        socketio.emit('image', {'url': file_url, 'username': session['username']})
        return 'File successfully uploaded', 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('message')
def handleMessage(msg):
    if 'username' in session:
        print(f'Message from {session["username"]}: {msg}')
        send({'msg': msg, 'username': session['username']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
