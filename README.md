# Control & Dispatch Engine (CDE)
<img src="https://github.com/bon4to/cde/assets/129971622/e1c1187c-e281-4f2b-8453-42cc4beb6c34" alt="git-cde-banner">


> A modular web-based application designed for inventory management, logistics coordination, and lightweight ERP functionalities.  

Originally conceived as a warehouse management tool, CDE evolved into a flexible system for managing operational workflows, dispatch routines, and department-level tasks.

---
 
## 📚 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Structure](#structure)
- [Contributing](#contributing)
- [License](#license)

---

## 🚀 Features

- Inventory registration, editing, and tracking
- Order dispatch and control routines
- Modular architecture for extensibility
- Templated user interface using Jinja2
- Internal API endpoints with Flask routing
- Access control (if implemented)
- Dashboard-style views for operational oversight

---

## 🧰 Tech Stack

- **Backend:** Python (Flask), JavaScript
- **Frontend:** Jinja2 templates (HTML + JS)
- **Database:** SQLite

---

## 🛠 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lucas-bonato/cde.git
   cd cde
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

   - On Mac/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python cde_wsgi.py
   ```

> ⚠️ **Important:** To perform ODBC-based queries to the ERP, the companion service [`cde-api`](https://github.com/lucas-bonato/cde-api) must be installed on the machine where the appropriate driver is available.

---

## 📁 Structure

```
/cde
 ├── /static           # CSS, JS, images
 ├── /templates        # Jinja2 templates (.j2 files)
 ├── /app              # Application logic
 ├── /db               # Database related files 
 ├── /tests            # Testing files 
 ├── /userdata         # Configuration files for users
 ├── cde.py            # Flask application logic
 ├── cde_wsgi.py       # WSGI entry point
 └── requirements.txt
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss the proposed modifications.  
Feel free to fork the repository and submit enhancements aligned with the project's scope and architecture.

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.