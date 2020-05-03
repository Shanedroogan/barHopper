from app import app, db
from app.models import User, Crawl, Bar_MasterList, Deal

@app.shell_context_processor
def make_shell_context():
    """Used for testing in virtual python environment"""
    return {'db' : db,
            'User' : User, 
            'Crawl' : Crawl, 
            'Bar_MasterList' : Bar_MasterList, 
            'Deal' : Deal}