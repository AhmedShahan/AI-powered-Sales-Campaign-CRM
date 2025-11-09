# Quick Start Guide - Docker Compose

## 🚀 দ্রুত শুরু করার জন্য

### 1. Prerequisites Check
```bash
# Docker check
docker --version
docker compose version
```

### 2. Environment Setup
```bash
# .env file তৈরি করুন
cp env.example .env

# .env file edit করুন এবং API Key যোগ করুন
nano .env  # বা আপনার preferred editor ব্যবহার করুন
```

### 3. Run with Docker Compose
```bash
# সব services একসাথে চালু করুন
docker compose up

# বা background এ চালু করতে
docker compose up -d
```

### 4. Access Services

- **MailHog Web UI**: http://localhost:8025
- **Application Logs**: `docker compose logs -f app`

### 5. Stop Services
```bash
docker compose down
```

## 📁 Important Files

- `docker-compose.yml` - Main Docker Compose configuration
- `Dockerfile` - Python application container definition
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create from env.example)
- `wait-for-mailhog.sh` - Script to wait for MailHog to be ready

## 🔧 Common Commands

```bash
# Build containers
docker compose build

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f app
docker compose logs -f mailhog

# Restart services
docker compose restart

# Remove everything
docker compose down -v
```

## 📝 Notes

- Dataset files should be in `./dataset/` directory
- Output files will be in `./output/` directory
- Reports will be in `./report/` directory
- All these directories are mounted as volumes, so files persist on your host machine

