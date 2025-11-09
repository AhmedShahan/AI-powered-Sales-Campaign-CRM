# Docker Setup Summary

## ✅ Created Files

1. **Dockerfile** - Python application container definition
2. **docker-compose.yml** - Main orchestration file with MailHog and App services
3. **requirements.txt** - Python dependencies
4. **.dockerignore** - Files to exclude from Docker build
5. **wait-for-mailhog.sh** - Script to wait for MailHog to be ready
6. **env.example** - Environment variables template
7. **README_DOCKER.md** - Detailed Docker setup guide
8. **QUICKSTART.md** - Quick start guide

## 🔧 Modified Files

1. **src/sendMailHog.py** - Updated to use environment variables for SMTP_HOST and SMTP_PORT

## 🚀 How to Use

### Step 1: Setup Environment
```bash
cp env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Step 2: Run with Docker Compose
```bash
docker compose up
# or
docker-compose up
```

### Step 3: Access Services
- MailHog Web UI: http://localhost:8025
- Application: Runs automatically and processes leads

## 📦 Services

1. **mailhog** - Email testing service (ports 1025, 8025)
2. **app** - Python sales campaign CRM workflow

## 📁 Volume Mounts

- `./dataset` → `/app/dataset` - Input CSV files
- `./output` → `/app/output` - Generated output files
- `./report` → `/app/report` - Final reports

## 🔑 Environment Variables

- `GOOGLE_API_KEY` - Required: Your Google Gemini API key
- `SMTP_HOST` - Auto-set to `mailhog` in Docker
- `SMTP_PORT` - Auto-set to `1025` in Docker

## ✨ Features

- ✅ Automatic MailHog startup
- ✅ Wait script ensures MailHog is ready before app starts
- ✅ Volume mounts for persistent data
- ✅ Network isolation
- ✅ Environment variable support
- ✅ Real-time logs

## 🐛 Troubleshooting

See README_DOCKER.md for detailed troubleshooting guide.

