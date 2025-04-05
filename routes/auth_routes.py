from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Teacher, Student
from forms import LoginForm, RegistrationForm, TeacherProfileForm, StudentProfileForm
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user)
            logger.debug(f"User {user.username} logged in successfully")
            
            # Redirect to the appropriate dashboard based on role
            next_page = request.args.get('next')
            if user.role == 'teacher':
                return redirect(next_page or url_for('teacher.dashboard'))
            else:
                return redirect(next_page or url_for('student.dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
            logger.debug("Login failed: Invalid credentials")
    
    return render_template('auth/login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.flush()  # To get the user ID
            
            # Create role-specific profile
            if user.role == 'teacher':
                profile = Teacher(user_id=user.id)
                db.session.add(profile)
            else:
                profile = Student(user_id=user.id)
                db.session.add(profile)
            
            db.session.commit()
            
            flash('Registration successful! Please complete your profile.', 'success')
            logger.debug(f"User {user.username} registered successfully as {user.role}")
            
            # Log the user in
            login_user(user)
            
            # Redirect to profile completion
            if user.role == 'teacher':
                return redirect(url_for('auth.complete_teacher_profile'))
            else:
                return redirect(url_for('auth.complete_student_profile'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            logger.error(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth.route('/profile/teacher', methods=['GET', 'POST'])
@login_required
def complete_teacher_profile():
    if current_user.role != 'teacher':
        flash('Access denied: You are not registered as a teacher.', 'danger')
        return redirect(url_for('index'))
    
    form = TeacherProfileForm()
    
    # Get teacher profile
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    
    if form.validate_on_submit():
        try:
            teacher.department = form.department.data
            db.session.commit()
            
            flash('Teacher profile updated successfully!', 'success')
            return redirect(url_for('teacher.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Profile update failed: {str(e)}', 'danger')
            logger.error(f"Teacher profile update error: {str(e)}")
    
    # Pre-fill form if profile exists
    if teacher and teacher.department:
        form.department.data = teacher.department
    
    return render_template('auth/teacher_profile.html', form=form)

@auth.route('/profile/student', methods=['GET', 'POST'])
@login_required
def complete_student_profile():
    if current_user.role != 'student':
        flash('Access denied: You are not registered as a student.', 'danger')
        return redirect(url_for('index'))
    
    form = StudentProfileForm()
    
    # Get student profile
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if form.validate_on_submit():
        try:
            student.grade = form.grade.data
            student.roll_number = form.roll_number.data
            db.session.commit()
            
            flash('Student profile updated successfully!', 'success')
            return redirect(url_for('student.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Profile update failed: {str(e)}', 'danger')
            logger.error(f"Student profile update error: {str(e)}")
    
    # Pre-fill form if profile exists
    if student:
        if student.grade:
            form.grade.data = student.grade
        if student.roll_number:
            form.roll_number.data = student.roll_number
    
    return render_template('auth/student_profile.html', form=form)
