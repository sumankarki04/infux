import bleach
import os
import uuid
from PIL import Image, UnidentifiedImageError
from flask import current_app


def clean(value):
    return bleach.clean(str(value).strip(), tags=[], strip=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload(file, prefix='img'):
    """Save an uploaded image safely.

    The file extension alone is spoofable, so the bytes are validated as a real
    image with Pillow and re-encoded (which strips any embedded payload / EXIF /
    polyglot content). The stored extension comes from the *detected* format, and
    the filename is server-generated, so there is no path-traversal or
    content-type-confusion vector.
    """
    if not file or not file.filename or not allowed_file(file.filename):
        return None

    try:
        file.stream.seek(0)
        Image.open(file.stream).verify()        # validate structure
        file.stream.seek(0)
        img = Image.open(file.stream)            # reopen — verify() consumes it
    except (UnidentifiedImageError, OSError, ValueError):
        return None

    fmt = (img.format or '').lower()
    fmt = 'jpg' if fmt == 'jpeg' else fmt
    if fmt not in current_app.config['ALLOWED_EXTENSIONS']:
        return None

    filename = f'{prefix}_{uuid.uuid4().hex[:8]}.{fmt}'
    img.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return filename


def format_number(n):
    if n is None:
        return '0'
    if n >= 1_000_000:
        return f'{n/1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n/1_000:.1f}K'
    return str(n)
