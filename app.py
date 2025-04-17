import os
from flask import Flask, render_template
from extensions import db, login_manager

# This is where we set up our website
app = Flask(__name__)

# This is like a secret password for our website
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# This tells our website where to store information
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Start up our database and login system
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Get ready to store information
with app.app_context():
    from models import User, Student, Teacher, Subject, Timetable, Performance, Notification
    db.create_all()

# This helps our website remember who is logged in
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Add all the different pages to our website
from routes.auth_routes import auth as auth_bp
from routes.teacher_routes import teacher as teacher_bp
from routes.student_routes import student as student_bp
from routes.notification_routes import notification as notification_bp
from routes.admin_routes import admin as admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(student_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(admin_bp)

# This is what shows up when you visit the main page
@app.route('/')
def index():
    return render_template('index.html')

# These handle errors when something goes wrong
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

# This starts our website when we run this file
if __name__ == "__main__":
    app.run(debug=True)
