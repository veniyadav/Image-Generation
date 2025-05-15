from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)    
    tokens = db.Column(db.Integer, default=200)# default tokens added
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))  # user subscribed plan
    plan = db.relationship('Plans')
 

class ImageData(db.Model):
    __tablename__ = 'imagedata'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(1000), nullable=False)
    image_name = db.Column(db.String(1000), nullable=True)
    prompt = db.Column(db.String(5000), nullable=True)
    timestamp = db.Column(db.String(100), nullable=False)

class Chat_messages(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(64), nullable=False)
    receiver_id = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_sender = db.Column(db.Boolean, nullable=False) 

class Plans(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(50), nullable=False)
    plan_price = db.Column(db.Float, nullable=False)
    plan_duration = db.Column(db.String(50), nullable=False)  # e.g., "1 month", "1 year"
    plan_tokens = db.Column(db.Integer, nullable=False)  # Number of tokens included in the plan