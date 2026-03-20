from __future__ import annotations

from flask import jsonify, render_template, request

from flavor_engine import engine
from models import Feedback, db


def register_routes(app):
    @app.route('/')
    def home():
        return render_template('base.html')

    @app.route('/api/overview')
    def overview():
        return jsonify(engine.get_overview())

    @app.route('/api/substitutions')
    def substitutions():
        seed = request.args.get('seed', 'Strawberry')
        category = request.args.get('category')
        compatibility = request.args.get('compatibility')
        allergen = request.args.get('exclude_allergen')
        try:
            return jsonify(engine.search_substitutions(seed, category, compatibility, allergen))
        except KeyError:
            return jsonify({'error': f'Unknown ingredient: {seed}'}), 404

    @app.route('/api/network')
    def network():
        return jsonify(engine.get_network())

    @app.route('/api/sensory-map')
    def sensory_map():
        return jsonify(engine.get_sensory_map())

    @app.route('/api/chat', methods=['POST'])
    def chat():
        payload = request.get_json(silent=True) or {}
        question = payload.get('question', '')
        return jsonify(engine.answer_question(question))

    @app.route('/api/feedback', methods=['POST'])
    def feedback():
        payload = request.get_json(silent=True) or {}
        item = Feedback(question=payload.get('question', ''), score=int(payload.get('score', 0)))
        db.session.add(item)
        db.session.commit()
        average = db.session.query(db.func.avg(Feedback.score)).scalar() or 0
        return jsonify({'average_feedback': round(float(average), 2)})
