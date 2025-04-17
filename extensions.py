from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# This helps us store information in our database
db = SQLAlchemy()

# This helps remember who is using the website
login_manager = LoginManager()
