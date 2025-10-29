# Installation Docs

## ⚠️ Requirements

Before starting, make sure you have:

- 🐳 [Docker](https://www.docker.com/)
- 📦 [Docker Compose](https://docs.docker.com/compose/)
- 🧬 [Git](https://git-scm.com/)
- ⚡ High-speed internet (initial build downloads heavy models)
- 💾 At least **10–12 GB of free disk space** (Docker image \~8–10 GB)

---

## 📦 1. Clone the Repository

```bash
git clone https://github.com/MAJOR-PROJECT-SEM-7/instagram-reel-authenticity-python-backend.git
cd instagram-reel-authenticity-python-backend
```

---

## 🏗️ 2. Build the Docker Image

> This step can take **20–30 minutes** during the first build due to large model downloads and package installations.

```bash
docker build -t reel-auth-backend .
```

---

## 🔐 3. Create `.env` File

Create a `.env` file in the project root and add your Google Gemini API key:

```env
GOOGLE_API_KEY="your-gemini-api-key"
PERPLEXITY_KEY="your-perplexity-key"
```

---

## 🚀 4. Run the App

### ✅ Option 1: Using Docker Compose (Recommended)

> Automatically uses `.env` and sets up everything in one command:

```bash
docker compose -f docker-compose.dev.yml up
```

### 🛠️ Option 2: Manual Docker Command (Dev Mode with Reload)

If you prefer running manually with code reloading:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd):/app \
  -v $(pwd)/.env:/app/.env \
  reel-auth-backend \
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🌐 API Access

Once running, access the API at:

```
http://localhost:8000
```

Interactive API Docs:

```
http://localhost:8000/docs
```

---

## 🗂️ Project Structure

```
instagram-reel-authenticity-python-backend/
├── app/
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env  <-- (create manually)
```
