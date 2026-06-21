# 📡 Network Status Bot

A Telegram bot for monitoring network node availability across the Southern Region of JSC Transtelecom's infrastructure in Kazakhstan. Built during an industrial internship in the company's IT department.

## 🎯 About

The on-duty engineer can check network node status directly from their phone, without needing to access the main monitoring system via PC. The bot supports manual checks, automated monitoring with alerts, and keeps a full history of all checks in a database.

## ✨ Features

- 🗺 Check nodes by region and city (Shymkent, Turkestan, Maktaral, Tole Bi, Kentau)
- 🔍 Manually check any IP address or domain
- 📜 View recent check history
- 🔴 View recent offline incidents
- 🚨 Automated monitoring every 5 minutes with notifications when a node goes down or recovers
- 🌐 Three-language support: Russian, English, Kazakh
- 💾 Check history stored in PostgreSQL

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| Telegram Bot Framework | aiogram 3 |
| Database | PostgreSQL |
| ORM | SQLAlchemy (async) + asyncpg |
| Task Scheduler | APScheduler |
| Containerization | Docker |
| Hosting | Railway |

## 📁 Project Structure

```
├── backend/
│   ├── database.py      # database connection, PingLog model
│   └── queries.py       # database queries (history, offline cases)
├── bot/
│   ├── main.py            # entry point, all command and button handlers
│   ├── translations.py    # bot text in 3 languages
│   └── user_lang.py       # stores each user's selected language
├── monitor/
│   ├── checker.py         # ping logic and result logging
│   ├── hosts.py            # list of regions, cities, and IP addresses
│   └── scheduler.py        # automated periodic checks
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🚀 Running Locally

1. Clone the repository:
```bash
git clone https://github.com/Marzhan-b/TTC_Bot.git
cd TTC_Bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/network_monitor
```

4. Create a PostgreSQL database named `network_monitor`

5. Run the bot:
```bash
python bot/main.py
```

## 🐳 Running with Docker

```bash
docker build -t network-status-bot .
docker run --env-file .env network-status-bot
```

## 📊 Database

The `ping_logs` table stores every check:

| Field | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| region | String | Region name |
| city | String | City name |
| node_name | String | Node name |
| ip | String | Node IP address |
| is_online | Boolean | Whether the node is reachable |
| response_time | String | Response time (if online) |
| checked_at | DateTime | Check timestamp (UTC+5, Almaty) |

## 👤 Bot Commands

| Command | Description |
|---|---|
| `/start` | Main menu |
| `/setduty` | Register as on-duty to receive automatic notifications |

## 📝 Author

Marzhan Tulebayeva — internship at the IT department of JSC Transtelecom, 2026.