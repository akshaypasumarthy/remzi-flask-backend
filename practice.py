import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError, PyMongoError
from flask_cors import CORS
from flask_restful import Api, Resource
import bcrypt

app = Flask(__name__)

# MongoDB URI - set via environment variable MONGODB_URI
# Example (Atlas): "mongodb+srv://<user>:<pass>@cluster0.xxxxxx.mongodb.net/mydatabase?retryWrites=true&w=majority"
app.config["MONGO_URI"] = os.environ.get(
    "MONGODB_URI",
    # fallback to local MongoDB
    "mongodb://localhost:27017/mydatabase"
)

# Configure CORS properly for Angular frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4200", "http://127.0.0.1:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

mongo = PyMongo(app)
api = Api(app)

# Collections
admins_coll = mongo.db.admins
reviews_coll = mongo.db.customer_reviews

# Ensure indexes (unique constraints)
def ensure_indexes():
    try:
        admins_coll.create_index("email_address", unique=True)
    except Exception as e:
        print(f"Warning creating index on admins.email_address: {e}")
    try:
        reviews_coll.create_index("email_address", unique=True)
    except Exception as e:
        print(f"Warning creating index on customer_reviews.email_address: {e}")
    try:
        reviews_coll.create_index("phone_number", unique=True)
    except Exception as e:
        print(f"Warning creating index on customer_reviews.phone_number: {e}")

# Helpers
def hash_password(plain_password: str) -> bytes:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())

def check_password(plain_password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed)

def review_to_dict(doc):
    return {
        "id": str(doc.get("_id")),
        "full_name": doc.get("full_name"),
        "email_address": doc.get("email_address"),
        "phone_number": doc.get("phone_number"),
        "review": doc.get("review"),
        "rating": doc.get("rating"),
        "created_at": doc.get("created_at").strftime('%Y-%m-%d %H:%M:%S') if doc.get("created_at") else None
    }

def admin_to_dict(doc):
    return {
        "id": str(doc.get("_id")),
        "full_name": doc.get("full_name"),
        "email_address": doc.get("email_address"),
        "phone_number": doc.get("phone_number"),
        # do NOT send password hash in responses in production, but included here only if truly needed.
    }

# Routes (mirrors your endpoints)

@app.route('/api/admin_login', methods=['POST'])
def login_admin():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        email = data.get('email_address')
        password = data.get('password')
        if not email or not password:
            return jsonify({'success': False, 'error': 'email_address and password are required'}), 400

        existing_admin = admins_coll.find_one({"email_address": email.strip().lower()})
        if not existing_admin:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

        stored_hash = existing_admin.get("password")
        if stored_hash and check_password(password, stored_hash):
            return jsonify({'success': True, 'message': 'login Successful'}), 200
        else:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    except PyMongoError as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/admin', methods=['POST'])
def create_admin():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        full_name = (data.get('full_name') or "").strip()
        email = (data.get('email_address') or "").strip().lower()
        phone = data.get('phone_number')
        password = data.get('password')

        if not full_name or not email or not password:
            return jsonify({'success': False, 'error': 'full_name, email_address and password are required'}), 400

        hashed = hash_password(password)

        new_admin = {
            "full_name": full_name,
            "email_address": email,
            "phone_number": phone,
            "password": hashed  # store bytes; PyMongo will store as Binary
        }

        try:
            result = admins_coll.insert_one(new_admin)
        except DuplicateKeyError:
            return jsonify({'success': False, 'error': 'Email already exists'}), 400

        created = admins_coll.find_one({"_id": result.inserted_id})
        return jsonify({'success': True, 'message': 'Admin created successfully', 'user': admin_to_dict(created)}), 201

    except PyMongoError as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/all_reviews', methods=['GET'])
def get_all_reviews():
    try:
        docs = reviews_coll.find().sort("created_at", -1)
        reviews = [review_to_dict(d) for d in docs]
        return jsonify({'success': True, 'users': reviews, 'count': len(reviews)}), 200
    except PyMongoError as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500


@app.route('/api/positive_reviews', methods=['GET'])
def get_all_positive_reviews():
    try:
        docs = reviews_coll.find({"rating": {"$gte": 3}}).sort("created_at", -1)
        reviews = [review_to_dict(d) for d in docs]
        return jsonify({'success': True, 'users': reviews, 'count': len(reviews)}), 200
    except PyMongoError as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500


@app.route('/api/create_review', methods=['POST'])
def create_review():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        full_name = (data.get('full_name') or "").strip()
        email = (data.get('email_address') or "").strip().lower()
        phone = data.get('phone_number')
        review_text = data.get('review')
        rating = data.get('rating')

        if not full_name or not email:
            return jsonify({'success': False, 'error': 'Full name and email address are required'}), 400

        try:
            rating = float(rating)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'Rating must be a number between 0 and 5'}), 400

        if rating < 0 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 0 and 5'}), 400

        new_review = {
            "full_name": full_name,
            "email_address": email,
            "phone_number": phone,
            "review": review_text,
            "rating": rating,
            "created_at": datetime.utcnow()
        }

        try:
            result = reviews_coll.insert_one(new_review)
        except DuplicateKeyError as dk:
            # either email or phone duplicate
            return jsonify({'success': False, 'error': 'Email or phone number already exists'}), 400

        created = reviews_coll.find_one({"_id": result.inserted_id})
        return jsonify({'success': True, 'message': 'Review created successfully', 'review': review_to_dict(created)}), 201

    except PyMongoError as e:
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500


# Flask-RESTful Resource for /api/reviews
class ReviewResource(Resource):
    def get(self):
        try:
            docs = reviews_coll.find().sort("created_at", -1)
            return {'customers': [review_to_dict(d) for d in docs]}, 200
        except PyMongoError as e:
            return {'error': f'Error fetching reviews: {str(e)}'}, 500

    def post(self):
        data = request.get_json()
        if not data:
            return {"error": "Invalid JSON body"}, 400
        # Reuse create_review logic-ish (lighter validation)
        try:
            full_name = data["full_name"]
            email = data["email_address"].strip().lower()
            phone = data.get("phone_number")
            review_text = data.get("review")
            rating = float(data.get("rating"))
            if rating < 0 or rating > 5:
                return {"error": "Rating must be between 0 and 5"}, 400

            new_review = {
                "full_name": full_name,
                "email_address": email,
                "phone_number": phone,
                "review": review_text,
                "rating": rating,
                "created_at": datetime.utcnow()
            }
            try:
                result = reviews_coll.insert_one(new_review)
            except DuplicateKeyError:
                return {"error": "Email or phone number already exists"}, 400

            created = reviews_coll.find_one({"_id": result.inserted_id})
            return created and review_to_dict(created) or {"error": "Could not fetch created review"}, 201

        except KeyError as e:
            return {"error": f"Missing required field: {e}"}, 400
        except ValueError as e:
            return {"error": str(e)}, 400
        except PyMongoError as e:
            return {"error": "Database error while adding review."}, 500
        except Exception:
            return {"error": "An internal server error occurred."}, 500


@app.route('/customers_review', methods=['GET', 'POST', 'OPTIONS'])
def customers_review():
    """Alternative endpoint for customer reviews"""
    if request.method == 'OPTIONS':
        # CORS preflight handled by Flask-Cors, but keep headers for Angular preflight assurance
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:4200')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response, 200

    if request.method == 'GET':
        try:
            docs = reviews_coll.find().sort("created_at", -1)
            return jsonify({'success': True, 'customers': [review_to_dict(d) for d in docs]}), 200
        except PyMongoError as e:
            return jsonify({'success': False, 'error': f'Error fetching reviews: {str(e)}'}), 500

    elif request.method == 'POST':
        return create_review()


# Register resource
api.add_resource(ReviewResource, '/api/reviews')

if __name__ == "__main__":
    # Ensure indexes once on startup
    ensure_indexes()

    # Optionally create a couple of sample documents if needed (commented out in production)
    # if admins_coll.count_documents({}) == 0:
    #     admins_coll.insert_one({
    #         "full_name": "Super Admin",
    #         "email_address": "admin@example.com",
    #         "phone_number": "0000000000",
    #         "password": hash_password("changeme")
    #     })

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
