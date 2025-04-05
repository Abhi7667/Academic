from app import app, db
from models import Student, Subject, Performance, User
from datetime import datetime, timedelta

def init_test_data():
    with app.app_context():
        # Check if we already have test data
        if Performance.query.first() is None:
            # Create test user if needed
            user = User.query.filter_by(username='test_student').first()
            if not user:
                user = User(
                    username='test_student',
                    email='test@example.com',
                    role='student'
                )
                user.set_password('test123')
                db.session.add(user)
                db.session.commit()

            # Create test student if needed
            student = Student.query.filter_by(user_id=user.id).first()
            if not student:
                student = Student(
                    user_id=user.id,
                    grade='10',
                    roll_number='S001'
                )
                db.session.add(student)
                db.session.commit()

            # Create test subject if needed
            subject = Subject.query.filter_by(name='Mathematics').first()
            if not subject:
                subject = Subject(
                    name='Mathematics',
                    code='MATH101',
                    grade='10',
                    teacher_id=1  # Assuming teacher with ID 1 exists
                )
                db.session.add(subject)
                db.session.commit()

            # Add test performance records
            performance1 = Performance(
                student_id=student.id,
                subject_id=subject.id,
                assessment_type='quiz',
                score=85,
                max_score=100,
                date=datetime.now() - timedelta(days=7),
                comments='Good performance in quiz'
            )

            performance2 = Performance(
                student_id=student.id,
                subject_id=subject.id,
                assessment_type='exam',
                score=92,
                max_score=100,
                date=datetime.now() - timedelta(days=1),
                comments='Excellent work in final exam'
            )

            db.session.add(performance1)
            db.session.add(performance2)
            db.session.commit()

            print("Test data initialized successfully!")
        else:
            print("Performance records already exist in database")

        # Print current records
        print("\nCurrent Performance Records:")
        performances = Performance.query.all()
        for p in performances:
            print(f"Student: {p.student.user.username}, Subject: {p.subject.name}, Score: {p.score}/{p.max_score}")

if __name__ == '__main__':
    init_test_data()