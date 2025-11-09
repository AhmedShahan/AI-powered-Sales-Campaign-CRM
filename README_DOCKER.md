# Docker Setup Guide

এই প্রজেক্ট Docker Compose ব্যবহার করে চালানো যায়।

## Prerequisites

1. Docker এবং Docker Compose installed থাকতে হবে
2. Google Gemini API Key থাকতে হবে

## Setup

1. **Environment Variables তৈরি করুন:**
   ```bash
   cp env.example .env
   ```
   
2. **.env file এ আপনার API Key যোগ করুন:**
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ```
   
   **Note:** Docker Compose automatically sets `SMTP_HOST=mailhog` and `SMTP_PORT=1025` for the app service.

## Running the Application

### Docker Compose দিয়ে চালানো:

```bash
# নতুন version (Docker Compose V2)
docker compose up

# বা পুরানো version (Docker Compose V1)
docker-compose up
```

এটি MailHog এবং Python application দুটোই একসাথে চালু করবে。

### Background এ চালানো:

```bash
docker compose up -d
# বা
docker-compose up -d
```

### Logs দেখা:

```bash
docker compose logs -f app
# বা
docker-compose logs -f app
```

### Stop করা:

```bash
docker compose down
# বা
docker-compose down
```

## Services

1. **app**: Python application (sales campaign CRM workflow)
2. **mailhog**: Email testing service
   - SMTP: `localhost:1025`
   - Web UI: `http://localhost:8025`

## Volumes

নিম্নলিখিত directories host machine এ mount করা আছে:
- `./dataset` - Input CSV files
- `./output` - Generated output files
- `./report` - Final reports

## MailHog Web UI

Email গুলো দেখতে: http://localhost:8025

## Troubleshooting

### API Key error:
- `.env` file এ `GOOGLE_API_KEY` সঠিকভাবে set করা আছে কিনা check করুন

### MailHog connection error:
- MailHog service running আছে কিনা check করুন: `docker compose ps`
- Environment variables সঠিক আছে কিনা check করুন

### Port already in use:
- Port 1025 বা 8025 অন্য কোনো service use করছে কিনা check করুন
- `docker-compose.yml` এ ports change করতে পারেন

