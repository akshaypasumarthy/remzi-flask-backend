from sqlalchemy import or_
from flask_restful import Resource,reqparse
from sqlalchemy.exc import SQLAlchemyError
from backend_application.models import Customer_review,Admin
from backend_application import api,db,app

from flask import request,session,jsonify
from datetime import datetime 
from flask_cors import CORS,cross_origin


@app.route('/api/create_review', methods=['POST'])
def create_review():
    try:
        data = request.get_json()
        
        # Validation
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
            
        if not data.get('full_name') or not data.get('email_address'):
            return jsonify({
                'success': False,
                'error': 'Name and email are required'
            }), 400
        
        existing_user = Customer_review.query.filter_by(email_address=data['email_address']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Email already exists'
            }), 400
        
        new_review = Customer_review(
            full_name=data['full_name'].strip(),
            email_address=data['email_address'].strip(),
            phone_number = data['phone_number'],
            review = data['review'],
            rating = data['rating']
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        print(f"✓ User created: {new_review.full_name} ({new_review.email_address})")
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': new_review.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating user: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500
   
@app.route('/api/admin/<int:admin_id>', methods=['GET'])     
def get_admin(admin_id):
    try:
        admin = Admin.query.get(admin_id)
        if not admin_id:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        return jsonify({
            'success': True,
            'user': admin.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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

