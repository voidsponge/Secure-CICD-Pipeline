"""SecureNotes : une petite API de notes, terrain de jeu du pipeline DevSecOps."""

import os
import sqlite3

from flask import Flask, g, jsonify, request

MAX_TITLE_LEN = 120
MAX_BODY_LEN = 5000


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("NOTES_DB", "notes.db"),
        MAX_CONTENT_LENGTH=16 * 1024,  # refuse les requêtes trop volumineuses
        JSON_SORT_KEYS=False,
    )
    if config:
        app.config.update(config)

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT NOT NULL, "
            "body TEXT NOT NULL)"
        )
        get_db().commit()

    @app.after_request
    def security_headers(response):
        # En-têtes recommandés par l'OWASP Secure Headers Project
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(error="not found"), 404

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(error="payload too large"), 413

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/notes")
    def list_notes():
        rows = get_db().execute("SELECT id, title, body FROM notes ORDER BY id").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int):
        # Requête paramétrée : aucune concaténation de l'entrée utilisateur
        row = (
            get_db()
            .execute("SELECT id, title, body FROM notes WHERE id = ?", (note_id,))
            .fetchone()
        )
        if row is None:
            return jsonify(error="not found"), 404
        return jsonify(dict(row))

    @app.post("/notes")
    def create_note():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="expected a JSON object"), 400

        title, body = data.get("title"), data.get("body")
        if not isinstance(title, str) or not isinstance(body, str):
            return jsonify(error="title and body must be strings"), 400
        title, body = title.strip(), body.strip()
        if not title or len(title) > MAX_TITLE_LEN:
            return jsonify(error=f"title must be 1-{MAX_TITLE_LEN} characters"), 400
        if len(body) > MAX_BODY_LEN:
            return jsonify(error=f"body must be at most {MAX_BODY_LEN} characters"), 400

        db = get_db()
        cur = db.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body))
        db.commit()
        return jsonify(id=cur.lastrowid, title=title, body=body), 201

    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int):
        db = get_db()
        cur = db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        db.commit()
        if cur.rowcount == 0:
            return jsonify(error="not found"), 404
        return "", 204

    return app
