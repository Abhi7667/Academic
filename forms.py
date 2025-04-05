from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, TimeField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class TeacherProfileForm(FlaskForm):
    department = StringField('Department', validators=[DataRequired()])
    submit = SubmitField('Save Profile')


class StudentProfileForm(FlaskForm):
    grade = StringField('Grade/Class', validators=[DataRequired()])
    roll_number = StringField('Roll Number', validators=[DataRequired()])
    submit = SubmitField('Save Profile')


class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    code = StringField('Subject Code', validators=[DataRequired()])
    submit = SubmitField('Save Subject')


class TimetableForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Day of Week', choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday')
    ], validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    room = StringField('Room', validators=[DataRequired()])
    grade = StringField('Grade/Class', validators=[DataRequired()])
    submit = SubmitField('Save Schedule')


class PerformanceForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    assessment_type = SelectField('Assessment Type', choices=[
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    score = FloatField('Score', validators=[DataRequired()])
    max_score = FloatField('Maximum Score', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    comments = TextAreaField('Comments')
    submit = SubmitField('Save Performance Record')


class NotificationForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    target_grade = StringField('Target Grade (leave empty for all)')
    submit = SubmitField('Send Notification')
