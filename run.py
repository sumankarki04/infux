import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debugger off unless explicitly requested (safer when exposed via a tunnel);
    # no reloader so the process stays stable.
    _dbg = os.getenv('FLASK_DEBUG')
    debug = (_dbg == '1') if _dbg is not None else (os.getenv('FLASK_ENV') != 'production')
    app.run(debug=debug, use_reloader=debug, port=int(os.getenv('PORT', 5001)))
