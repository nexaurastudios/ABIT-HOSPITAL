import os
from app import create_app

# Create Flask application instance via the Application Factory
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1']
    print(f"Starting Hospital Analytics System on http://127.0.0.1:{port} ...")
    app.run(host='0.0.0.0', port=port, debug=debug)

