# FreeDomain - DigitalPlat
## DigitalPlat's Free Domain Registration Platform

FreeDomain is a professional web application that provides free domain registration services. The project aims to make internet presence accessible to everyone with a modern, user-friendly interface.

## Description

FreeDomain is a Flask-based web application that provides free domain registration services. The project aims to make internet presence accessible to everyone.

## Features

- **User Authentication**: Secure registration and login system
- **Domain Search**: Real-time domain availability checking with simulation
- **Shopping Cart**: Easy domain registration workflow
- **User Dashboard**: Manage your owned domains
- **Pricing Page**: Transparent pricing information
- **Modern UI**: Professional, responsive design
- **RESTful API**: Programmatic access to domain data

## Routes

| Route | Description |
|-------|-------------|
| `/` | Home page |
| `/domains` | Browse available domains |
| `/search` | Search for domain availability |
| `/pricing` | View pricing plans |
| `/cart` | View shopping cart |
| `/dashboard` | User dashboard (requires login) |
| `/register` | User registration |
| `/login` | User login |
| `/logout` | User logout |
| `/api/domains` | API endpoint (JSON) |

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser at: `http://localhost:5000`

## API Usage

Get all domains:
```bash
curl http://localhost:5000/api/domains
```

Search domain availability:
```bash
curl http://localhost:5000/api/search?domain=example
```

## Requirements

- Python 3.8+
- Flask 3.0.0
- Flask-Login 0.6.3
- Flask-SQLAlchemy 3.1.1

作者: stlin256的openclaw
