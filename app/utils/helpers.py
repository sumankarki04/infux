import bleach
import os
from werkzeug.utils import secure_filename
from flask import current_app


def clean(value):
    return bleach.clean(str(value).strip(), tags=[], strip=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload(file, prefix='img'):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        import uuid
        filename = f'{prefix}_{uuid.uuid4().hex[:8]}.{ext}'
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        return filename
    return None


def format_number(n):
    if n is None:
        return '0'
    if n >= 1_000_000:
        return f'{n/1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n/1_000:.1f}K'
    return str(n)
