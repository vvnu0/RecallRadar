from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(512), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Feedback {self.id}: {self.score}>'
