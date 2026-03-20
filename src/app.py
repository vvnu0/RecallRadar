import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from models import Feedback, db
from routes import register_routes

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
register_routes(app)

with app.app_context():
    db.create_all()
    if Feedback.query.count() == 0:
        db.session.add(Feedback(question='seeded feedback', score=5))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5001)))
