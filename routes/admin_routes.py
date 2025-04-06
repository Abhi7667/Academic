from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Teacher, Student
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied: Admin permissions required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@admin.route('/dashboard')
@admin_required
def admin_dashboard():
    # Get counts for dashboard
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_users = User.query.count()
    
    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_users=total_users
    )

@admin.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/user/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('admin.add_user'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('admin.add_user'))
        
        try:
            # Create user
            user = User(
                username=username,
                email=email,
                role=role
            )
            user.set_password(password)
            
            # Add and commit the user first to get the ID
            db.session.add(user)
            db.session.commit()
            
            # Now create role-specific profile with the user ID
            if role == 'teacher':
                profile = Teacher(user_id=user.id)
                db.session.add(profile)
            elif role == 'student':
                profile = Student(user_id=user.id)
                db.session.add(profile)
            
            # Commit the profile
            db.session.commit()
            flash('User added successfully', 'success')
            return redirect(url_for('admin.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {str(e)}', 'danger')
            logger.error(f"User creation error: {str(e)}")
    
    return render_template('admin/add_user.html')

@admin.route('/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        is_active = 'is_active' in request.form
        
        # Check if username or email already exists for other users
        username_exists = User.query.filter(
            User.username == username,
            User.id != user_id
        ).first()
        email_exists = User.query.filter(
            User.email == email,
            User.id != user_id
        ).first()
        
        if username_exists:
            flash('Username already exists', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        if email_exists:
            flash('Email already registered', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        try:
            user.username = username
            user.email = email
            user.role = role
            user.is_active = is_active
            
            if 'password' in request.form and request.form['password']:
                user.set_password(request.form['password'])
            
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
            logger.error(f"User update error: {str(e)}")
    
    return render_template('admin/edit_user.html', user=user)

@admin.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_admin and User.query.filter_by(role='admin').count() <= 1:
        flash('Cannot delete the last admin user', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
        logger.error(f"User deletion error: {str(e)}")
    
    return redirect(url_for('admin.manage_users'))