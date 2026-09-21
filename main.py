import csv
import datetime
import json
import os
import shutil
import sys

# ==========================
# FILE PATHS & CONSTANTS
# ==========================

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def find_data_file(filename):
    """Locate data file in APP_DIR, parent directory, or current working directory."""
    candidates = [
        os.path.join(APP_DIR, filename),
        os.path.join(os.path.dirname(APP_DIR), filename),
        os.path.join(os.getcwd(), filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return os.path.join(APP_DIR, filename)


BOOKS_FILE = find_data_file("books.json")
STUDENTS_FILE = find_data_file("students.json")
TRANSACTIONS_FILE = find_data_file("transactions.json")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

BORROW_PERIOD_DAYS = 7
DAILY_FINE_RATE = 5
MAX_BORROW_LIMIT = 3


# ==========================
# INPUT VALIDATION HELPERS
# ==========================

def get_non_empty_input(prompt):
    """Prompt user repeatedly until a non-empty string is provided."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Error: Input cannot be blank. Please try again.")


def get_integer(prompt, min_val=None, max_val=None, allow_blank=False, default=None):
    """Prompt user for a valid integer within optional min/max range."""
    while True:
        val_str = input(prompt).strip()
        if allow_blank and val_str == "":
            return default
        try:
            val = int(val_str)
            if min_val is not None and val < min_val:
                print(f"Error: Value must be at least {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"Error: Value must be at most {max_val}.")
                continue
            return val
        except ValueError:
            print("Error: Please enter a valid integer number.")


def get_yes_no(prompt, default_yes=False):
    """Prompt user for a yes/no response."""
    while True:
        try:
            ans = input(prompt).strip().lower()
        except (EOFError, StopIteration):
            return default_yes
        if not ans and default_yes:
            return True
        if ans in ["y", "yes"]:
            return True
        elif ans in ["n", "no"]:
            return False
        print("Please enter 'y' for yes or 'n' for no.")


def get_password_input(prompt="Password : "):
    """Get password input in a clean, portable way."""
    return input(prompt).strip()


# ==========================
# DATA MODELS
# ==========================

class Book:
    def __init__(self, book_id, title, author, category="General", isbn="", quantity=0, available_status=True):
        self.book_id = str(book_id).strip()
        self.title = str(title).strip()
        self.author = str(author).strip()
        self.category = str(category).strip() if str(category).strip() else "General"
        self.isbn = str(isbn).strip()
        self.quantity = max(0, int(quantity))
        self.available_status = bool(available_status) if self.quantity > 0 else False

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "isbn": self.isbn,
            "quantity": self.quantity,
            "available_status": self.available_status
        }

    @classmethod
    def from_dict(cls, data):
        quantity = int(data.get("quantity", 0))
        avail = data.get("available_status", quantity > 0)
        return cls(
            book_id=data.get("book_id", ""),
            title=data.get("title", ""),
            author=data.get("author", ""),
            category=data.get("category", "General"),
            isbn=data.get("isbn", ""),
            quantity=quantity,
            available_status=avail
        )


class Student:
    def __init__(self, student_id, name, password):
        self.student_id = str(student_id).strip()
        self.name = str(name).strip()
        self.password = str(password).strip()

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "name": self.name,
            "password": self.password
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            student_id=data.get("student_id", ""),
            name=data.get("name", ""),
            password=data.get("password", "")
        )


class Transaction:
    def __init__(self, transaction_id, student_id, book_id, borrow_date, due_date=None, return_date=None, status="Borrowed"):
        self.transaction_id = int(transaction_id)
        self.student_id = str(student_id).strip()
        self.book_id = str(book_id).strip()
        self.borrow_date = str(borrow_date).strip()
        self.status = str(status).strip()  # "Borrowed" or "Returned"
        self.return_date = str(return_date).strip() if return_date else None

        # Compute due_date if not provided
        if due_date:
            self.due_date = str(due_date).strip()
        else:
            try:
                b_dt = datetime.datetime.strptime(self.borrow_date, "%Y-%m-%d").date()
                self.due_date = (b_dt + datetime.timedelta(days=BORROW_PERIOD_DAYS)).strftime("%Y-%m-%d")
            except Exception:
                self.due_date = self.borrow_date

    def is_overdue(self, current_date=None):
        """Check if active borrowed transaction is past due date."""
        if self.status != "Borrowed":
            return False
        if not self.due_date:
            return False
        try:
            today_date = current_date or datetime.date.today()
            if isinstance(today_date, str):
                today_date = datetime.datetime.strptime(today_date, "%Y-%m-%d").date()
            due_dt = datetime.datetime.strptime(self.due_date, "%Y-%m-%d").date()
            return today_date > due_dt
        except Exception:
            return False

    def calculate_fine(self, current_date=None, daily_rate=DAILY_FINE_RATE):
        """Return (days_overdue, fine_amount)."""
        if not self.is_overdue(current_date):
            return 0, 0
        try:
            today_date = current_date or datetime.date.today()
            if isinstance(today_date, str):
                today_date = datetime.datetime.strptime(today_date, "%Y-%m-%d").date()
            due_dt = datetime.datetime.strptime(self.due_date, "%Y-%m-%d").date()
            days_overdue = (today_date - due_dt).days
            return days_overdue, max(0, days_overdue * daily_rate)
        except Exception:
            return 0, 0

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "student_id": self.student_id,
            "book_id": self.book_id,
            "borrow_date": self.borrow_date,
            "due_date": self.due_date,
            "return_date": self.return_date,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        borrow_d = str(data.get("borrow_date", "")).strip()
        due_d = data.get("due_date")
        if not due_d and borrow_d:
            try:
                b_dt = datetime.datetime.strptime(borrow_d, "%Y-%m-%d").date()
                due_d = (b_dt + datetime.timedelta(days=BORROW_PERIOD_DAYS)).strftime("%Y-%m-%d")
            except Exception:
                due_d = borrow_d

        return cls(
            transaction_id=data.get("transaction_id", 0),
            student_id=data.get("student_id", ""),
            book_id=data.get("book_id", ""),
            borrow_date=borrow_d,
            due_date=due_d,
            return_date=data.get("return_date"),
            status=data.get("status", "Borrowed")
        )


# ==========================
# DATABASE MANAGER
# ==========================

class DatabaseManager:

    def __init__(self, books_file=None, students_file=None, transactions_file=None):
        self.books_file = books_file or BOOKS_FILE
        self.students_file = students_file or STUDENTS_FILE
        self.transactions_file = transactions_file or TRANSACTIONS_FILE
        self.books = []
        self.students = []
        self.transactions = []
        self.load_data()

    def load_data(self):
        """Safely load books, students, and transactions from JSON files."""
        # Load Books
        if os.path.exists(self.books_file):
            try:
                with open(self.books_file, "r", encoding="utf-8") as f:
                    raw_books = json.load(f)
                    if isinstance(raw_books, list):
                        self.books = [
                            Book.from_dict(x) for x in raw_books
                            if isinstance(x, dict) and x.get("book_id")
                        ]
                    else:
                        self.books = []
            except Exception:
                self.books = []
        else:
            self.books = []

        # Load Students
        if os.path.exists(self.students_file):
            try:
                with open(self.students_file, "r", encoding="utf-8") as f:
                    raw_students = json.load(f)
                    if isinstance(raw_students, list):
                        self.students = [
                            Student.from_dict(x)
                            for x in raw_students
                            if isinstance(x, dict)
                            and str(x.get("student_id", "")).strip()
                            and str(x.get("name", "")).strip()
                        ]
                    else:
                        self.students = []
            except Exception:
                self.students = []
        else:
            self.students = []

        # Load Transactions
        if os.path.exists(self.transactions_file):
            try:
                with open(self.transactions_file, "r", encoding="utf-8") as f:
                    raw_transactions = json.load(f)
                    if isinstance(raw_transactions, list):
                        self.transactions = [
                            Transaction.from_dict(x)
                            for x in raw_transactions
                            if isinstance(x, dict) and x.get("transaction_id") is not None
                        ]
                    else:
                        self.transactions = []
            except Exception:
                self.transactions = []
        else:
            self.transactions = []

    def save_books(self):
        """Save books list to JSON file."""
        try:
            with open(self.books_file, "w", encoding="utf-8") as f:
                json.dump([b.to_dict() for b in self.books], f, indent=4)
        except Exception as e:
            print(f"Error saving books: {e}")

    def save_students(self):
        """Save students list to JSON file."""
        try:
            with open(self.students_file, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in self.students], f, indent=4)
        except Exception as e:
            print(f"Error saving students: {e}")

    def save_transactions(self):
        """Save transactions list to JSON file."""
        try:
            with open(self.transactions_file, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.transactions], f, indent=4)
        except Exception as e:
            print(f"Error saving transactions: {e}")

    def get_book(self, book_id):
        if not book_id:
            return None
        book_id_str = str(book_id).strip().lower()
        for book in self.books:
            if book.book_id.lower() == book_id_str:
                return book
        return None

    def get_student(self, student_id):
        if not student_id:
            return None
        student_id_str = str(student_id).strip().lower()
        for student in self.students:
            if student.student_id.lower() == student_id_str:
                return student
        return None

    def get_next_transaction_id(self):
        if not self.transactions:
            return 1
        return max(t.transaction_id for t in self.transactions) + 1

    def get_active_transaction(self, student_id, book_id):
        if not student_id or not book_id:
            return None
        s_id = str(student_id).strip().lower()
        b_id = str(book_id).strip().lower()
        for t in self.transactions:
            if t.student_id.lower() == s_id and t.book_id.lower() == b_id and t.status == "Borrowed":
                return t
        return None

    def get_student_transactions(self, student_id):
        if not student_id:
            return []
        s_id = str(student_id).strip().lower()
        return [t for t in self.transactions if t.student_id.lower() == s_id]

    def get_student_active_transactions(self, student_id):
        if not student_id:
            return []
        s_id = str(student_id).strip().lower()
        return [t for t in self.transactions if t.student_id.lower() == s_id and t.status == "Borrowed"]

    def has_active_borrowing_for_book(self, book_id):
        if not book_id:
            return False
        b_id = str(book_id).strip().lower()
        for t in self.transactions:
            if t.book_id.lower() == b_id and t.status == "Borrowed":
                return True
        return False

    def get_active_borrowed_count_for_book(self, book_id):
        if not book_id:
            return 0
        b_id = str(book_id).strip().lower()
        count = 0
        for t in self.transactions:
            if t.book_id.lower() == b_id and t.status == "Borrowed":
                count += 1
        return count

    def has_active_borrowing_for_student(self, student_id):
        if not student_id:
            return False
        s_id = str(student_id).strip().lower()
        for t in self.transactions:
            if t.student_id.lower() == s_id and t.status == "Borrowed":
                return True
        return False

    def delete_book(self, book_id):
        book = self.get_book(book_id)
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False

    def delete_student(self, student_id):
        student = self.get_student(student_id)
        if student:
            self.students.remove(student)
            self.save_students()
            return True
        return False

    def backup_data(self, target_dir=None):
        """Create backups of books.json, students.json, and transactions.json."""
        out_dir = target_dir or os.path.dirname(self.books_file)
        books_bak = os.path.join(out_dir, "books_backup.json")
        students_bak = os.path.join(out_dir, "students_backup.json")
        tx_bak = os.path.join(out_dir, "transactions_backup.json")

        try:
            with open(books_bak, "w", encoding="utf-8") as f:
                json.dump([b.to_dict() for b in self.books], f, indent=4)
            with open(students_bak, "w", encoding="utf-8") as f:
                json.dump([s.to_dict() for s in self.students], f, indent=4)
            with open(tx_bak, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.transactions], f, indent=4)
            return True, [books_bak, students_bak, tx_bak]
        except Exception as e:
            return False, str(e)

    def restore_data(self, target_dir=None):
        """Restore database from backup files if they exist."""
        in_dir = target_dir or os.path.dirname(self.books_file)
        books_bak = os.path.join(in_dir, "books_backup.json")
        students_bak = os.path.join(in_dir, "students_backup.json")
        tx_bak = os.path.join(in_dir, "transactions_backup.json")

        if not (os.path.exists(books_bak) or os.path.exists(students_bak) or os.path.exists(tx_bak)):
            return False, "No backup files found."

        try:
            if os.path.exists(books_bak):
                shutil.copyfile(books_bak, self.books_file)
            if os.path.exists(students_bak):
                shutil.copyfile(students_bak, self.students_file)
            if os.path.exists(tx_bak):
                shutil.copyfile(tx_bak, self.transactions_file)

            self.load_data()
            return True, "Backup restored successfully."
        except Exception as e:
            return False, f"Restore failed: {e}"

    def export_transactions_csv(self, output_path=None):
        """Export all transactions to a CSV file."""
        csv_file = output_path or os.path.join(os.path.dirname(self.transactions_file), "transactions.csv")
        try:
            with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Transaction ID",
                    "Student ID",
                    "Book ID",
                    "Borrow Date",
                    "Due Date",
                    "Return Date",
                    "Status"
                ])
                for t in self.transactions:
                    writer.writerow([
                        t.transaction_id,
                        t.student_id,
                        t.book_id,
                        t.borrow_date,
                        t.due_date or "-",
                        t.return_date or "-",
                        t.status
                    ])
            return True, csv_file
        except Exception as e:
            return False, str(e)


# ==========================
# LIBRARY SERVICE
# ==========================

class LibraryService:

    def __init__(self, db):
        self.db = db

    # ----------------------
    # BOOK OPERATIONS
    # ----------------------

    def add_book(self):
        print("\n===== ADD BOOK =====")

        book_id = input("Book ID : ").strip()
        if not book_id:
            print("Book ID cannot be empty.")
            return

        if self.db.get_book(book_id):
            print("Book ID already exists.")
            return

        title = input("Title : ").strip()
        if not title:
            print("Title cannot be empty.")
            return

        author = input("Author : ").strip()
        if not author:
            print("Author cannot be empty.")
            return

        category = input("Category : ").strip()
        if not category:
            category = "General"

        isbn = input("ISBN : ").strip()

        while True:
            try:
                quantity = int(input("Quantity : "))
                if quantity < 0:
                    raise ValueError
                break
            except ValueError:
                print("Enter a valid non-negative quantity.")

        new_book = Book(
            book_id,
            title,
            author,
            category,
            isbn,
            quantity,
            quantity > 0
        )

        self.db.books.append(new_book)
        self.db.save_books()

        print("\nBook added successfully.")

    def update_book(self):
        print("\n===== UPDATE BOOK =====")

        book_id = input("Enter Book ID to update : ").strip()
        book = self.db.get_book(book_id)

        if not book:
            print("Book not found.")
            return

        print("\n--- Current Details ---")
        print(f"Title    : {book.title}")
        print(f"Author   : {book.author}")
        print(f"Category : {book.category}")
        print(f"ISBN     : {book.isbn}")
        print(f"Quantity : {book.quantity}")

        active_borrowed = self.db.get_active_borrowed_count_for_book(book.book_id)
        if active_borrowed > 0:
            print(f"(Note: {active_borrowed} copies are currently borrowed)")

        print("\n(Press Enter to keep current value)")

        new_title = input(f"New Title [{book.title}]: ").strip()
        new_author = input(f"New Author [{book.author}]: ").strip()
        new_category = input(f"New Category [{book.category}]: ").strip()
        new_isbn = input(f"New ISBN [{book.isbn}]: ").strip()
        new_qty_str = input(f"New Quantity [{book.quantity}]: ").strip()

        if new_title:
            book.title = new_title
        if new_author:
            book.author = new_author
        if new_category:
            book.category = new_category
        if new_isbn:
            book.isbn = new_isbn

        if new_qty_str:
            try:
                new_quantity = int(new_qty_str)
                if new_quantity < 0:
                    print("Quantity cannot be negative. Quantity not updated.")
                elif new_quantity < active_borrowed:
                    print(f"Error: Total copies cannot be less than currently borrowed copies ({active_borrowed}). Quantity not updated.")
                else:
                    book.quantity = new_quantity
            except ValueError:
                print("Invalid quantity entered. Quantity not updated.")

        book.available_status = book.quantity > 0

        self.db.save_books()
        print("\nBook updated successfully.")

    def delete_book(self):
        print("\n===== DELETE BOOK =====")

        book_id = input("Enter Book ID to delete : ").strip()
        book = self.db.get_book(book_id)

        if not book:
            print("Book not found.")
            return

        if self.db.has_active_borrowing_for_book(book.book_id):
            print("\nError: Cannot delete book. This book currently has active borrowing record(s).")
            return

        confirm = input(f"Are you sure you want to delete '{book.title}' (ID: {book.book_id})? (y/n): ").strip().lower()
        if confirm in ["y", "yes"]:
            self.db.delete_book(book.book_id)
            print("\nBook deleted successfully.")
        else:
            print("\nDeletion cancelled.")

    def view_books(self, books_to_display=None, sort_by=None):
        """Display books in a formatted table with optional sorting."""
        book_list = list(books_to_display) if books_to_display is not None else list(self.db.books)

        print("\n=========== BOOK LIST ===========")
        if len(book_list) == 0:
            print("No books available.")
            return

        # Apply sorting if requested
        if sort_by == "title" or sort_by == "2":
            book_list = sorted(book_list, key=lambda b: b.title.lower())
        elif sort_by == "author" or sort_by == "3":
            book_list = sorted(book_list, key=lambda b: b.author.lower())
        elif sort_by == "category" or sort_by == "4":
            book_list = sorted(book_list, key=lambda b: b.category.lower())
        elif sort_by == "availability" or sort_by == "5":
            book_list = sorted(book_list, key=lambda b: b.quantity, reverse=True)

        print("-" * 105)
        print(
            f"{'ID':<10}"
            f"{'TITLE':<30}"
            f"{'AUTHOR':<22}"
            f"{'CATEGORY':<18}"
            f"{'QTY':<8}"
            f"{'STATUS'}"
        )
        print("-" * 105)

        for book in book_list:
            status = "Available" if book.quantity > 0 else "Unavailable"
            print(
                f"{book.book_id:<10}"
                f"{book.title[:28]:<30}"
                f"{book.author[:20]:<22}"
                f"{book.category[:16]:<18}"
                f"{book.quantity:<8}"
                f"{status}"
            )

        print("-" * 105)

    def search_book(self):
        """Search books by ID, Title, Author, Category, or ISBN with clean tabular output."""
        keyword = input("\nEnter Book ID / Title / Author / Category / ISBN : ").strip().lower()

        if not keyword:
            print("Please enter a valid search term.")
            return

        results = [
            b for b in self.db.books
            if (
                keyword in b.book_id.lower()
                or keyword in b.title.lower()
                or keyword in b.author.lower()
                or keyword in b.category.lower()
                or keyword in b.isbn.lower()
            )
        ]

        print("\n========== SEARCH RESULTS ==========")
        if not results:
            print("No matching books found.")
            return

        print("-" * 105)
        print(
            f"{'ID':<10}"
            f"{'TITLE':<30}"
            f"{'AUTHOR':<22}"
            f"{'CATEGORY':<18}"
            f"{'QTY':<8}"
            f"{'STATUS'}"
        )
        print("-" * 105)
        for book in results:
            status = "Available" if book.quantity > 0 else "Unavailable"
            print(
                f"{book.book_id:<10}"
                f"{book.title[:28]:<30}"
                f"{book.author[:20]:<22}"
                f"{book.category[:16]:<18}"
                f"{book.quantity:<8}"
                f"{status}"
            )
        print("-" * 105)

    def browse_books_by_category(self):
        """Browse and filter books by category."""
        print("\n===== BROWSE BOOKS BY CATEGORY =====")
        categories = sorted(list({b.category for b in self.db.books if b.category}))
        if not categories:
            print("No book categories available.")
            return

        for idx, cat in enumerate(categories, 1):
            count = sum(1 for b in self.db.books if b.category.lower() == cat.lower())
            print(f"{idx}. {cat} ({count} titles)")

        choice = input(f"\nSelect category (1-{len(categories)}): ").strip()
        try:
            cat_idx = int(choice) - 1
            if 0 <= cat_idx < len(categories):
                selected_cat = categories[cat_idx]
                matched_books = [b for b in self.db.books if b.category.lower() == selected_cat.lower()]
                print(f"\n--- Books in Category: {selected_cat} ---")
                self.view_books(matched_books)
            else:
                print("Invalid category choice.")
        except ValueError:
            print("Please enter a valid number.")

    def view_book_details(self):
        """Display full information card for a specific book."""
        print("\n===== BOOK DETAILS =====")
        book_id = input("Enter Book ID : ").strip()
        book = self.db.get_book(book_id)
        if not book:
            print("Book not found.")
            return

        active_borrowed = self.db.get_active_borrowed_count_for_book(book.book_id)
        status = "Available" if book.quantity > 0 else "Unavailable"

        print("\n" + "-" * 35)
        print(f"Book ID        : {book.book_id}")
        print(f"Title          : {book.title}")
        print(f"Author         : {book.author}")
        print(f"Category       : {book.category}")
        print(f"ISBN           : {book.isbn}")
        print(f"Total Copies   : {book.quantity + active_borrowed}")
        print(f"Available      : {book.quantity}")
        print(f"Borrowed       : {active_borrowed}")
        print(f"Status         : {status}")
        print("-" * 35)

    # ----------------------
    # STUDENT OPERATIONS
    # ----------------------

    def register_student(self):
        print("\n===== STUDENT REGISTRATION =====")

        student_id = input("Student ID : ").strip()
        if not student_id:
            print("Student ID cannot be empty.")
            return

        if self.db.get_student(student_id):
            print("Student ID already exists.")
            return

        name = input("Student Name : ").strip()
        if not name:
            print("Name cannot be empty.")
            return

        password = input("Password : ").strip()
        if not password:
            print("Password cannot be empty.")
            return

        student = Student(
            student_id,
            name,
            password
        )

        self.db.students.append(student)
        self.db.save_students()

        print("\nStudent registered successfully.")

    def view_students(self):
        print("\n========== STUDENTS ==========")

        if len(self.db.students) == 0:
            print("No students registered.")
            return

        print("-" * 65)
        print(f"{'ID':<15}{'NAME':<30}{'ACTIVE BORROWINGS'}")
        print("-" * 65)

        for student in self.db.students:
            active_count = len(self.db.get_student_active_transactions(student.student_id))
            print(f"{student.student_id:<15}{student.name[:28]:<30}{active_count}")

        print("-" * 65)

    def delete_student(self):
        print("\n===== DELETE STUDENT =====")

        student_id = input("Enter Student ID to delete : ").strip()
        student = self.db.get_student(student_id)

        if not student:
            print("Student not found.")
            return

        if self.db.has_active_borrowing_for_student(student.student_id):
            print("\nError: Cannot delete student. This student currently has active borrowed book(s) that must be returned first.")
            return

        confirm = input(f"Are you sure you want to delete student '{student.name}' (ID: {student.student_id})? (y/n): ").strip().lower()
        if confirm in ["y", "yes"]:
            self.db.delete_student(student.student_id)
            print("\nStudent deleted successfully.")
        else:
            print("\nDeletion cancelled.")

    # ----------------------
    # BORROW & RETURN OPERATIONS
    # ----------------------

    def borrow_book(self, student):
        print("\n===== BORROW BOOK =====")

        # Enforce max 3 books limit
        student_active = self.db.get_student_active_transactions(student.student_id)
        if len(student_active) >= MAX_BORROW_LIMIT:
            print(f"\nCannot borrow: Maximum limit of {MAX_BORROW_LIMIT} borrowed books reached.")
            print("Please return an existing book before borrowing a new one.")
            return

        book_id = input("Enter Book ID to borrow : ").strip()
        if not book_id:
            print("Book ID cannot be empty.")
            return

        book = self.db.get_book(book_id)
        if not book:
            print("Book not found.")
            return

        if book.quantity <= 0:
            print("Cannot borrow: No copies of this book are currently available.")
            return

        active_tx = self.db.get_active_transaction(student.student_id, book.book_id)
        if active_tx:
            print("Cannot borrow: You already have an active borrowing record for this book. Please return it first.")
            return

        book.quantity -= 1
        book.available_status = book.quantity > 0

        transaction_id = self.db.get_next_transaction_id()
        today = datetime.date.today()
        today_str = today.strftime("%Y-%m-%d")
        due_str = (today + datetime.timedelta(days=BORROW_PERIOD_DAYS)).strftime("%Y-%m-%d")

        new_transaction = Transaction(
            transaction_id=transaction_id,
            student_id=student.student_id,
            book_id=book.book_id,
            borrow_date=today_str,
            due_date=due_str,
            return_date=None,
            status="Borrowed"
        )

        self.db.transactions.append(new_transaction)
        self.db.save_books()
        self.db.save_transactions()

        print(f"\nSuccess: You have successfully borrowed '{book.title}'.")
        print(f"Transaction ID: {transaction_id} | Borrow Date: {today_str} | Due Date: {due_str}")

    def return_book(self, student):
        print("\n===== RETURN BOOK =====")

        active_txs = self.db.get_student_active_transactions(student.student_id)
        if not active_txs:
            print("You do not have any currently borrowed books to return.")
            return

        print("\n--- Currently Borrowed Books ---")
        print("-" * 90)
        print(f"{'TX ID':<8}{'BOOK ID':<12}{'TITLE':<28}{'BORROW DATE':<14}{'DUE DATE':<14}{'STATUS'}")
        print("-" * 90)
        for tx in active_txs:
            b = self.db.get_book(tx.book_id)
            title = b.title if b else "Unknown"
            status_display = "OVERDUE" if tx.is_overdue() else "Borrowed"
            print(f"{tx.transaction_id:<8}{tx.book_id:<12}{title[:26]:<28}{tx.borrow_date:<14}{tx.due_date:<14}{status_display}")
        print("-" * 90)

        book_id = input("\nEnter Book ID to return : ").strip()
        if not book_id:
            print("Book ID cannot be empty.")
            return

        active_tx = self.db.get_active_transaction(student.student_id, book_id)
        if not active_tx:
            print("Error: You do not have an active borrowing record for this Book ID.")
            return

        book = self.db.get_book(active_tx.book_id)
        book_title = book.title if book else active_tx.book_id
        today = datetime.date.today().strftime("%Y-%m-%d")
        days_overdue, fine = active_tx.calculate_fine()

        print("\n--- Return Confirmation Summary ---")
        print(f"Book       : {book_title}")
        print(f"Borrowed   : {active_tx.borrow_date}")
        print(f"Due        : {active_tx.due_date}")
        print(f"Today      : {today}")

        if active_tx.is_overdue():
            print(f"Status     : OVERDUE ({days_overdue} days late)")
            print(f"Fine Due   : ₹{fine} (at ₹{DAILY_FINE_RATE}/day)")
        else:
            print("Status     : On Time (No fine)")

        # Safe confirmation with default 'y' if mock/unattended
        try:
            confirm = input("\nConfirm return? (y/n): ").strip().lower()
            if not confirm:
                confirm = "y"
        except (EOFError, StopIteration):
            confirm = "y"

        if confirm not in ["y", "yes"]:
            print("\nReturn cancelled.")
            return

        active_tx.status = "Returned"
        active_tx.return_date = today

        if book:
            book.quantity += 1
            book.available_status = True
            self.db.save_books()

        self.db.save_transactions()

        print(f"\nSuccess: Book '{book_title}' has been returned successfully on {today}.")
        if fine > 0:
            print(f"Please ensure overdue fine of ₹{fine} is settled with the librarian.")

    def view_student_borrowed_books(self, student):
        print(f"\n=========== MY BORROWED BOOKS ({student.name}) ===========")

        student_txs = self.db.get_student_transactions(student.student_id)
        if not student_txs:
            print("No borrowing history found.")
            return

        print("-" * 105)
        print(
            f"{'TX ID':<8}"
            f"{'BOOK ID':<10}"
            f"{'TITLE':<26}"
            f"{'BORROW DATE':<13}"
            f"{'DUE DATE':<13}"
            f"{'RETURN DATE':<13}"
            f"{'STATUS'}"
        )
        print("-" * 105)

        for tx in student_txs:
            book = self.db.get_book(tx.book_id)
            title = book.title if book else "Unknown / Deleted"
            ret_date = tx.return_date if tx.return_date else "-"
            due_d = tx.due_date if tx.due_date else "-"

            status_display = tx.status
            if tx.status == "Borrowed" and tx.is_overdue():
                status_display = "OVERDUE"

            print(
                f"{tx.transaction_id:<8}"
                f"{tx.book_id:<10}"
                f"{title[:24]:<26}"
                f"{tx.borrow_date:<13}"
                f"{due_d:<13}"
                f"{ret_date:<13}"
                f"{status_display}"
            )

        print("-" * 105)

    def change_student_password(self, student):
        print("\n===== CHANGE PASSWORD =====")

        current_pw = get_password_input("Current Password : ")
        if current_pw != student.password:
            print("\nError: Incorrect current password.")
            return

        new_pw = get_password_input("New Password : ")
        if not new_pw:
            print("\nError: Password cannot be empty.")
            return

        confirm_pw = get_password_input("Confirm New Password : ")
        if new_pw != confirm_pw:
            print("\nError: New password and confirm password do not match.")
            return

        student.password = new_pw
        self.db.save_students()

        print("\nSuccess: Password changed successfully.")

    def show_student_profile(self, student):
        """Display student profile and summary."""
        print("\n=========================================")
        print(f"          MY PROFILE ({student.name})")
        print("=========================================")

        txs = self.db.get_student_transactions(student.student_id)
        active_txs = [t for t in txs if t.status == "Borrowed"]
        returned_txs = [t for t in txs if t.status == "Returned"]
        overdue_txs = [t for t in active_txs if t.is_overdue()]

        print(f"Student ID             : {student.student_id}")
        print(f"Full Name              : {student.name}")
        print(f"Currently Borrowed     : {len(active_txs)} (Max limit: {MAX_BORROW_LIMIT})")
        print(f"Total Books Borrowed   : {len(txs)}")
        print(f"Total Books Returned   : {len(returned_txs)}")
        print(f"Overdue Books          : {len(overdue_txs)}")
        print("=========================================")

        choice = input("\nWould you like to change your password? (y/n): ").strip().lower()
        if choice in ["y", "yes"]:
            self.change_student_password(student)

    def show_student_dashboard(self, student):
        """Display brief student summary banner upon login."""
        txs = self.db.get_student_transactions(student.student_id)
        active_txs = [t for t in txs if t.status == "Borrowed"]
        returned_txs = [t for t in txs if t.status == "Returned"]
        overdue_txs = [t for t in active_txs if t.is_overdue()]

        latest_title = "None"
        if txs:
            last_tx = txs[-1]
            b = self.db.get_book(last_tx.book_id)
            latest_title = b.title if b else last_tx.book_id

        print("\n" + "=" * 45)
        print(f"WELCOME, {student.name.upper()}")
        print("=" * 45)
        print(f"Currently Borrowed : {len(active_txs)}")
        print(f"Books Returned     : {len(returned_txs)}")
        print(f"Total Borrowings   : {len(txs)}")
        print(f"Overdue Books      : {len(overdue_txs)}")
        print("\nLatest Book:")
        print(f"{latest_title}")
        print("=" * 45)

    # ----------------------
    # ADMIN DASHBOARD & REPORTS
    # ----------------------

    def show_admin_dashboard(self):
        """Display high-level library analytics and KPIs."""
        print("\n-------------------------------------------")
        print("            LIBRARY DASHBOARD")
        print("-------------------------------------------")

        total_titles = len(self.db.books)
        available_copies = sum(b.quantity for b in self.db.books)
        borrowed_copies = sum(1 for t in self.db.transactions if t.status == "Borrowed")
        total_copies = available_copies + borrowed_copies
        total_students = len(self.db.students)
        total_transactions = len(self.db.transactions)

        # Most borrowed book
        book_counts = {}
        for t in self.db.transactions:
            book_counts[t.book_id] = book_counts.get(t.book_id, 0) + 1

        most_borrowed_book_str = "None"
        if book_counts:
            top_book_id = max(book_counts, key=book_counts.get)
            b = self.db.get_book(top_book_id)
            top_book_name = b.title if b else top_book_id
            most_borrowed_book_str = f"{top_book_name} ({book_counts[top_book_id]} times)"

        # Most active student
        student_counts = {}
        for t in self.db.transactions:
            student_counts[t.student_id] = student_counts.get(t.student_id, 0) + 1

        most_active_student_str = "None"
        if student_counts:
            top_student_id = max(student_counts, key=student_counts.get)
            stu = self.db.get_student(top_student_id)
            stu_name = stu.name if stu else top_student_id
            most_active_student_str = f"{top_student_id} - {stu_name} ({student_counts[top_student_id]} borrowings)"

        # Overdue count
        overdue_count = sum(1 for t in self.db.transactions if t.status == "Borrowed" and t.is_overdue())

        print(f"Total Books        : {total_titles}")
        print(f"Total Copies       : {total_copies}")
        print(f"Available Copies   : {available_copies}")
        print(f"Borrowed Copies    : {borrowed_copies}")
        print(f"Total Students     : {total_students}")
        print(f"Total Transactions : {total_transactions}")
        print(f"\nMost Borrowed Book : {most_borrowed_book_str}")
        print(f"Most Active Student: {most_active_student_str}")
        print(f"\nOverdue Books      : {overdue_count}")
        print("-------------------------------------------")

    def show_inventory_report(self):
        """Display library inventory details."""
        print("\n================= LIBRARY INVENTORY REPORT =================")
        total_titles = len(self.db.books)
        available_copies = sum(b.quantity for b in self.db.books)
        borrowed_copies = sum(1 for t in self.db.transactions if t.status == "Borrowed")
        total_copies = available_copies + borrowed_copies
        out_of_stock = [b for b in self.db.books if b.quantity == 0]

        print(f"Total Titles        : {total_titles}")
        print(f"Total Copies        : {total_copies}")
        print(f"Available Copies    : {available_copies}")
        print(f"Borrowed Copies     : {borrowed_copies}")
        print(f"Unavailable Titles  : {len(out_of_stock)}")

        if out_of_stock:
            print("\n--- Out of Stock Titles ---")
            for b in out_of_stock:
                print(f"- [{b.book_id}] {b.title} by {b.author}")
        print("============================================================")

    def view_all_transactions(self, transactions_to_show=None):
        """Display all transactions in a clear tabular format."""
        tx_list = transactions_to_show if transactions_to_show is not None else self.db.transactions

        print("\n========================= ALL TRANSACTIONS =========================")
        if not tx_list:
            print("No transactions recorded.")
            return

        print("-" * 115)
        print(
            f"{'TX ID':<8}"
            f"{'STUDENT':<16}"
            f"{'BOOK ID':<10}"
            f"{'TITLE':<24}"
            f"{'BORROW DATE':<13}"
            f"{'DUE DATE':<13}"
            f"{'RETURN DATE':<13}"
            f"{'STATUS'}"
        )
        print("-" * 115)

        for tx in tx_list:
            stu = self.db.get_student(tx.student_id)
            stu_info = f"{tx.student_id}" + (f" ({stu.name[:6]})" if stu else "")
            book = self.db.get_book(tx.book_id)
            book_title = book.title if book else "Unknown"
            ret_date = tx.return_date if tx.return_date else "-"
            due_d = tx.due_date if tx.due_date else "-"

            status_display = tx.status
            if tx.status == "Borrowed" and tx.is_overdue():
                status_display = "OVERDUE"

            print(
                f"{tx.transaction_id:<8}"
                f"{stu_info[:14]:<16}"
                f"{tx.book_id:<10}"
                f"{book_title[:22]:<24}"
                f"{tx.borrow_date:<13}"
                f"{due_d:<13}"
                f"{ret_date:<13}"
                f"{status_display}"
            )

        print("-" * 115)

    def search_transactions(self):
        """Search transactions by ID, Student ID, Book ID, or Status."""
        print("\n===== SEARCH TRANSACTIONS =====")
        print("1. Search by Transaction ID")
        print("2. Search by Student ID")
        print("3. Search by Book ID")
        print("4. Search by Status (Borrowed / Returned / Overdue)")
        print("5. Universal Keyword Search")

        choice = input("Enter choice (1-5): ").strip()
        keyword = input("Enter search term: ").strip().lower()

        if not keyword:
            print("Please enter a valid search term.")
            return

        results = []
        for tx in self.db.transactions:
            if choice == "1" and keyword in str(tx.transaction_id):
                results.append(tx)
            elif choice == "2" and keyword in tx.student_id.lower():
                results.append(tx)
            elif choice == "3" and keyword in tx.book_id.lower():
                results.append(tx)
            elif choice == "4":
                if keyword == "overdue" and tx.is_overdue():
                    results.append(tx)
                elif keyword in tx.status.lower():
                    results.append(tx)
            else:
                if (
                    keyword in str(tx.transaction_id)
                    or keyword in tx.student_id.lower()
                    or keyword in tx.book_id.lower()
                    or keyword in tx.status.lower()
                    or (keyword == "overdue" and tx.is_overdue())
                ):
                    results.append(tx)

        if not results:
            print("\nNo matching transactions found.")
        else:
            self.view_all_transactions(results)

    def show_borrowing_statistics(self):
        """Display transaction statistics for administrator."""
        print("\n===== BORROWING HISTORY STATISTICS =====")
        if not self.db.transactions:
            print("No transaction data available.")
            return

        total_tx = len(self.db.transactions)
        total_borrowed = sum(1 for t in self.db.transactions if t.status == "Borrowed")
        total_returned = sum(1 for t in self.db.transactions if t.status == "Returned")
        overdue_count = sum(1 for t in self.db.transactions if t.status == "Borrowed" and t.is_overdue())

        book_counts = {}
        student_counts = {}
        for t in self.db.transactions:
            book_counts[t.book_id] = book_counts.get(t.book_id, 0) + 1
            student_counts[t.student_id] = student_counts.get(t.student_id, 0) + 1

        top_book_id = max(book_counts, key=book_counts.get) if book_counts else "None"
        b = self.db.get_book(top_book_id)
        top_book_name = b.title if b else top_book_id

        top_student_id = max(student_counts, key=student_counts.get) if student_counts else "None"
        s = self.db.get_student(top_student_id)
        top_student_name = s.name if s else top_student_id

        print(f"Total Transactions : {total_tx}")
        print(f"Total Returns      : {total_returned}")
        print(f"Currently Borrowed : {total_borrowed}")
        print(f"Overdue Books      : {overdue_count}")
        print(f"Most Borrowed Book : {top_book_name} ({book_counts.get(top_book_id, 0)} times)")
        print(f"Most Active Student: {top_student_id} - {top_student_name} ({student_counts.get(top_student_id, 0)} borrowings)")
        print("========================================")

    def export_transactions(self):
        """Export transaction records to CSV."""
        print("\n===== EXPORT TRANSACTIONS =====")
        success, path_or_err = self.db.export_transactions_csv()
        if success:
            print(f"Transactions exported successfully to:\n{path_or_err}")
        else:
            print(f"Export failed: {path_or_err}")

    def backup_database(self):
        """Create a backup of the system data."""
        print("\n===== BACKUP DATA =====")
        success, files_or_err = self.db.backup_data()
        if success:
            print("Data backup completed successfully:")
            for fpath in files_or_err:
                print(f" - {os.path.basename(fpath)}")
        else:
            print(f"Backup failed: {files_or_err}")

    def restore_database(self):
        """Restore database from backup after user confirmation."""
        print("\n===== RESTORE DATA =====")
        print("Warning: Restoring backup will overwrite all current changes since last backup.")
        confirm = input("Are you sure you want to restore from backup? (y/n): ").strip().lower()
        if confirm in ["y", "yes"]:
            success, msg = self.db.restore_data()
            print(f"\n{msg}")
        else:
            print("\nRestore operation cancelled.")

    def show_library_rules(self):
        """Display library policies and borrowing rules."""
        print("\n==========================================")
        print("           LIBRARY RULES & POLICIES")
        print("==========================================")
        print(f"1. Maximum {MAX_BORROW_LIMIT} books can be borrowed at once per student.")
        print(f"2. Standard borrowing duration is {BORROW_PERIOD_DAYS} days.")
        print("3. Books must be returned on or before the specified due date.")
        print(f"4. Overdue returns are subject to a nominal fine of ₹{DAILY_FINE_RATE} per day.")
        print("5. Students cannot borrow multiple copies of the same book simultaneously.")
        print("6. Books must be kept in good physical condition.")
        print("==========================================")

    def show_about_system(self):
        """Display college project information."""
        print("\n==========================================")
        print("     SMART LIBRARY MANAGEMENT SYSTEM")
        print("==========================================")
        print("Version   : 1.0 (Polished College Edition)")
        print("Platform  : Python Terminal / CLI Application")
        print("Storage   : JSON File Persistence")
        print("\nCore Technologies & Concepts Used:")
        print(" * Object-Oriented Programming (Classes & Objects)")
        print(" * Clean Layered Architecture (Models, DB, Service, CLI)")
        print(" * File Handling & JSON Serialization")
        print(" * Transaction Tracking & Overdue Calculation")
        print(" * Searching, Sorting & Dynamic Filtering")
        print(" * Data Backup, Restore & CSV Export")
        print(" * Robust Input Validation & Error Handling")
        print("==========================================")


# ==========================
# USER INTERFACE (CLI)
# ==========================

class LibraryCLI:

    def __init__(self, db=None):
        self.db = db or DatabaseManager()
        self.service = LibraryService(self.db)

    # -------------------------
    # ADMIN LOGIN
    # -------------------------

    def admin_login(self):
        print("\n========== ADMIN LOGIN ==========")

        username = input("Username : ").strip()
        password = get_password_input("Password : ")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            print("\nLogin Successful!")
            self.admin_menu()
        else:
            print("\nInvalid Username or Password.")

    # -------------------------
    # STUDENT LOGIN
    # -------------------------

    def student_login(self):
        print("\n========== STUDENT LOGIN ==========")

        sid = input("Student ID : ").strip()
        password = get_password_input("Password : ")

        student = self.db.get_student(sid)

        if student is None:
            print("\nStudent not found.")
            return

        if student.password != password:
            print("\nIncorrect Password.")
            return

        # Show welcome summary dashboard
        self.service.show_student_dashboard(student)
        self.student_menu(student)

    # -------------------------
    # ADMIN MENU
    # -------------------------

    def admin_menu(self):
        while True:
            print("\n===================================")
            print("            ADMIN PANEL")
            print("===================================")
            print("1.  Add Book")
            print("2.  Update Book")
            print("3.  Delete Book")
            print("4.  View Books")
            print("5.  Search / Filter Books")
            print("6.  Register Student")
            print("7.  View Students")
            print("8.  Delete Student")
            print("9.  Library Dashboard")
            print("10. Transaction Management")
            print("11. Library Inventory Report")
            print("12. Export Transactions (CSV)")
            print("13. Backup / Restore Data")
            print("14. Logout")

            choice = input("\nEnter Choice : ").strip()

            if choice == "1":
                self.service.add_book()
            elif choice == "2":
                self.service.update_book()
            elif choice == "3":
                self.service.delete_book()
            elif choice == "4":
                self.view_books_with_sort()
            elif choice == "5":
                self.admin_book_search_menu()
            elif choice == "6":
                self.service.register_student()
            elif choice == "7":
                self.service.view_students()
            elif choice == "8":
                self.service.delete_student()
            elif choice == "9":
                self.service.show_admin_dashboard()
            elif choice == "10":
                self.admin_transaction_menu()
            elif choice == "11":
                self.service.show_inventory_report()
            elif choice == "12":
                self.service.export_transactions()
            elif choice == "13":
                self.admin_backup_menu()
            elif choice == "14":
                print("\nLogging Out...")
                break
            else:
                print("\nInvalid Choice. Please enter a number between 1 and 14.")

    def view_books_with_sort(self):
        """Prompt sort options and display books."""
        print("\nSort Options:")
        print("1. Default Order | 2. By Title | 3. By Author | 4. By Category | 5. By Availability")
        sort_choice = input("Select sort option (or press Enter for default): ").strip()
        self.service.view_books(sort_by=sort_choice)

    def admin_book_search_menu(self):
        """Submenu for searching and filtering books."""
        print("\n--- BOOK SEARCH & FILTER ---")
        print("1. Search Books (Keyword / Field)")
        print("2. Browse by Category")
        print("3. View Single Book Details")
        ch = input("Enter Choice (1-3): ").strip()
        if ch == "1":
            self.service.search_book()
        elif ch == "2":
            self.service.browse_books_by_category()
        elif ch == "3":
            self.service.view_book_details()
        else:
            print("Invalid choice.")

    def admin_transaction_menu(self):
        """Submenu for transaction operations."""
        while True:
            print("\n--- TRANSACTION MANAGEMENT ---")
            print("1. View All Transactions")
            print("2. Search Transactions")
            print("3. Transaction Statistics")
            print("4. Back to Admin Panel")
            ch = input("Enter Choice (1-4): ").strip()
            if ch == "1":
                self.service.view_all_transactions()
            elif ch == "2":
                self.service.search_transactions()
            elif ch == "3":
                self.service.show_borrowing_statistics()
            elif ch == "4":
                break
            else:
                print("Invalid Choice.")

    def admin_backup_menu(self):
        """Submenu for backup and restore operations."""
        print("\n--- DATA BACKUP & RESTORE ---")
        print("1. Backup Data")
        print("2. Restore Data from Backup")
        print("3. Back to Admin Panel")
        ch = input("Enter Choice (1-3): ").strip()
        if ch == "1":
            self.service.backup_database()
        elif ch == "2":
            self.service.restore_database()
        elif ch == "3":
            return
        else:
            print("Invalid Choice.")

    # -------------------------
    # STUDENT MENU
    # -------------------------

    def student_menu(self, student):
        while True:
            print("\n===================================")
            print(f"      STUDENT PANEL ({student.name})")
            print("===================================")
            print("1. View All Books")
            print("2. Search Books")
            print("3. Browse by Category")
            print("4. Borrow Book")
            print("5. Return Book")
            print("6. My Borrowed Books")
            print("7. My Profile")
            print("8. Change Password")
            print("9. Library Rules")
            print("10. Logout")

            choice = input("\nEnter Choice : ").strip()

            if choice == "1":
                self.view_books_with_sort()
            elif choice == "2":
                self.service.search_book()
            elif choice == "3":
                self.service.browse_books_by_category()
            elif choice == "4":
                self.service.borrow_book(student)
            elif choice == "5":
                self.service.return_book(student)
            elif choice == "6":
                self.service.view_student_borrowed_books(student)
            elif choice == "7":
                self.service.show_student_profile(student)
            elif choice == "8":
                self.service.change_student_password(student)
            elif choice == "9":
                self.service.show_library_rules()
            elif choice == "10":
                print("\nLogging Out...")
                break
            else:
                print("\nInvalid Choice. Please enter a number between 1 and 10.")

    # -------------------------
    # MAIN MENU
    # -------------------------

    def run(self):
        while True:
            print("\n===================================")
            print(" SMART LIBRARY MANAGEMENT SYSTEM ")
            print("===================================")
            print("1. Admin Login")
            print("2. Student Registration")
            print("3. Student Login")
            print("4. Library Rules")
            print("5. About System")
            print("6. Exit")

            choice = input("\nEnter Choice : ").strip()

            if choice == "1":
                self.admin_login()
            elif choice == "2":
                self.service.register_student()
            elif choice == "3":
                self.student_login()
            elif choice == "4":
                self.service.show_library_rules()
            elif choice == "5":
                self.service.show_about_system()
            elif choice == "6":
                print("\nThank you for using Library Management System.")
                break
            else:
                print("\nInvalid Choice.")


# ==========================
# UTILITY METHODS
# ==========================

def print_banner():
    print("=" * 50)
    print("      SMART LIBRARY MANAGEMENT SYSTEM")
    print("=" * 50)


def pause():
    input("\nPress Enter to continue...")


# ==========================
# APPLICATION ENTRY POINT
# ==========================

def main():
    print_banner()
    app = LibraryCLI()

    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user.")
    except Exception as e:
        print("\nUnexpected Error:", e)
    finally:
        print("\nThank you for using the system.")


if __name__ == "__main__":
    main()