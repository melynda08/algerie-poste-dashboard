# run.py
from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
