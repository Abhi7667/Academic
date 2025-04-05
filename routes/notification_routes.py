from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Notification, Teacher
from forms import NotificationForm
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
notification = Blueprint('notification', __name__, url_prefix='/notifications')

# Decorator to check if user is a teacher
def teacher_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Access denied: Teacher permissions required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@notification.route('/')
@login_required
def index():
    # Different view for teachers and students
    if current_user.role == 'teacher':
        return redirect(url_for('notification.teacher_notifications'))
    else:
        return redirect(url_for('notification.student_notifications'))

@notification.route('/teacher', methods=['GET', 'POST'])
@teacher_required
def teacher_notifications():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Form for creating notifications
    form = NotificationForm()
    
    if form.validate_on_submit():
        try:
            notification = Notification(
                title=form.title.data,
                message=form.message.data,
                teacher_id=teacher_profile.id,
                target_grade=form.target_grade.data if form.target_grade.data else None
            )
            db.session.add(notification)
            db.session.commit()
            
            flash('Notification sent successfully!', 'success')
            return redirect(url_for('notification.teacher_notifications'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to send notification: {str(e)}', 'danger')
            logger.error(f"Notification creation error: {str(e)}")
    
    # Get all notifications created by this teacher
    notifications = Notification.query.filter_by(teacher_id=teacher_profile.id).order_by(Notification.created_at.desc()).all()
    
    return render_template('teacher/notifications.html', form=form, notifications=notifications)

@notification.route('/student')
@login_required
def student_notifications():
    if current_user.role != 'student':
        flash('Access denied: Student permissions required.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get student profile
    student = db.session.query(db.Model.metadata.tables['students']).filter_by(user_id=current_user.id).first()
    
    if not student:
        flash('Student profile not found. Please complete your profile.', 'warning')
        return redirect(url_for('auth.complete_student_profile'))
    
    # Get notifications for this student's grade or all students
    notifications = db.session.query(
        Notification, Teacher, db.Model.metadata.tables['users']
    ).join(
        Teacher, Notification.teacher_id == Teacher.id
    ).join(
        db.Model.metadata.tables['users'], Teacher.user_id == db.Model.metadata.tables['users'].c.id
    ).filter(
        (Notification.target_grade == student.grade) | 
        (Notification.target_grade == None) |
        (Notification.target_grade == '')
    ).order_by(
        Notification.created_at.desc()
    ).all()
    
    return render_template('student/notifications.html', notifications=notifications)

@notification.route('/delete/<int:notification_id>', methods=['POST'])
@teacher_required
def delete_notification(notification_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get notification and verify ownership
    notification = Notification.query.filter_by(id=notification_id, teacher_id=teacher_profile.id).first_or_404()
    
    try:
        db.session.delete(notification)
        db.session.commit()
        flash('Notification deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete notification: {str(e)}', 'danger')
        logger.error(f"Notification deletion error: {str(e)}")
    
    return redirect(url_for('notification.teacher_notifications'))
