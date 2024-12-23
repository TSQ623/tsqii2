from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 配置数据库 URI
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 数据库模型
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    scores = db.relationship('Score', backref='player', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'username': self.username}

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {'id': self.id, 'score': self.score, 'timestamp': self.timestamp}

# 创建数据库表
with app.app_context():
    db.create_all()

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 注册玩家
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'message': 'Username is required'}), 400
    if Player.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400
    new_player = Player(username=username)
    db.session.add(new_player)
    db.session.commit()
    return jsonify({'message': 'Player registered successfully', 'player_id': new_player.id}), 201

# 获取玩家信息
@app.route('/api/players', methods=['GET'])
def get_player_by_username():
    username = request.args.get('username')
    if not username:
        return jsonify({'message': 'Username is required'}), 400
    player = Player.query.filter_by(username=username).first()
    if not player:
        return jsonify({'message': 'Player not found'}), 404
    return jsonify(player.to_dict()), 200

# 提交游戏分数
@app.route('/api/scores', methods=['POST'])
def add_score():
    data = request.get_json()
    player_id = data.get('player_id')
    score_value = data.get('score')
    if not player_id or not score_value:
        return jsonify({'message': 'Player ID and score are required'}), 400
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'message': 'Player not found'}), 404
    new_score = Score(score=score_value, player_id=player_id)
    db.session.add(new_score)
    db.session.commit()
    return jsonify({'message': 'Score added successfully'}), 201

# 获取玩家分数历史
@app.route('/api/players/<int:player_id>/scores', methods=['GET'])
def get_scores(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'message': 'Player not found'}), 404
    scores = [score.to_dict() for score in player.scores]
    # 按分数从高到低排序
    scores.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(scores), 200

if __name__ == '__main__':
    app.run(debug=True)