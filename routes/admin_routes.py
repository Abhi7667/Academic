from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Teacher, Student, Subject, Timetable, Performance, Notification, TimetableChangeRequest
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
import logging
from datetime import time

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
    
    # Get the related profiles if they exist
    teacher_profile = Teacher.query.filter_by(user_id=user_id).first()
    student_profile = Student.query.filter_by(user_id=user_id).first()
    
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
            # Update basic user info
            user.username = username
            user.email = email
            user.is_active = is_active
            
            # Handle role change
            if user.role != role:
                # If changing to teacher
                if role == 'teacher' and not teacher_profile:
                    if student_profile:
                        db.session.delete(student_profile)
                    new_profile = Teacher(user_id=user.id)
                    db.session.add(new_profile)
                # If changing to student
                elif role == 'student' and not student_profile:
                    if teacher_profile:
                        db.session.delete(teacher_profile)
                    new_profile = Student(user_id=user.id)
                    db.session.add(new_profile)
                # If changing to admin
                elif role == 'admin':
                    if teacher_profile:
                        db.session.delete(teacher_profile)
                    if student_profile:
                        db.session.delete(student_profile)
                
                user.role = role
            
            # Update profile specific data if provided in the form
            if role == 'teacher' and teacher_profile and 'department' in request.form:
                teacher_profile.department = request.form['department']
            
            if role == 'student' and student_profile:
                if 'grade' in request.form:
                    student_profile.grade = request.form['grade']
                if 'roll_number' in request.form:
                    student_profile.roll_number = request.form['roll_number']
            
            # Update password if provided
            if 'password' in request.form and request.form['password']:
                user.set_password(request.form['password'])
            
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
            logger.error(f"User update error: {str(e)}")
    
    return render_template('admin/edit_user.html', user=user, teacher_profile=teacher_profile, student_profile=student_profile)

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

# Placeholder routes for new dashboard features
@admin.route('/subjects', methods=['GET', 'POST'])
@admin_required
def manage_subjects():
    # Create form for adding new subjects
    class SubjectForm(FlaskForm):
        name = StringField('Subject Name', validators=[DataRequired()])
        code = StringField('Subject Code', validators=[DataRequired()])
        type = SelectField('Subject Type', choices=[
            ('Theory', 'Theory'), 
            ('Practical', 'Practical'),
            ('Laboratory', 'Laboratory')
        ], validators=[DataRequired()])
        teacher_id = SelectField('Assign Teacher', coerce=int, validators=[DataRequired()])
        submit = SubmitField('Add Subject')
    
    # Get all teachers for the dropdown
    teachers = Teacher.query.join(User).filter(User.role == 'teacher').all()
    teacher_choices = [(teacher.id, teacher.user.username) for teacher in teachers]
    
    form = SubjectForm()
    form.teacher_id.choices = teacher_choices
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            subject = Subject(
                name=form.name.data,
                code=form.code.data,
                type=form.type.data,
                teacher_id=form.teacher_id.data
            )
            db.session.add(subject)
            db.session.commit()
            
            flash('Subject added successfully!', 'success')
            return redirect(url_for('admin.manage_subjects'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add subject: {str(e)}', 'danger')
            logger.error(f"Subject creation error: {str(e)}")
    
    # Get all subjects
    subjects = Subject.query.all()
    
    return render_template('admin/subjects.html', form=form, subjects=subjects)

@admin.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@admin_required
def delete_subject(subject_id):
    # Get subject
    subject = Subject.query.get_or_404(subject_id)
    
    try:
        db.session.delete(subject)
        db.session.commit()
        flash('Subject deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete subject: {str(e)}', 'danger')
        logger.error(f"Subject deletion error: {str(e)}")
    
    return redirect(url_for('admin.manage_subjects'))

@admin.route('/faculties')
@admin_required
def manage_faculties():
    # Query for users with the 'teacher' role
    faculties = User.query.filter_by(role='teacher').all()
    return render_template('admin/users.html', users=faculties, title="Manage Faculties")

@admin.route('/students')
@admin_required
def manage_students():
    # Query for users with the 'student' role
    students = User.query.filter_by(role='student').all()
    return render_template('admin/users.html', users=students, title="Manage Students")

@admin.route('/schedule', methods=['GET'])
@admin_required
def schedule_periods():
    selected_grade = request.args.get('grade')
    
    # Get distinct grades from Student table or Timetable table (or a predefined list)
    # Option 1: From Student table
    grades_query = db.session.query(Student.grade).distinct().filter(Student.grade.isnot(None))
    available_grades = sorted([g[0] for g in grades_query.all()])

    # Get all subjects with their teachers for the dropdowns
    available_subjects = Subject.query.options(db.joinedload(Subject.teacher).joinedload(Teacher.user)).order_by(Subject.code).all()
    
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
            # Break/Lunch (12-1 PM) - not scheduled
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
        'admin/schedule_periods.html',
        available_grades=available_grades,
        selected_grade=selected_grade,
        timetable_data=timetable_data,
        available_subjects=available_subjects
    )

@admin.route('/schedule/update', methods=['POST'])
@admin_required
def update_schedule():
    grade = request.form.get('grade')
    day = request.form.get('day')
    period_str = request.form.get('period')
    subject_id_str = request.form.get('subject_id')

    if not all([grade, day, period_str, subject_id_str]):
        flash('Missing data for timetable update.', 'danger')
        return redirect(url_for('admin.schedule_periods', grade=grade))

    try:
        period = int(period_str)
        # Define period start/end times (should match the display)
        period_times = {
            1: (time(9, 0), time(10, 0)),
            2: (time(10, 0), time(11, 0)),
            3: (time(11, 0), time(12, 0)),
            # Break/Lunch (12-1 PM) - not scheduled 
            4: (time(13, 0), time(14, 0)),
            5: (time(14, 0), time(15, 0)),
            6: (time(15, 0), time(16, 0)),
        }
        start_time, end_time = period_times.get(period)
        
        if not start_time:
             raise ValueError("Invalid period number.")

        # Check if removing the subject
        if subject_id_str.lower() == 'remove':
            # Find and delete existing entry
            existing_entry = Timetable.query.filter_by(
                grade=grade, day_of_week=day, start_time=start_time
            ).first()
            if existing_entry:
                db.session.delete(existing_entry)
                db.session.commit()
                flash(f'Period {period} on {day} cleared for grade {grade}.', 'info')
            else:
                 flash(f'No entry found to remove for Period {period} on {day} for grade {grade}.', 'warning')
            return redirect(url_for('admin.schedule_periods', grade=grade))

        # Adding or updating a subject
        subject_id = int(subject_id_str)
        subject = Subject.query.get(subject_id)
        if not subject:
            raise ValueError("Invalid Subject ID.")
            
        # Find existing entry for this slot
        existing_entry = Timetable.query.filter_by(
            grade=grade, day_of_week=day, start_time=start_time
        ).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.subject_id = subject.id
            existing_entry.teacher_id = subject.teacher_id
            flash(f'Timetable updated for Grade {grade}, {day}, Period {period}.', 'success')
        else:
            # Create new entry
            new_entry = Timetable(
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                grade=grade,
                subject_id=subject.id,
                teacher_id=subject.teacher_id,
                room='TBD' # Or fetch room info if available
            )
            db.session.add(new_entry)
            flash(f'Period scheduled for Grade {grade}, {day}, Period {period}.', 'success')
            
        db.session.commit()

    except ValueError as ve:
         db.session.rollback()
         flash(f'Invalid input: {str(ve)}', 'danger')
         logger.error(f"Timetable update ValueError: {str(ve)} - Data: {request.form}")
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating timetable: {str(e)}', 'danger')
        logger.error(f"Timetable update error: {str(e)}")

    return redirect(url_for('admin.schedule_periods', grade=grade))

@admin.route('/timetable/section', methods=['GET'])
@admin_required
def view_timetable_section():
    selected_grade = request.args.get('grade')
    
    # Get distinct available grades
    grades_query = db.session.query(Student.grade).distinct().filter(Student.grade.isnot(None))
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
        'admin/timetable_section.html',
        available_grades=available_grades,
        selected_grade=selected_grade,
        timetable_data=timetable_data
    )

@admin.route('/timetable/faculty', methods=['GET'])
@admin_required
def view_timetable_faculty():
    selected_teacher_id = request.args.get('teacher_id')
    
    # Get all teachers for the dropdown
    teachers = Teacher.query.join(User).filter(User.role == 'teacher').order_by(User.username).all()
    
    timetable_data = {}
    selected_teacher = None
    change_requests = []
    
    if selected_teacher_id:
        try:
            teacher_id = int(selected_teacher_id)
            selected_teacher = Teacher.query.get(teacher_id)
            
            if selected_teacher:
                # Fetch timetable entries for the selected teacher
                entries = Timetable.query.filter_by(teacher_id=teacher_id)\
                                       .options(db.joinedload(Timetable.subject))\
                                       .all()
                
                # Fetch pending change requests for this teacher
                change_requests = TimetableChangeRequest.query.filter_by(
                    teacher_id=teacher_id,
                    status='pending'
                ).order_by(TimetableChangeRequest.created_at.desc()).all()
                
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
                            # Store the entry, could potentially have multiple entries if teacher teaches same period in different grades
                            # For simplicity now, just store the last one found, or consider storing a list if needed
                            timetable_data[entry.day_of_week][period] = entry 
                            break # Found the period for this entry
            else:
                 flash(f'Teacher with ID {teacher_id} not found.', 'warning')
                 
        except ValueError:
             flash('Invalid Teacher ID specified.', 'danger')
             selected_teacher_id = None # Reset selection

    return render_template(
        'admin/timetable_faculty.html',
        teachers=teachers,
        selected_teacher_id=selected_teacher_id,
        selected_teacher=selected_teacher,
        timetable_data=timetable_data,
        change_requests=change_requests
    )

@admin.route('/timetable/change-request/<int:request_id>/<action>', methods=['POST'])
@admin_required
def handle_change_request(request_id, action):
    # Verify action is valid
    if action not in ['approve', 'reject']:
        flash('Invalid action specified.', 'danger')
        return redirect(url_for('admin.view_timetable_faculty'))
    
    # Get the change request
    change_request = TimetableChangeRequest.query.get_or_404(request_id)
    
    try:
        # Update the request status
        change_request.status = 'approved' if action == 'approve' else 'rejected'
        db.session.commit()
        
        # Get the teacher's name for the flash message
        teacher_name = change_request.teacher.user.username
        
        if action == 'approve':
            flash(f'Change request from {teacher_name} has been approved.', 'success')
            # Here you could also implement the actual schedule change if needed
        else:
            flash(f'Change request from {teacher_name} has been rejected.', 'info')
        
        # Redirect back to the faculty timetable view with the same teacher selected
        return redirect(url_for('admin.view_timetable_faculty', teacher_id=change_request.teacher_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing change request: {str(e)}', 'danger')
        return redirect(url_for('admin.view_timetable_faculty'))