from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Student, Performance, Subject, Timetable, Notification, Teacher, User
from sqlalchemy import func
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
student = Blueprint('student', __name__, url_prefix='/student')

# Decorator to check if user is a student
def student_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied: Student permissions required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@student.route('/dashboard')
@student_required
def dashboard():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash('Student profile not found. Please complete your profile.', 'warning')
        return redirect(url_for('auth.complete_student_profile'))
    
    # Get performance data for charts
    performances = db.session.query(
        Subject.name,
        func.avg(Performance.score / Performance.max_score * 100).label('avg_score')
    ).join(
        Performance, Subject.id == Performance.subject_id
    ).filter(
        Performance.student_id == student_profile.id
    ).group_by(
        Subject.name
    ).all()
    
    subjects = [p[0] for p in performances]
    scores = [round(p[1], 2) for p in performances]
    
    # Get recent performance records
    recent_performances = db.session.query(
        Performance, Subject
    ).join(
        Subject, Performance.subject_id == Subject.id
    ).filter(
        Performance.student_id == student_profile.id
    ).order_by(
        Performance.date.desc()
    ).limit(5).all()
    
    # Calculate overall performance
    overall_performance = db.session.query(
        func.avg(Performance.score / Performance.max_score * 100)
    ).filter(
        Performance.student_id == student_profile.id
    ).scalar() or 0
    
    overall_performance = round(overall_performance, 2)
    
    # Get available grades
    available_grades = db.session.query(Timetable.grade).distinct().order_by(Timetable.grade).all()
    available_grades = [grade[0] for grade in available_grades]
    
    # Get selected grade from request or default to student's grade
    selected_grade = request.args.get('grade', student_profile.grade)
    
    # Verify the selected grade exists in available grades
    if selected_grade not in available_grades and available_grades:
        selected_grade = available_grades[0]
    
    # Get today's classes
    today = datetime.now().strftime("%A")
    
    # Query today's classes with teacher information
    today_classes = db.session.query(
        Timetable, Subject, Teacher, User
    ).join(
        Subject, Timetable.subject_id == Subject.id
    ).join(
        Teacher, Timetable.teacher_id == Teacher.id
    ).join(
        User, Teacher.user_id == User.id
    ).filter(
        Timetable.grade == selected_grade,
        Timetable.day_of_week == today
    ).order_by(
        Timetable.start_time
    ).all()
    
    # Format classes like timetable page
    formatted_classes = []
    for entry in today_classes:
        timetable, subject, teacher, teacher_user = entry
        formatted_classes.append({
            'timetable': timetable,
            'subject': subject,
            'teacher': teacher,
            'teacher_user': teacher_user
        })
    
    # Get recent notifications for this student's grade
    recent_notifications = Notification.query.filter(
        (Notification.target_grade == student_profile.grade) | 
        (Notification.target_grade == None) |
        (Notification.target_grade == '')
    ).order_by(
        Notification.created_at.desc()
    ).limit(3).all()
    
    return render_template(
        'student/dashboard.html',
        student=student_profile,
        subjects=subjects,
        scores=scores,
        recent_performances=recent_performances,
        overall_performance=overall_performance,
        today_classes=formatted_classes,
        today=today,
        recent_notifications=recent_notifications,
        available_grades=available_grades,
        selected_grade=selected_grade
    )

@student.route('/timetable')
@student_required
def timetable():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash('Student profile not found. Please complete your profile.', 'warning')
        return redirect(url_for('auth.complete_student_profile'))
    
    # Get available grades
    available_grades = db.session.query(Timetable.grade).distinct().order_by(Timetable.grade).all()
    available_grades = [grade[0] for grade in available_grades]
    
    # Get selected grade from request or default to student's grade
    selected_grade = request.args.get('grade', student_profile.grade)
    
    # Verify the selected grade exists in available grades
    if selected_grade not in available_grades and available_grades:
        selected_grade = available_grades[0]
    
    # Get timetable for selected grade
    days_order = {
        'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 
        'Thursday': 4, 'Friday': 5, 'Saturday': 6
    }
    
    # Query timetable entries with subject and teacher information
    timetable_entries = db.session.query(
        Timetable, Subject, Teacher, User
    ).join(
        Subject, Timetable.subject_id == Subject.id
    ).join(
        Teacher, Timetable.teacher_id == Teacher.id
    ).join(
        User, Teacher.user_id == User.id
    ).filter(
        Timetable.grade == selected_grade
    ).all()
    
    # Sort by day and time
    timetable_entries.sort(key=lambda x: (days_order.get(x[0].day_of_week, 7), x[0].start_time))
    
    # Group by day for easier display
    timetable_by_day = {}
    for day in days_order.keys():
        timetable_by_day[day] = []
    
    for entry in timetable_entries:
        timetable, subject, teacher, teacher_user = entry
        # Create a custom object with all data needed in template
        timetable_by_day[timetable.day_of_week].append({
            'timetable': timetable,
            'subject': subject,
            'teacher': teacher,
            'teacher_user': teacher_user
        })
    
    return render_template(
        'student/timetable.html',
        timetable_by_day=timetable_by_day,
        days=list(days_order.keys()),
        available_grades=available_grades,
        selected_grade=selected_grade
    )

@student.route('/performance')
@student_required
def performance():
    # Get student profile
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student_profile:
        flash('Student profile not found. Please complete your profile.', 'warning')
        return redirect(url_for('auth.complete_student_profile'))
    
    # Get performance records grouped by subject
    subjects = db.session.query(Subject).join(
        Performance, Subject.id == Performance.subject_id
    ).filter(
        Performance.student_id == student_profile.id
    ).distinct().all()
    
    performance_by_subject = {}
    
    for subject in subjects:
        performances = db.session.query(Performance).filter(
            Performance.student_id == student_profile.id,
            Performance.subject_id == subject.id
        ).order_by(Performance.date.desc()).all()
        
        # Calculate average for this subject
        avg_score = sum([p.score / p.max_score * 100 for p in performances]) / len(performances)
        
        performance_by_subject[subject] = {
            'performances': performances,
            'average': round(avg_score, 2)
        }
    
    # Calculate overall average
    if performance_by_subject:
        overall_avg = sum([data['average'] for data in performance_by_subject.values()]) / len(performance_by_subject)
        overall_avg = round(overall_avg, 2)
    else:
        overall_avg = 0
    
    return render_template(
        'student/performance.html',
        performance_by_subject=performance_by_subject,
        overall_avg=overall_avg
    )
