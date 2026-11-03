import os
import time
from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def get_db_connection(retries=20, delay=2):
    for attempt in range(retries):
        try:
            return mysql.connector.connect(
                host=os.getenv("DB_HOST", "db"),
                user=os.getenv("DB_USER", "devops"),
                password=os.getenv("DB_PASSWORD", "devops123"),
                database=os.getenv("DB_NAME", "devopsdb"),
                port=int(os.getenv("DB_PORT", "3306")),
                connection_timeout=5,
            )
        except Error:
            if attempt == retries - 1:
                raise
            time.sleep(delay)

def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            content VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()

# O Gunicorn importa este módulo sem executar o bloco __main__.
# Inicializamos a tabela durante a inicialização do container.
initialize_database()

@app.get("/")
def home():
    return jsonify({
        "application": "UGB DevOps API",
        "message": "API executando em container",
        "endpoints": ["/health", "/messages"]
    })

@app.get("/health")
def health():
    try:
        connection = get_db_connection(retries=1)
        connection.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Error as exc:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(exc)}), 503

@app.get("/messages")
def list_messages():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    for row in rows:
        row["created_at"] = row["created_at"].isoformat() if row["created_at"] else None
    return jsonify(rows)

@app.post("/messages")
def create_message():
    data = request.get_json(silent=True) or {}
    content = data.get("content")
    if not isinstance(content, str) or not content.strip():
        return jsonify({"error": "Envie um campo 'content' não vazio."}), 400
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO messages (content) VALUES (%s)", (content.strip(),))
    connection.commit()
    message_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return jsonify({"id": message_id, "content": content.strip()}), 201

if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
