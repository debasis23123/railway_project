# 🚆 Railway Reservation System (Django Project)

## 📌 Overview

This is a **Railway Reservation System** built using **Django**.
The application allows users to book train tickets, view booking details, and manage reservations efficiently.

---

## 🚀 Features

* User Registration & Login
* Search Trains
* Book Tickets
* View Booking History
* Cancel Booking
* QR Code Generation for Tickets
* Admin Dashboard for managing bookings

---

## 🛠️ Tech Stack

* **Backend:** Django (Python)
* **Frontend:** HTML, CSS, Bootstrap
* **Database:** mysql
* **Other Tools:** Git, GitHub

---

## 📂 Project Structure

```
railway_project/
│
├── booking/
│   ├── migrations/
│   ├── templates/
│   ├── views.py
│   ├── models.py
│   ├── urls.py
│   └── qr_utils.py
│
├── railway_project/
│   ├── settings.py
│   ├── urls.py
│
├── mysql
├── manage.py
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/railway_project.git
cd railway_project
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5️⃣ Run the server

```bash
python manage.py runserver
```

### 6️⃣ Open in browser

```
http://127.0.0.1:8000/
```

---




---

## 📌 Future Improvements

* Payment Integration
* Live Train Status API
* Email Notifications
* Better UI/UX

---

## 👨‍💻 Author

**Debasis Samal**

GitHub: https://github.com/debasis23123

---

## 📄 License

This project is for educational purposes.
