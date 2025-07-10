# Hostify Backend

Flask backend API for the Hostify guest ID verification system.

## Quick Setup

```bash
# Run the setup script
./setup-venv.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Running the Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Run the development server
python run.py
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
FIREBASE_ADMIN_SDK_JSON={"type": "service_account", ...}
```

## API Endpoints

- `GET /` - Health check
- `POST /upload-id` - Upload and process ID document
- `POST /generate-pdf` - Generate PDF police form
- `GET /guests` - Get user's guests
- `POST /guests` - Save guest data

## Dependencies

- Flask - Web framework
- Flask-CORS - Cross-origin resource sharing
- Pillow - Image processing
- pytesseract - OCR processing
- reportlab - PDF generation
- supabase - Database client
- firebase-admin - Authentication
- python-dotenv - Environment variables

## Development

```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install black pytest

# Format code
black .

# Run tests
pytest
``` 