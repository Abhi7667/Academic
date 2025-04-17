import os

# This file has settings for our website

# Database settings - where to store all the information
DATABASE_URL = "sqlite:///database.db"

# Website settings
class Config:
    # Secret code for safety
    SECRET_KEY = "school_website_secret_key"
    
    # Where to find the database
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    # Technical setting we don't need to worry about
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Show errors when they happen
    DEBUG = True
