from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tabelname__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)    
 

class ImageData(db.Model):
    __tablename__ = 'imagedata'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(1000), nullable=False)
    image_url = db.Column(db.String(1000), nullable=False)
    prompt = db.Column(db.String(5000), nullable=True)
    timestamp = db.Column(db.String, nullable=False)