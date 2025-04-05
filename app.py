import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv
from extensions import db, login_manager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)

# Security configuration
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    logger.warning("No SECRET_KEY found in environment variables. Using a temporary key for development.")
    app.secret_key = os.urandom(24)

# Configure database with fallback to SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Import models and create tables
with app.app_context():
    from models import User, Student, Teacher, Subject, Timetable, Performance, Notification
    db.create_all()
    logger.debug("Database tables created successfully.")

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register blueprints
from routes.auth_routes import auth as auth_bp
from routes.teacher_routes import teacher as teacher_bp
from routes.student_routes import student as student_bp
from routes.notification_routes import notification as notification_bp

app.register_blueprint(auth_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(student_bp)
app.register_blueprint(notification_bp)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

if __name__ == "__main__":
    app.run(debug=True)
