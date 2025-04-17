from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Subject, Timetable, Performance, Student, Teacher, User, TimetableChangeRequest
from forms import SubjectForm, TimetableForm, PerformanceForm
from sqlalchemy import func
import logging
from datetime import datetime, time, date

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
                type=form.type.data,
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
    # Redirect to timetable_section since we've removed the My Timetable view
    return redirect(url_for('teacher.timetable_section'))

# Keep the original implementation as a separate function for the API
@teacher.route('/timetable/manage', methods=['GET', 'POST'])
@teacher_required
def manage_timetable():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Form for adding timetable entries
    form = TimetableForm()
    
    # Get all subjects for this teacher for dropdowns
    subjects = Subject.query.filter_by(teacher_id=teacher_profile.id).all()
    
    # Populate form subject choices
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
            return redirect(url_for('teacher.manage_timetable'))
            
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
    
    return render_template(
        'teacher/timetable.html',
        form=form,
        timetable_entries=timetable_entries,
        subjects=subjects
    )

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
    
    return redirect(url_for('teacher.manage_timetable'))

@teacher.route('/update_timetable', methods=['POST'])
@teacher_required
def update_timetable():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    try:
        subject_id = request.form.get('subject_id')
        day = request.form.get('day')
        period = int(request.form.get('period'))
        
        # Calculate time based on period
        start_hour = 8 + period
        end_hour = start_hour + 1
        start_time = datetime.strptime(f"{start_hour}:00", "%H:%M").time()
        end_time = datetime.strptime(f"{end_hour}:00", "%H:%M").time()
        
        # Check if an entry already exists for this slot
        existing_entry = Timetable.query.filter_by(
            teacher_id=teacher_profile.id,
            day_of_week=day,
            start_time=start_time
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.subject_id = subject_id
            flash('Timetable updated successfully!', 'success')
        else:
            # Create new entry
            subject = Subject.query.get(subject_id)
            timetable_entry = Timetable(
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                room=subject.room if hasattr(subject, 'room') else 'TBD',
                teacher_id=teacher_profile.id,
                subject_id=subject_id,
                grade=subject.grade if hasattr(subject, 'grade') else 'TBD'
            )
            db.session.add(timetable_entry)
            flash('New timetable entry added successfully!', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update timetable: {str(e)}', 'danger')
        logger.error(f"Timetable update error: {str(e)}")
    
    return redirect(url_for('teacher.manage_timetable'))

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

@teacher.route('/timetable_section', methods=['GET'])
@teacher_required
def timetable_section():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    selected_grade = request.args.get('grade')
    
    # Get distinct available grades
    grades_query = db.session.query(Timetable.grade).distinct().filter(Timetable.grade.isnot(None))
    available_grades = sorted([g[0] for g in grades_query.all()])
    
    timetable_data = {}
    if selected_grade:
        # Fetch timetable entries for the selected grade
        entries = Timetable.query.filter_by(grade=selected_grade)\
                               .options(db.joinedload(Timetable.subject), db.joinedload(Timetable.teacher).joinedload(Teacher.user))\
                               .all()
        
        # Organize data for the template: {day: {period: entry}}
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        period_times = {
            1: (time(9, 0), time(10, 0)),
            2: (time(10, 0), time(11, 0)),
            3: (time(11, 0), time(12, 0)),
            4: (time(13, 0), time(14, 0)),
            5: (time(14, 0), time(15, 0)),
            6: (time(15, 0), time(16, 0)),
        }

        for day in days_order:
            timetable_data[day] = {}
            
        for entry in entries:
            for period, (start, end) in period_times.items():
                if entry.start_time == start:
                    timetable_data[entry.day_of_week][period] = entry
                    break # Found the period for this entry

    return render_template(
        'teacher/timetable_section.html',
        available_grades=available_grades,
        selected_grade=selected_grade,
        timetable_data=timetable_data
    )

@teacher.route('/timetable_faculty', methods=['GET'])
@teacher_required
def timetable_faculty():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    selected_teacher_id = request.args.get('teacher_id')
    
    # Get all teachers for the dropdown
    teachers = Teacher.query.join(User).filter(User.role == 'teacher').order_by(User.username).all()
    
    timetable_data = {}
    selected_teacher = None
    
    if selected_teacher_id:
        try:
            teacher_id = int(selected_teacher_id)
            selected_teacher = Teacher.query.get(teacher_id)
            
            if selected_teacher:
                # Fetch timetable entries for the selected teacher
                entries = Timetable.query.filter_by(teacher_id=teacher_id)\
                                       .options(db.joinedload(Timetable.subject))\
                                       .all()
                
                # Organize data for the template: {day: {period: entry}}
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                period_times = {
                    1: (time(9, 0), time(10, 0)),
                    2: (time(10, 0), time(11, 0)),
                    3: (time(11, 0), time(12, 0)),
                    4: (time(13, 0), time(14, 0)),
                    5: (time(14, 0), time(15, 0)),
                    6: (time(15, 0), time(16, 0)),
                }

                for day in days_order:
                    timetable_data[day] = {}
                    
                for entry in entries:
                    for period, (start, end) in period_times.items():
                        if entry.start_time == start:
                            timetable_data[entry.day_of_week][period] = entry
                            break # Found the period for this entry
        except Exception as e:
            flash(f'Error loading faculty timetable: {str(e)}', 'danger')
            logger.error(f"Faculty timetable error: {str(e)}")

    return render_template(
        'teacher/timetable_faculty.html',
        teachers=teachers,
        selected_teacher=selected_teacher,
        selected_teacher_id=selected_teacher_id,
        timetable_data=timetable_data
    )

# Handle the timetable change request submission
@teacher.route('/submit_timetable_change_request', methods=['POST'])
@teacher_required
def submit_timetable_change_request():
    # Get teacher profile
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    
    # Get data from request
    data = request.json
    
    try:
        # Parse date if provided
        request_date = None
        if data.get('date') and data['date'].strip():
            request_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Create change request
        change_request = TimetableChangeRequest(
            teacher_id=teacher_profile.id,
            type=data['type'],
            day=data['day'],
            period=int(data['period']),
            date=request_date,
            reason=data['reason'],
            status='pending'
        )
        
        db.session.add(change_request)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Your change request has been submitted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Change request submission error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to submit change request: {str(e)}'
        }), 500
