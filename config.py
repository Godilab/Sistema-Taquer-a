import os

class Config:
    SECRET_KEY = 'taqueria_idgs803_utl_2026'
    
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://adminDB:Admin123@localhost/taqueria'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'diegolanderosbolanos.23@gmail.com'
    MAIL_PASSWORD = 'xkeojwsaionljqwd'
    MAIL_DEFAULT_SENDER = 'diegolanderosbolanos.23@gmail.com'

    
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_LOCK_MINUTES = 15