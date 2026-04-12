import json
import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from policylens_handler import PolicyLensHandler

app = Flask(__name__, static_folder='.', static_url_path='')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'temp_uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

handler = PolicyLensHandler()


def save_temp_pdf(file_storage):
    filename = secure_filename(file_storage.filename or 'upload.pdf')
    temp_path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(temp_path)
    return temp_path


def extract_pdf_text_from_upload(pdf_file):
    temp_path = save_temp_pdf(pdf_file)
    try:
        text = handler.extract_pdf_text(temp_path)
        if text.startswith('Error'):
            return None, text
        return text, None
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


@app.route('/')
def index():
    return send_from_directory('.', 'policylens_frontend.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)


@app.route('/api/summary', methods=['POST'])
def api_summary():
    if 'pdf' not in request.files:
        return jsonify(error='No PDF file uploaded'), 400

    pdf = request.files['pdf']
    summary_type = request.form.get('type', 'brief')
    _, error = extract_pdf_text_from_upload(pdf)
    if error:
        return jsonify(error=error), 400

    summary = handler.generate_summary(summary_type)
    return jsonify(summary=summary)


@app.route('/api/snapshot', methods=['POST'])
def api_snapshot():
    if 'pdf' not in request.files:
        return jsonify(error='No PDF file uploaded'), 400

    pdf = request.files['pdf']
    _, error = extract_pdf_text_from_upload(pdf)
    if error:
        return jsonify(error=error), 400

    snapshot_json_str = handler.generate_snapshot()
    try:
        snapshot_data = json.loads(snapshot_json_str)
        return jsonify(snapshot=snapshot_data)
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return the error with the raw response for debugging
        return jsonify(error=f'Invalid JSON in snapshot: {str(e)}', raw=snapshot_json_str), 502


@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'pdf' not in request.files:
        return jsonify(error='No PDF file uploaded'), 400
    if not request.form.get('question'):
        return jsonify(error='Question is required'), 400

    pdf = request.files['pdf']
    _, error = extract_pdf_text_from_upload(pdf)
    if error:
        return jsonify(error=error), 400

    question = request.form['question']
    answer = handler.ask_question(question)
    return jsonify(answer=answer)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
