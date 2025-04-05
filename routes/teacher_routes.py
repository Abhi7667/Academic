from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Subject, Timetable, Performance, Student, Teacher
from forms import SubjectForm, TimetableForm, PerformanceForm
from sqlalchemy import func
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
teacher = Blueprint('teacher', __name__, url_prefix='/teacher')

# Decorator to check if user is a teacher
def teacher_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Access denied: Teacher permissions required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@teacher.route('/dashboard')
@teacher_required
def dashboard():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get counts for dashboard stats
    subjects_count = Subject.query.filter_by(teacher_id=teacher_profile.id).count()
    classes_count = Timetable.query.filter_by(teacher_id=teacher_profile.id).count()
    
    # Get performances by subject for chart
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    subject_data = []
    performance_data = []
    
    for subject in subjects:
        subject_data.append(subject.name)
        
        # Calculate average performance for this subject
        avg_score = db.session.query(
            func.avg(Performance.score / Performance.max_score * 100)
        ).filter_by(subject_id=subject.id).scalar() or 0
        
        performance_data.append(round(avg_score, 2))
    
    # Get recent performances
    recent_performances = db.session.query(
        Performance, Student, Subject
    ).join(
        Student, Performance.student_id == Student.id
    ).join(
        Subject, Performance.subject_id == Subject.id
    ).filter(
        Subject.teacher_id == teacher_profile.id
    ).order_by(
        Performance.date.desc()
    ).limit(5).all()
    
    # Get today's classes
    today = datetime.now().strftime("%A")
    today_classes = db.session.query(
        Timetable, Subject
    ).join(
        Subject, Timetable.subject_id == Subject.id
    ).filter(
        Timetable.teacher_id == teacher_profile.id,
        Timetable.day_of_week == today
    ).order_by(
        Timetable.start_time
    ).all()
    
    return render_template(
        'teacher/dashboard.html',
        subjects_count=subjects_count,
        classes_count=classes_count,
        subject_data=subject_data,
        performance_data=performance_data,
        recent_performances=recent_performances,
        today_classes=today_classes,
        today=today
    )

@teacher.route('/subjects', methods=['GET', 'POST'])
@teacher_required
def subjects():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Form for adding new subjects
    form = SubjectForm()
    
    if form.validate_on_submit():
        try:
            subject = Subject(
                name=form.name.data,
                code=form.code.data,
                teacher_id=teacher_profile.id
            )
            db.session.add(subject)
            db.session.commit()
            
            flash('Subject added successfully!', 'success')
            return redirect(url_for('teacher.subjects'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add subject: {str(e)}', 'danger')
            logger.error(f"Subject creation error: {str(e)}")
    
    # Get all subjects for this teacher
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    
    return render_template('teacher/subjects.html', form=form, subjects=subjects)

@teacher.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@teacher_required
def delete_subject(subject_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get subject and verify ownership
    subject = Subject.query.filter_by(id=subject_id, teacher_id=teacher_profile.id).first_or_404()
    
    try:
        db.session.delete(subject)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete subject: {str(e)}', 'danger')
        logger.error(f"Subject deletion error: {str(e)}")
    
    return redirect(url_for('teacher.subjects'))

@teacher.route('/timetable', methods=['GET', 'POST'])
@teacher_required
def timetable():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Form for adding timetable entries
    form = TimetableForm()
    
    # Populate subject choices
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in subjects]
    
    if form.validate_on_submit():
        try:
            timetable_entry = Timetable(
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                room=form.room.data,
                teacher_id=teacher_profile.id,
                subject_id=form.subject_id.data,
                grade=form.grade.data
            )
            db.session.add(timetable_entry)
            db.session.commit()
            
            flash('Timetable entry added successfully!', 'success')
            return redirect(url_for('teacher.timetable'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add timetable entry: {str(e)}', 'danger')
            logger.error(f"Timetable creation error: {str(e)}")
    
    # Get timetable entries for this teacher
    days_order = {
        'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 
        'Thursday': 4, 'Friday': 5, 'Saturday': 6
    }
    
    timetable_entries = db.session.query(
        Timetable, Subject
    ).join(
        Subject, Timetable.subject_id == Subject.id
    ).filter(
        Timetable.teacher_id == teacher_profile.id
    ).all()
    
    # Sort by day and time
    timetable_entries.sort(key=lambda x: (days_order.get(x[0].day_of_week, 7), x[0].start_time))
    
    return render_template('teacher/timetable.html', form=form, timetable_entries=timetable_entries)

@teacher.route('/timetable/delete/<int:timetable_id>', methods=['POST'])
@teacher_required
def delete_timetable(timetable_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get timetable entry and verify ownership
    timetable_entry = Timetable.query.filter_by(id=timetable_id, teacher_id=teacher_profile.id).first_or_404()
    
    try:
        db.session.delete(timetable_entry)
        db.session.commit()
        flash('Timetable entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete timetable entry: {str(e)}', 'danger')
        logger.error(f"Timetable deletion error: {str(e)}")
    
    return redirect(url_for('teacher.timetable'))

@teacher.route('/performance', methods=['GET', 'POST'])
@teacher_required
def student_performance():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Form for adding performance records
    form = PerformanceForm()
    
    # Populate subject choices
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in subjects]
    
    # Populate student choices - based on subjects taught by this teacher
    # We'll get all students from grades that this teacher teaches
    grades_taught = db.session.query(Timetable.grade).filter_by(teacher_id=teacher_profile.id).distinct().all()
    grades_list = [g[0] for g in grades_taught]
    
    students = Student.query.filter(Student.grade.in_(grades_list)).all()
    form.student_id.choices = [(s.id, f"{s.user.username} ({s.roll_number} - {s.grade})") for s in students]
    
    if form.validate_on_submit():
        try:
            performance = Performance(
                student_id=form.student_id.data,
                subject_id=form.subject_id.data,
                assessment_type=form.assessment_type.data,
                score=form.score.data,
                max_score=form.max_score.data,
                date=form.date.data,
                comments=form.comments.data
            )
            db.session.add(performance)
            db.session.commit()
            
            flash('Performance record added successfully!', 'success')
            return redirect(url_for('teacher.student_performance'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add performance record: {str(e)}', 'danger')
            logger.error(f"Performance record creation error: {str(e)}")
    
    # Get performance records for subjects taught by this teacher
    subject_ids = [subject.id for subject in subjects]
    
    performance_records = db.session.query(
        Performance, Student, Subject
    ).join(
        Student, Performance.student_id == Student.id
    ).join(
        Subject, Performance.subject_id == Subject.id
    ).filter(
        Subject.id.in_(subject_ids)
    ).order_by(
        Performance.date.desc()
    ).all()
    
    return render_template(
        'teacher/student_performance.html', 
        form=form, 
        performance_records=performance_records
    )

@teacher.route('/performance/delete/<int:performance_id>', methods=['POST'])
@teacher_required
def delete_performance(performance_id):
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get performance record and verify it's for a subject taught by this teacher
    performance = Performance.query.join(Subject).filter(
        Performance.id == performance_id,
        Subject.teacher_id == teacher_profile.id
    ).first_or_404()
    
    try:
        db.session.delete(performance)
        db.session.commit()
        flash('Performance record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete performance record: {str(e)}', 'danger')
        logger.error(f"Performance deletion error: {str(e)}")
    
    return redirect(url_for('teacher.student_performance'))
