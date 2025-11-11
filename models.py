from backend_application import db
from sqlalchemy.orm import validates

from datetime import datetime

class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email_address = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=True)
    password  = db.Column(db.String(20),nullable = False,unique = True)
    
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
    
    customer_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    full_name = db.Column(db.String(length=30), nullable=False)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    phone_number = db.Column(db.String(length=10), nullable=False, unique=True)
    review = db.Column(db.Text, nullable=False, )
    rating = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime,nullable=False)
    
    @validates('rating')
    def validate_rating(self, key, value):
        if value < 0 or value > 5:
            raise ValueError("Rating must be between 0 and 5")
        return value
    
    def to_dict(self):
        return {"customer_id":self.customer_id,
            "full_name":self.full_name,
            "email_address":self.email_address,
            "phone_number":self.phone_number,
            "review":self.review,
            "rating":self.rating,
            "created_at":self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
            }
    def json(self):
        """Alias for to_dict to support both naming conventions"""
        return self.to_dict()
        
    def __repr__(self):
        return f'<Customer {self.full_name}>'
    
def init_database():
    """Initialize database and create tables"""
    try:
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Check if tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Available tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        print(f"✗ Database initialization error: {str(e)}")
        return False
