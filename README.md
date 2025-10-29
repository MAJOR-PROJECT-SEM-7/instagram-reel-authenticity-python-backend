# Instagram Reel Authenticity Checker

## Setup Instructions

After cloning the repository, follow these steps to set up the project:

### 1. Create Environment File
Create a `.env` file in the root directory with your Google Gemini API key:

```.env
GOOGLE_API_KEY="your gemini api key"
PERPLEXITY_KEY="your-perplexity-key"
```

### 2. Set Up Virtual Environment
Open Command Prompt or PowerShell and run:
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
**On Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**On Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:8000`

## Base URL

```
http://localhost:8000
```
