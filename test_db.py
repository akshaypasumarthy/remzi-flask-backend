
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_cors import CORS
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Configure CORS properly for Angular frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4200", "http://127.0.0.1:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# DB_CONFIG = {
#     'host': 'sql7.freesqldatabase.com',
#     'port': 3306,
#     'user': 'sql7807469',
#     'password': '57pFPQ4aNM',
#     'database': 'sql7807469'
# }


# app.config['SQLALCHEMY_DATABASE_URI'] = (
#     f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
#     f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
# )
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ECHO'] = True

USER=postgres.boqfwfmwdrfnozlgpfpi 
PASSWORD=root
HOST=aws-1-eu-west-1.pooler.supabase.com 
PORT=5432 
DBNAME=postgres
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")
# Apply to Flask-SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Optional: show SQL statements in logs if helpful
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(app)
api = Api(app)

# models.py
from datetime import datetime
from sqlalchemy.orm import validates

class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email_address = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=True)
    password  = db.Column(db.String(20),nullable = False)
    
    def to_dict(self):
        return {"id":self.id,
            "full_name":self.full_name,
            "email_address":self.email_address,
            "phone_number":self.phone_number,
            "password":self.password,
            }
    def json(self):
        """Alias for to_dict to support both naming conventions"""
        return self.to_dict()
        
    def __repr__(self):
        return f'<Admin {self.full_name}>'

class Customer_review(db.Model):
    __tablename__ = "Customer"
    
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(length=30), nullable=False)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    phone_number = db.Column(db.String(length=10), nullable=False, unique=True)
    review = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    @validates('rating')
    def validate_rating(self, key, value):
        if value < 0 or value > 5:
            raise ValueError("Rating must be between 0 and 5")
        return value
    
    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "full_name": self.full_name,
            "email_address": self.email_address,
            "phone_number": self.phone_number,
            "review": self.review,
            "rating": self.rating,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    def json(self):
        """Alias for to_dict to support both naming conventions"""
        return self.to_dict()
        
    def __repr__(self):
        return f'<Customer {self.full_name}>'

# routes.py
from flask import request, jsonify
from flask_restful import Resource
from flask_cors import cross_origin
from sqlalchemy.exc import SQLAlchemyError


@app.route('/api/admin_login', methods = ['POST'])
def login_admin():
    try:
        data = request.get_json()
        print(data)
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
                    
        if not data.get('email_address') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': ' email_address and password are required'
            }), 400
        existing_admin = Admin.query.filter_by(email_address=data['email_address']).first()
        if existing_admin.password == data['password']:
            return jsonify({
                'success': True,
                'message': 'login Sucessful'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error finding Admin: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500
        
@app.route('/api/admin', methods=['POST'])
def create_admin():
    try:
        data = request.get_json()
        print(data)
        
        # Validation
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        if not data.get('full_name') or not data.get('email_address'):
            return jsonify({
                'success': False,
                'error': 'Full_Name and email_address are required'
            }), 400
        
        # Check if email already exists
        existing_admin = Admin.query.filter_by(email_address=data['email_address']).first()
        if existing_admin:
            return jsonify({
                'success': False,
                'error': 'Email already exists'
            }), 400
        
        # Create new user
        new_admin = Admin(
            full_name=data['full_name'].strip(),
            email_address=data['email_address'].strip().lower(),
            phone_number=data['phone_number'],
            password = data["password"].strip()
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        print(f"✓ User created: {new_admin.full_name} ({new_admin.email_address})")
        
        return jsonify({
            'success': True,
            'message': 'Admin created successfully',
            'user': new_admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating Admin: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500
 
 
@app.route('/api/all_reviews', methods=['GET'])
def get_all_reviews():
    try:
        reviews = Customer_review.query.order_by(Customer_review.created_at.desc()).all()
        return jsonify({
            'success': True,
            'users': [review.to_dict() for review in reviews],
            'count': len(reviews)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500

@app.route('/api/positive_reviews', methods=['GET'])
def get_all_postive_reviews():
    try:
        reviews = (Customer_review.query.filter(Customer_review.rating>=3).order_by(Customer_review.created_at.desc()).all())
        print(reviews)
        return jsonify({
            'success': True,
            'users': [review.to_dict() for review in reviews],
            'count': len(reviews)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500


@app.route('/api/create_review', methods=['POST'])
def create_review():
    """Create new customer review"""
    try:
        data = request.get_json()
        
        # Validation
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        # Check for required fields with correct names
        if not data.get('full_name') or not data.get('email_address'):
            return jsonify({
                'success': False,
                'error': 'Full name and email address are required'
            }), 400
        
        # Check if email already exists (using correct field name)
        existing_user = Customer_review.query.filter_by(email_address=data['email_address']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Email already exists'
            }), 400
        
        # Check if phone number already exists
        existing_phone = Customer_review.query.filter_by(phone_number=data['phone_number']).first()
        if existing_phone:
            return jsonify({
                'success': False,
                'error': 'Phone number already exists'
            }), 400
        
        # Create new review
        new_review = Customer_review(
            full_name=data['full_name'].strip(),
            email_address=data['email_address'].strip(),
            phone_number=data['phone_number'],
            review=data['review'],
            rating=float(data['rating'])
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        print(f"✓ Review created: {new_review.full_name} ({new_review.email_address})")
        
        return jsonify({
            'success': True,
            'message': 'Review created successfully',
            'review': new_review.to_dict()
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        print(f"✗ Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating review: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500


class Review(Resource):
    
    def get(self):
        try:
            customers = Customer_review.query.all()
            return {'customers': [x.json() for x in customers]}, 200
        except Exception as e:
            return {'error': f'Error fetching reviews: {str(e)}'}, 500
    
    def post(self):
        data = request.get_json()
        
        if not data:
            return {"error": "Invalid JSON body"}, 400 
        
        try:
            new_customer = Customer_review(
                full_name=data["full_name"],
                email_address=data["email_address"],
                phone_number=data["phone_number"],
                review=data["review"],
                rating=float(data["rating"])
            )
            
            db.session.add(new_customer)
            db.session.commit()
            
            print("✓ Successfully committed new customer review to DB.")
            return new_customer.json(), 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"✗ Database error during POST: {e}")
            return {"error": "Database error while adding review."}, 500
        except KeyError as e:
            return {"error": f"Missing required field: {e}"}, 400
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            print(f"✗ An unexpected error occurred: {e}")
            return {"error": "An internal server error occurred."}, 500


@app.route('/customers_review', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
def customers_review():
    """Alternative endpoint for customer reviews"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:4200')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response, 200
    
    if request.method == 'GET':
        try:
            customers = Customer_review.query.all()
            return jsonify({
                'success': True,
                'customers': [x.to_dict() for x in customers]
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error fetching reviews: {str(e)}'
            }), 500
    
    elif request.method == 'POST':
        return create_review()


# Register the Resource endpoint
api.add_resource(Review, '/api/reviews')


# run.py or at the bottom of your main file
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✓ Database tables created")
    port = int(os.environ.get('PORT',5000))
    app.run(host = '0.0.0.0',port = port,debug=False)
    
