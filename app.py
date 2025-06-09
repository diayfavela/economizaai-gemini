import os
import base64
import mimetypes
import threading
import uuid
from flask import Flask, request, jsonify
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv

load_dotenv()
configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)

# Armazena jobs em memória (demonstração)
JOBS = {}

SUPPORTED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif']

def process_job(job_id, data, is_text=False):
    try:
        prompt = """Você é um assistente especializado em interpretar cupons fiscais brasileiros...
        5. Extraia obrigatoriamente a chave de acesso completa (44 dígitos)..."""
        if is_text:
            response = model.generate_content([prompt, data])
        else:
            response = model.generate_content([prompt, {"mime_type": data['mime_type'], "data": data['base64']}])
        text = response.text
        import json
        cleaned = text.replace("```json\n", "").replace("```", "").strip()
        dados = json.loads(cleaned)
        dados['access_key'] = dados.get('access_key', '')
        JOBS[job_id] = {"status": "done", "result": dados}
    except Exception as e:
        JOBS[job_id] = {"status": "error", "error": str(e)}

@app.route("/api/interpretar-cupom", methods=["POST"])
def interpretar_cupom():
    if 'image' not in request.files:
        return jsonify({"error": "Nenhuma imagem"}), 400
    f = request.files['image']
    mime_type, _ = mimetypes.guess_type(f.filename)
    if mime_type not in SUPPORTED_MIME_TYPES:
        return jsonify({"error": "Formato não suportado"}), 400
    img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "processing"}
    threading.Thread(
        target=process_job,
        args=(job_id, {'base64': img_b64, 'mime_type': mime_type}, False)
    ).start()
    return jsonify({"jobId": job_id}), 202

@app.route("/api/interpretar-cupom-texto", methods=["POST"])
def interpretar_cupom_texto():
    if not request.is_json:
        return jsonify({"error": "Corpo deve ser JSON"}), 400
    data = request.get_json()
    if 'text' not in data:
        return jsonify({"error": "Campo 'text' é obrigatório"}), 400
    text = data['text']
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "processing"}
    threading.Thread(
        target=process_job,
        args=(job_id, text, True)
    ).start()
    return jsonify({"jobId": job_id}), 202

@app.route("/api/status", methods=["GET"])
def status():
    job_id = request.args.get("jobId")
    if job_id not in JOBS:
        return jsonify({"error": "JobId inválido"}), 404
    job = JOBS[job_id]
    if job["status"] == "processing":
        return jsonify({"status": "processing"}), 202
    if job["status"] == "error":
        return jsonify({"status": "error", "error": job["error"]}), 500
    return jsonify({"status": "done", "data": job["result"]}), 200

if __name__ == "__main__":
    app.run(debug=True)