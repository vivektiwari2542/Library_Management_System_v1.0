# 📚 Smart Library Management System (v2.0)

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Phase%201%20%26%202%20Complete-success?style=for-the-badge)](https://github.com/szeeshanZ123/Library_Management_System)
[![Storage](https://img.shields.io/badge/Storage-JSON%20Flat%20Files-orange?style=for-the-badge&logo=json&logoColor=white)](https://github.com/szeeshanZ123/Library_Management_System)
[![Architecture](https://img.shields.io/badge/Architecture-OOP%20%26%20Service%20Layer-blueviolet?style=for-the-badge)](https://github.com/szeeshanZ123/Library_Management_System)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen?style=for-the-badge)](https://github.com/szeeshanZ123/Library_Management_System)

A robust, modular, object-oriented **Library Management System** developed in Python. The application features dual-role authentication (Admin & Student), persistent JSON data storage, dynamic inventory tracking, and full lifecycle transaction logging for book borrowings and returns with rigorous data-integrity constraints.

---

ent System





A Python-based Library Management System built as a command-line application for managing books, students, and library transactions.

The project demonstrates practical use of Python programming, file handling, JSON data storage, authentication, CRUD operations, and library inventory management.

📑 Table of Contents

Overview

Key Features

Administrator Panel

Student Panel

Business Rules

Project Structure

Technologies Used

Installation

How to Run

Data Storage

Learning Objectives

Future Improvements

Author

🌟 Overview

The Library Management System is a simple CLI-based application designed to manage common library operations.

It provides separate access for Admin and Student users and stores application data in JSON files.

System Flow

                  📚 LIBRARY MANAGEMENT SYSTEM
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
          👨‍💼 ADMIN PANEL              🎓 STUDENT PANEL
                │                           │
        ┌───────┼────────┐          ┌───────┼────────┐
        │       │        │          │       │        │
        ▼       ▼        ▼          ▼       ▼        ▼
      Books  Students  Records    Search  Borrow   Return
        │       │        │          │       │        │
        └───────┴────────┴──────────┴───────┴────────┘
                              │
                              ▼
                       💾 JSON STORAGE

✨ Key Features

👨‍💼 Administrator Panel

The Admin section provides functionality for managing the library.

Feature

Description

📚 Add Book

Add new books to the library catalog

✏️ Update Book

Modify existing book information

🗑️ Delete Book

Remove books from the catalog

🔎 Search Books

Search books using available details

📖 View Books

View the library book catalog

👨‍🎓 Register Student

Create student accounts

👥 View Students

View registered students

🗑️ Delete Student

Remove student records

📋 Transactions

View library transaction records

🎓 Student Panel

Students can use the system to interact with the library catalog and manage their books.

Feature

Description

🔐 Student Login

Login using student credentials

📚 View Books

Browse books available in the library

🔎 Search Books

Find books in the catalog

📖 Borrow Book

Borrow an available book

🔄 Return Book

Return a previously borrowed book

📜 Borrow History

View borrowing-related information

🔑 Change Password

Update student login credentials

🛡️ Business Rules

The system applies basic validation rules to maintain consistent library records.

A book cannot be borrowed when its available quantity is 0.

Students should not borrow the same book multiple times simultaneously.

Book records should be maintained correctly when books are borrowed or returned.

Transaction records are updated when borrowing and returning operations take place.

Student records are managed through the Admin section.

📁 Project Structure

Library_Management_System_v1.0/
│
├── main.py
│
├── books.json
├── students.json
├── transactions.json
│
└── README.md

📄 File Description

main.py

Contains the main Python application, menus, authentication, library operations, and program logic.

books.json

Stores book-related information used by the application.

students.json

Stores registered student information.

transactions.json

Stores borrowing and returning transaction records.

README.md

Project documentation and setup instructions.

🛠️ Technologies Used

Technology

Purpose

🐍 Python

Application development

📄 JSON

Data storage

💻 Command Line Interface

User interaction

📂 File Handling

Reading and writing data

🔐 Authentication

Admin/Student access

🔄 CRUD Operations

Managing records

🚀 Installation

Prerequisites

Make sure you have:

Python installed on your computer

Git installed (if cloning the repository)

1. Clone the Repository

git clone https://github.com/vivektiwari2542/Library_Management_System_v1.0.git

2. Open the Project Directory

cd Library_Management_System_v1.0

▶️ How to Run

Run the following command:

python main.py

If your system uses python3:

python3 main.py

The application will start in the terminal/command prompt.

💾 Data Storage

This project uses JSON files for persistent data storage instead of a traditional database.

Books

books.json

Used to store book information and inventory-related data.

Students

students.json

Used to store registered student information.

Transactions

transactions.json

Used to maintain borrowing and returning records.

🔄 Library Workflow

📖 Borrowing a Book

Student Login
      ↓
View/Search Books
      ↓
Select Available Book
      ↓
Borrow Book
      ↓
Inventory Updated
      ↓
Transaction Recorded

🔄 Returning a Book

Student Login
      ↓
View Borrowed Books
      ↓
Select Book
      ↓
Return Book
      ↓
Inventory Updated
      ↓
Transaction Updated

🎯 Learning Objectives

This project helps demonstrate practical understanding of:

Python programming

Functions

Conditional statements

Loops

File handling

JSON handling

CRUD operations

User authentication

Input validation

Inventory management

Transaction management

Command-line application development

🔮 Future Improvements

The project can be extended with:

🗄️ MySQL or MongoDB database integration

🌐 Web-based interface

🎨 HTML/CSS/JavaScript frontend

📊 Admin dashboard

📈 Library statistics and reports

🔐 Password hashing

📧 Email notifications

🔔 Due-date reminders

☁️ Cloud deployment

📱 Mobile-friendly interface

📌 Project Status

Version: 1.0
Status: Learning / Academic Project
Language: Python
Storage: JSON
Interface: Command Line

👨‍💻 Author

Vivek Tiwari

B.Sc. Information Technology Student

GitHub: @vivektiwari2542

⭐ Support

If you find this project useful for learning Python and Library Management concepts, consider giving the repository a ⭐ on GitHub.

💡 Note: This project is developed for educational and learning purposes and can be further enhanced with a database, web interface, and additional security features.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
