from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_cors import CORS
from flask_session import Session
import os

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',           # Your MySQL username
    'password': 'root',  # Your MySQL password
    'database': 'user_management'  # Your database name
}

# Configure MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Set to False in production

db = SQLAlchemy(app)
