# 👕 Custom Apparel Design

An end-to-end platform that allows users to create, preview, and purchase custom-designed apparel. Users can upload their own artwork or generate AI-powered designs, apply them to products like t-shirts, hoodies, or shirts, and place an order directly through the platform.

---

## 🚀 Features

- 🔐 User authentication and profile management
- 🖼️ Upload your own design (PNG/JPEG/SVG)
- 🧠 AI-generated custom designs (optional integration)
- 👕 Live product preview (t-shirt, hoodie, shirt)
- 🛒 Add to cart, checkout, and order confirmation
- 📬 Email-based password reset via OTP
- 🔧 Role-based permissions (admin/user)
- 📦 Order tracking and shipping information
- 🔄 Celery-based background tasks (e.g., sending emails)
- 🐳 Dockerized for easy setup and deployment

---

## 🛠️ Tech Stack

- **Backend:** Django, Django REST Framework (DRF)
- **Asynchronous Tasks:** Celery + Redis
- **Database:** PostgreSQL
- **Deployment:** Docker (optional)

---

## 📸 Screenshots

> _Coming Soon_: Demo images or GIFs of uploading a design, previewing on t-shirt, and placing order.

---

## 📦 Setup Instructions

### 🔧 Prerequisites

- Python 3.10+
- Docker & Docker Compose (if using containers)
- Redis (if using Celery)
- PostgreSQL (or SQLite for dev)

### 🐍 Local Installation

```bash
git clone https://github.com/ahmedshimmas/Custom-Apparel-Design.git
cd custom-apparel-design
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
