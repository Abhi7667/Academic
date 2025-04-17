from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# This is for people who use our website
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)  # Your login name
    email = db.Column(db.String(120), unique=True, nullable=False)    # Your email address
    password_hash = db.Column(db.String(256), nullable=False)         # Your secret password
    role = db.Column(db.String(10), nullable=False)                   # Are you a teacher, student, or admin?
    created_at = db.Column(db.DateTime, default=datetime.utcnow)      # When you joined
    is_active = db.Column(db.Boolean, default=True)                   # Are you using the website?
    
    # Links to your teacher or student information
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    
    # Check if you're an admin
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    # Set your password safely
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # Check if your password is correct    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


# This is for teachers
class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Which user are you?
    department = db.Column(db.String(100))                                      # What do you teach?
    
    # What subjects you teach, your schedule, and messages you send
    subjects = db.relationship('Subject', backref='teacher', cascade='all, delete-orphan')
    timetables = db.relationship('Timetable', backref='teacher', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='teacher', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Teacher {self.user.username}>'


# This is for students
class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Which user are you?
    grade = db.Column(db.String(50))                                            # What grade are you in?
    roll_number = db.Column(db.String(20), unique=True)                         # Your student ID number
    
    # Your test scores and grades
    performances = db.relationship('Performance', backref='student', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.user.username}>'


# This is for school subjects
class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)                              # Subject name
    code = db.Column(db.String(20), nullable=False, unique=True)                  # Subject code
    type = db.Column(db.String(20), nullable=False, default='Theory')             # Theory or Practical?
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)  # Who teaches it?
    
    # Class schedule and student grades for this subject
    timetables = db.relationship('Timetable', backref='subject', cascade='all, delete-orphan')
    performances = db.relationship('Performance', backref='subject', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Subject {self.name}>'


# This is the class schedule
class Timetable(db.Model):
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)              # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)                     # When class starts
    end_time = db.Column(db.Time, nullable=False)                       # When class ends
    room = db.Column(db.String(20))                                     # Classroom number
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)  # Who teaches?
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)  # What subject?
    grade = db.Column(db.String(50), nullable=False)                    # What grade is this for?
    
    def __repr__(self):
        return f'<Timetable {self.subject.name} - {self.day_of_week}>'


# This is for test scores and grades
class Performance(db.Model):
    __tablename__ = 'performances'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)  # Which student?
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)  # Which subject?
    assessment_type = db.Column(db.String(50), nullable=False)  # Quiz, test, homework, etc.
    score = db.Column(db.Float, nullable=False)                 # Points you got
    max_score = db.Column(db.Float, nullable=False)             # Total possible points
    date = db.Column(db.Date, nullable=False)                   # When was the test?
    comments = db.Column(db.Text)                               # Teacher's notes
    
    def __repr__(self):
        return f'<Performance {self.student.user.username} - {self.subject.name}>'


# This is for messages and announcements
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)                                # Message title
    message = db.Column(db.Text, nullable=False)                                     # The message
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False) # Who sent it?
    target_grade = db.Column(db.String(50))                                          # Who should see it?
    created_at = db.Column(db.DateTime, default=datetime.utcnow)                     # When was it sent?
    
    def __repr__(self):
        return f'<Notification {self.title}>'


# This is for teacher timetable change requests
class TimetableChangeRequest(db.Model):
    __tablename__ = 'timetable_change_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)  # Which teacher requested?
    type = db.Column(db.String(50), nullable=False)                                   # Type of change (schedule, room, etc.)
    day = db.Column(db.String(10), nullable=False)                                    # Which day?
    period = db.Column(db.Integer, nullable=False)                                    # Which period?
    date = db.Column(db.Date)                                                         # Specific date if applicable
    reason = db.Column(db.Text, nullable=False)                                       # Reason for change
    status = db.Column(db.String(20), default='pending')                              # Status (pending, approved, rejected)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)                      # When was it requested?
    
    # Link to the teacher who made the request
    teacher = db.relationship('Teacher', backref='change_requests')
    
    def __repr__(self):
        return f'<TimetableChangeRequest {self.teacher.user.username} - {self.day} Period {self.period}>'
