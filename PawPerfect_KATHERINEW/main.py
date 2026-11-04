import calendar
import mysql.connector
import re
import tkinter as tk
from datetime import date as calendar_date, datetime
from decimal import Decimal, InvalidOperation
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Missing required dependency 'Pillow'. Install it with: pip install -r requirements.txt"
    ) from exc

from db_connect import init_db


class PawPerfectApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PawPerfect")
        self.root.geometry("1000x700")
        self.root.configure(bg="#FFF5EB")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.current_user = ""
        self.user_id = None
        self.user_role = "user"
        self.photo_images = []
        self.db = None
        self.appointments = []
        self.pets = []
        self.active_tab = "Upcoming"
        self.admin_appointment_filter = "All"
        self.admin_appointments_refresh_job = None

        if self.connect_db():
            self.show_login_page()
        else:
            self.root.destroy()

    def connect_db(self):
        try:
            self.db = init_db()
            return True
        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", f"Cannot connect:\n{error}")
            return False

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
        self.root.destroy()

    def clear_page(self):
        if self.admin_appointments_refresh_job is not None:
            try:
                self.root.after_cancel(self.admin_appointments_refresh_job)
            except tk.TclError:
                pass
            self.admin_appointments_refresh_job = None
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_sidebar(self, active_page):
        sidebar = tk.Frame(
            self.root, bg="#FBF4E9", width=190, padx=18, pady=18,
            highlightthickness=1, highlightbackground="#8A5A42",
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="🐾 PAW\nPERFECT",
            font=("Arial Black", 15, "bold"),
            fg="#4E3021", bg="#FBF4E9", justify="center",
        ).pack(pady=(0, 28))

        if self.user_role == "admin":
            pages = [
                ("Dashboard", self.show_admin_dashboard),
                ("Appointments", self.show_admin_appointments),
                ("Services", self.show_services),
                ("Settings", self.show_settings),
            ]
        else:
            pages = [
                ("Dashboard", self.show_dashboard),
                ("Appointments", self.show_appointments),
                ("My Pets", self.show_mypets),
                ("Services", self.show_services),
                ("Message", self.show_messages),
                ("Settings", self.show_settings),
            ]
        for label, command in pages:
            is_active = label == active_page
            tk.Button(
                sidebar,
                text=label,
                bg="#CDAF8A" if is_active else "#FFFFFF",
                fg="#4E3021",
                font=("Arial", 10, "bold" if is_active else "normal"),
                relief="solid",
                bd=1,
                padx=8,
                pady=7,
                command=command,
                cursor="hand2",
            ).pack(fill="x", pady=5)

        tk.Frame(sidebar, bg="#FBF4E9").pack(expand=True, fill="y")
        tk.Button(
            sidebar,
            text="Logout",
            bg="#4E3021",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=18,
            pady=7,
            command=self.logout,
        ).pack(side="bottom", fill="x")

    def create_input(self, parent, placeholder, show=None):
        password_row = None
        if show:
            password_row = tk.Frame(
                parent, bg="#FFFFFF", relief="solid", bd=1,
            )
            password_row.pack(pady=6)

        entry = tk.Entry(
            password_row or parent, font=("Arial", 10),
            width=31 if show else 35, bg="#FFFFFF", fg="#5C3A21",
            show=show, bd=0 if show else 1,
            highlightthickness=0 if show else 1,
        )
        entry.insert(0, placeholder)
        entry.bind(
            "<FocusIn>",
            lambda _: self._clear_placeholder(entry, placeholder, show),
        )
        entry.bind(
            "<FocusOut>",
            lambda _: self._restore_placeholder(entry, placeholder, show),
        )
        if show:
            entry.pack(side="left", padx=(5, 0), pady=4)
            visibility_button = tk.Button(
                password_row,
                text="👁",
                width=3,
                bg="#FFFFFF",
                fg="#8B5A2B",
                relief="flat",
                bd=0,
                activebackground="#FFFFFF",
                cursor="hand2",
                command=lambda: self.toggle_password_visibility(
                    entry, placeholder,
                ),
            )
            visibility_button.pack(side="right", padx=(0, 4), pady=2)
        else:
            entry.pack(pady=6)
        return entry

    @staticmethod
    def toggle_password_visibility(entry, placeholder):
        if entry.get() == placeholder:
            return

        if entry.cget("show"):
            entry.configure(show="")
        else:
            entry.configure(show="*")

    @staticmethod
    def _clear_placeholder(entry, placeholder, show):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            if show:
                entry.configure(show=show)

    @staticmethod
    def _restore_placeholder(entry, placeholder, show):
        if not entry.get():
            if show:
                entry.configure(show="")
            entry.insert(0, placeholder)

    def show_login_page(self):
        self.clear_page()
        self.root.configure(bg="#FBF4E9")
        panel = tk.Frame(
            self.root, bg="#FFFFFF", relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        panel.pack(expand=True, fill="both", padx=90, pady=70)

        brand = tk.Frame(
            panel, bg="#FBF4E9", width=330,
            highlightthickness=1, highlightbackground="#FFFFFF",
        )
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)
        tk.Label(
            brand, text="🐾", font=("Arial", 64),
            bg="#FBF4E9", fg="#4E3021",
        ).pack(pady=(100, 4))
        tk.Label(
            brand, text="PAW\nPERFECT",
            font=("Arial Black", 22, "bold"),
            fg="#4E3021", bg="#FBF4E9", justify="center",
        ).pack()
        tk.Label(
            brand, text="Pet Grooming Appointment System",
            font=("Arial", 11, "bold"),
            fg="#4E3021", bg="#FBF4E9",
        ).pack(pady=(12, 0))

        card = tk.Frame(
            panel, bg="#FFFFFF", padx=55, pady=35,
        )
        card.pack(side="right", fill="both", expand=True)
        tk.Label(
            card, text="Login", font=("Arial", 20, "bold"),
            fg="#4E3021", bg="#FFFFFF",
        ).pack(pady=(35, 18))

        self.login_email = self.create_input(card, "Username")
        self.login_password = self.create_input(card, "Password", show="*")
        tk.Button(
            card, text="Login", bg="#4E3021", fg="white",
            font=("Arial", 10, "bold"), padx=30, pady=8,
            relief="flat", cursor="hand2",
            command=self.handle_login,
        ).pack(fill="x", pady=12)
        tk.Label(
            card, text="Don't have an account?",
            fg="#6A5A50", bg="#FFFFFF", font=("Arial", 9),
        ).pack(pady=(18, 0))
        tk.Button(
            card, text="Sign up", bg="#FFFFFF", fg="#9A704F",
            font=("Arial", 9, "underline"), relief="flat",
            command=self.show_signup_page, cursor="hand2",
        ).pack()

    def show_signup_page(self):
        self.clear_page()
        card = tk.Frame(
            self.root, bg="#FFFFFF", padx=55, pady=30, relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        card.pack(expand=True)
        tk.Label(
            card, text="🐾 PAW PERFECT",
            font=("Arial Black", 12, "bold"), fg="#4E3021", bg="#FFFFFF",
        ).pack(pady=(0, 8))
        tk.Label(
            card, text="Create Account", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFFFFF",
        ).pack(pady=(0, 15))

        self.fullname_entry = self.create_input(card, "Full Name")
        self.email_entry = self.create_input(card, "Username")
        self.password_entry = self.create_input(card, "Password", show="*")
        tk.Button(
            card, text="Sign Up", bg="#4E3021", fg="white",
            font=("Arial", 10, "bold"), padx=30, pady=5,
            command=self.handle_signup,
        ).pack(pady=15)
        tk.Label(
            card, text="Already have an account?", fg="#6A5A50",
            bg="#FFFFFF", font=("Arial", 9),
        ).pack()
        tk.Button(
            card, text="Login", bg="#FFFFFF", fg="#9A704F",
            font=("Arial", 9, "underline"), relief="flat",
            command=self.show_login_page,
        ).pack()

    def handle_signup(self):
        fullname = self.fullname_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if (
            not fullname or fullname == "Full Name"
            or not email or email == "Email"
            or not password or password == "Password"
        ):
            messagebox.showwarning("Warning", "Please fill in all fields!")
            return
        if "@" not in email:
            messagebox.showwarning("Warning", "Please enter a valid email!")
            return
        if len(password) < 4:
            messagebox.showwarning(
                "Warning", "Password must be at least 4 characters!",
            )
            return

        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                "SELECT 1 FROM users WHERE email = %s", (email,),
            )
            existing_user = cursor.fetchone()
            if existing_user:
                cursor.close()
                messagebox.showwarning("Warning", "Email already registered!")
                return

            cursor.execute(
                """
                INSERT INTO users (fullname, email, password, phone)
                VALUES (%s, %s, %s, %s)
                """,
                (fullname, email, password, "N/A"),
            )
            self.db.commit()
        except mysql.connector.Error as error:
            self.db.rollback()
            messagebox.showerror("Error", f"Failed to save account:\n{error}")
            return

        self.user_id = cursor.lastrowid
        cursor.close()
        self.current_user = fullname
        self._load_sample_data()
        messagebox.showinfo("Success", f"Account created!\nWelcome, {fullname}!")
        self.show_dashboard()

    def handle_login(self):
        email = self.login_email.get().strip()
        password = self.login_password.get().strip()
        if email in ("", "Email") or password in ("", "Password"):
            messagebox.showwarning("Warning", "Please enter email and password!")
            return

        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, fullname, password, role FROM users WHERE email = %s",
                (email,),
            )
            user = cursor.fetchone()
            cursor.close()
        except mysql.connector.Error as error:
            messagebox.showerror("Error", f"Login failed:\n{error}")
            return

        if user is None or user["password"] != password:
            messagebox.showerror("Error", "Invalid email or password")
            return

        self.user_id = user["id"]
        self.current_user = user["fullname"]
        self.user_role = user.get("role", "user")
        self._load_sample_data()
        messagebox.showinfo("Success", f"Welcome, {self.current_user}!")
        if self.user_role == "admin":
            self.show_admin_dashboard()
        else:
            self.show_dashboard()

    def _load_sample_data(self):
        self.services = []
        self.service_catalog = {}
        self.pet_sizes = [
            "Small (1-5kg)", "Medium (6-10kg)", "Large (11-16kg)",
            "Extra Large (17kg+)",
        ]
        self.pets = []
        self.appointments = []

        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT name, description, small_price, medium_price, large_price
                FROM services ORDER BY name
                """
            )
            service_rows = cursor.fetchall()
            self.services = [row["name"] for row in service_rows]
            self.service_catalog = {
                row["name"]: {
                    "description": row["description"],
                    "Small": Decimal(row["small_price"]),
                    "Medium": Decimal(row["medium_price"]),
                    "Large": Decimal(row["large_price"]),
                }
                for row in service_rows
            }
            if self.user_role == "admin":
                cursor.execute(
                    "SELECT id, name, breed, gender, age, photo_path FROM pets ORDER BY id"
                )
            else:
                cursor.execute(
                    """
                    SELECT id, name, breed, gender, age, photo_path
                    FROM pets WHERE user_id=%s ORDER BY id
                    """,
                    (self.user_id,),
                )
            pet_rows = cursor.fetchall()

            self.pets = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "breed": row["breed"],
                    "gender": row["gender"],
                    "age": row["age"],
                    "photo_path": row["photo_path"],
                }
                for row in pet_rows
            ]

            if self.user_role == "admin":
                cursor.execute(
                    """
                    SELECT a.id, a.user_id, p.name AS pet_name, p.breed, p.gender, p.age,
                           a.service, a.pet_size, a.appointment_date,
                           a.appointment_time, a.status, a.price, a.payment_method,
                           p.photo_path, u.fullname AS client_name
                    FROM appointments a
                    JOIN pets p ON p.id=a.pet_id
                    JOIN users u ON u.id=a.user_id
                    ORDER BY a.created_at DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT a.id, a.user_id, p.name AS pet_name, p.breed, p.gender, p.age,
                           a.service, a.pet_size, a.appointment_date,
                           a.appointment_time, a.status, a.price, a.payment_method,
                           p.photo_path, u.fullname AS client_name
                    FROM appointments a
                    JOIN pets p ON p.id=a.pet_id
                    JOIN users u ON u.id=a.user_id
                    WHERE a.user_id=%s
                    ORDER BY a.created_at DESC
                    """,
                    (self.user_id,),
                )
            appointment_rows = cursor.fetchall()
            self.appointments = [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "client_name": row["client_name"],
                    "pet_name": row["pet_name"],
                    "breed": row["breed"],
                    "gender": row["gender"],
                    "age": row["age"],
                    "service": row["service"],
                    "pet_size": row["pet_size"],
                    "date": row["appointment_date"],
                    "time": row["appointment_time"],
                    "status": row["status"],
                    "price": row["price"],
                    "payment_method": row["payment_method"],
                    "photo_path": row["photo_path"],
                }
                for row in appointment_rows
            ]
            for appointment in self.appointments:
                if not appointment["price"] or appointment["price"] in ("P0.00", "₱0.00", "0"):
                    appointment["price"] = self.get_appointment_price(
                        appointment["service"], appointment["pet_size"],
                    )
                    cursor.execute(
                        "UPDATE appointments SET price=%s WHERE id=%s",
                        (appointment["price"], appointment["id"]),
                    )
            self.db.commit()
            cursor.close()
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Database Error", f"Unable to load PawPerfect data:\n{error}",
            )

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.current_user = ""
            self.user_id = None
            self.user_role = "user"
            self.appointments = []
            self.pets = []
            self.show_login_page()

    def stat_card(self, parent, icon, label, number):
        card = tk.Frame(
            parent, bg="#FFFFFF", relief="solid", bd=1, padx=20, pady=15,
        )
        card.pack(side="left", padx=10, fill="x", expand=True)
        tk.Label(
            card, text=icon, font=("Arial", 24), bg="#FFFFFF", fg="#8B5A2B",
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            card, text=label, font=("Arial", 9), fg="#5C3A21", bg="#FFFFFF",
        ).pack(anchor="n")
        tk.Label(
            card, text=str(number), font=("Arial", 24, "bold"),
            fg="#8B5A2B", bg="#FFFFFF",
        ).pack(anchor="w")

    def show_admin_dashboard(self):
        self.clear_page()
        self.create_sidebar("Dashboard")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text=f"Hello {self.current_user}!",
            font=("Arial", 16, "bold"), fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w")
        tk.Label(
            content, text="Here's what happening today!",
            font=("Arial", 9), fg="#777", bg="#FFF5EB",
        ).pack(anchor="w")

        stats_row = tk.Frame(content, bg="#FFF5EB")
        stats_row.pack(fill="x", pady=20)
        for label, number in (
            ("Upcoming\nAppointments", 14),
            ("Pending\nAppointments", 8),
            ("Confirmed\nAppointments", 10),
            ("Completed\nAppointments", 29),
        ):
            card = tk.Frame(
                stats_row, bg="#FFF5EB", padx=12, pady=12,
                relief="solid", bd=1,
                highlightthickness=1, highlightbackground="#9A704F",
            )
            card.pack(side="left", fill="x", expand=True, padx=6)
            tk.Label(
                card, text=label, font=("Arial", 8), bg="#FFF5EB",
                fg="#6A5A50",
            ).pack(side="left")
            tk.Label(
                card, text=str(number), font=("Arial", 24, "bold"),
                bg="#FFF5EB", fg="#4E3021",
            ).pack(side="right", padx=(5, 0))

        section = tk.Frame(
            content, bg="#FFF5EB", padx=15, pady=15,
            relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        section.pack(fill="both", expand=True)
        header = tk.Frame(section, bg="#FFF5EB")
        header.pack(fill="x", pady=(0, 10))
        tk.Label(
            header, text="Upcoming Appointments",
            font=("Arial", 12, "bold"), fg="#4E3021", bg="#FFF5EB",
        ).pack(side="left")
        tk.Button(
            header, text="View All", fg="#4E3021", bg="#FFF5EB",
            relief="flat", font=("Arial", 9, "underline"),
            command=self.show_admin_appointments,
        ).pack(side="right")

        for appointment in self.appointments[:3]:
            if appointment["status"] not in ("Pending", "Paid", "Confirmed"):
                continue
            row = tk.Frame(
                section, bg="#FFF5EB", padx=10, pady=10,
                relief="solid", bd=1,
            )
            row.pack(fill="x", pady=4)
            tk.Label(
                row, text=f"{appointment['pet_name']}\n{appointment['breed']}",
                font=("Arial", 8), fg="#6A5A50", bg="#FFF5EB",
                justify="left",
            ).pack(side="left", fill="x", expand=True)
            tk.Label(
                row, text=appointment["service"], font=("Arial", 9),
                fg="#4E3021", bg="#FFF5EB",
            ).pack(side="left", fill="x", expand=True)
            tk.Label(
                row,
                text=f"{appointment['date']}\n{appointment['time']}",
                font=("Arial", 8), fg="#777", bg="#FFF5EB",
                justify="center",
            ).pack(side="left", fill="x", expand=True)
            status = appointment["status"]
            status_color = "#F3B73A" if status == "Pending" else "#A6D7A3"
            tk.Label(
                row, text=status, bg=status_color, fg="#4E3021",
                font=("Arial", 8, "bold"), padx=10, pady=4,
            ).pack(side="right", padx=5)

    def show_admin_appointments(self):
        self.clear_page()
        self.create_sidebar("Appointments")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="Appointments",
            font=("Arial", 16, "bold"), fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w")

        self._load_sample_data()

        total_count = len(self.appointments)
        pending_count = sum(
            appointment["status"] == "Pending" for appointment in self.appointments
        )
        confirmed_count = sum(
            appointment["status"] in ("Confirmed", "Paid")
            for appointment in self.appointments
        )
        completed_count = sum(
            appointment["status"] == "Completed" for appointment in self.appointments
        )
        cancelled_count = sum(
            appointment["status"] == "Cancelled" for appointment in self.appointments
        )
        counts = {
            "All": total_count,
            "Pending": pending_count,
            "Confirmed": confirmed_count,
            "Completed": completed_count,
            "Cancelled": cancelled_count,
        }

        stats_row = tk.Frame(content, bg="#FFF5EB")
        stats_row.pack(fill="x", pady=20)
        for label, number in (
            ("Total Appointments", total_count),
            ("Pending", pending_count),
            ("Confirmed", confirmed_count),
            ("Completed", completed_count),
            ("Cancelled", cancelled_count),
        ):
            card = tk.Frame(
                stats_row, bg="#FFFFFF", padx=8, pady=10, relief="solid", bd=1,
                cursor="hand2",
            )
            card.pack(side="left", fill="x", expand=True, padx=5)
            filter_name = "All" if label == "Total Appointments" else label
            selected = self.admin_appointment_filter == filter_name
            card.configure(
                bg="#D8C3A5" if selected else "#FFFFFF",
                highlightthickness=1,
                highlightbackground="#8B5A2B" if selected else "#BBAA99",
            )
            label_widget = tk.Label(
                card, text=label, font=("Arial", 8), bg="#FFFFFF", fg="#777",
            )
            label_widget.configure(bg=card.cget("bg"))
            label_widget.pack()
            number_widget = tk.Label(
                card, text=str(counts[filter_name]),
                font=("Arial", 20, "bold"), bg="#FFFFFF", fg="#4E3021",
            )
            number_widget.configure(bg=card.cget("bg"))
            number_widget.pack()

            def select_filter(selected_filter=filter_name):
                self.admin_appointment_filter = selected_filter
                self.show_admin_appointments()

            card.bind("<Button-1>", lambda _event, fn=select_filter: fn())
            label_widget.bind("<Button-1>", lambda _event, fn=select_filter: fn())
            number_widget.bind("<Button-1>", lambda _event, fn=select_filter: fn())

        table = tk.Frame(
            content, bg="#FFF5EB", padx=10, pady=10,
            relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        table.pack(fill="both", expand=True)
        columns = ("Client Name", "Service", "Date & Time", "Status", "Action")
        widths = (180, 160, 150, 100, 80)
        header = tk.Frame(table, bg="#FFF5EB")
        header.pack(fill="x")
        for title, width in zip(columns, widths):
            tk.Label(
                header, text=title, width=width // 10, font=("Arial", 8, "bold"),
                fg="#4E3021", bg="#F4E9DD", anchor="w",
            ).pack(side="left", padx=3, pady=5)

        if self.admin_appointment_filter == "All":
            filtered_appointments = self.appointments
        elif self.admin_appointment_filter == "Confirmed":
            filtered_appointments = [
                appointment for appointment in self.appointments
                if appointment["status"] in ("Confirmed", "Paid")
            ]
        else:
            filtered_appointments = [
                appointment for appointment in self.appointments
                if appointment["status"] == self.admin_appointment_filter
            ]

        for appointment in filtered_appointments[:8]:
            row = tk.Frame(table, bg="#FFF5EB")
            row.pack(fill="x", pady=3)
            status = appointment["status"]
            values = (
                f"{appointment.get('client_name', 'Unknown')}\n"
                f"{appointment['pet_name']} ({appointment['breed']})",
                appointment["service"],
                f"{appointment['date']}\n{appointment['time']}",
            )
            for value, width in zip(values, widths[:3]):
                tk.Label(
                    row, text=value, width=width // 10, font=("Arial", 8),
                    fg="#4E3021", bg="#FFF5EB", anchor="w",
                ).pack(side="left", padx=3, pady=7)
            status_colors = {
                "Pending": "#F3B73A", "Confirmed": "#A6D7A3",
                "Paid": "#A6D7A3", "Completed": "#BBA0DD",
                "Cancelled": "#E99595",
            }
            tk.Label(
                row, text=status, bg=status_colors.get(status, "#CCCCCC"),
                fg="#4E3021", font=("Arial", 8, "bold"), width=12,
            ).pack(side="left", padx=3)
            tk.Button(
                row, text="View", bg="#9FB9E2", fg="#FFFFFF",
                relief="flat", font=("Arial", 8, "bold"), padx=8, pady=3,
                command=lambda appointment=appointment: self.update_appointment_status(appointment),
            ).pack(side="left", padx=3)

        def refresh_admin_appointments():
            if self.user_role != "admin":
                return
            if any(isinstance(widget, tk.Toplevel) for widget in self.root.winfo_children()):
                self.admin_appointments_refresh_job = self.root.after(
                    5000, refresh_admin_appointments
                )
                return
            self.show_admin_appointments()

        self.admin_appointments_refresh_job = self.root.after(
            5000, refresh_admin_appointments
        )

    def update_appointment_status(self, appointment):
        popup = tk.Toplevel(self.root)
        popup.title("Update Appointment Status")
        popup.geometry("360x230")
        popup.configure(bg="#FFF5EB")
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(
            popup, text=f"{appointment['pet_name']} - {appointment['service']}",
            font=("Arial", 10, "bold"), fg="#4E3021", bg="#FFF5EB",
        ).pack(pady=(20, 8))
        status_var = tk.StringVar(value=appointment["status"])
        ttk.Combobox(
            popup, textvariable=status_var,
            values=("Pending", "Confirmed", "Paid", "Completed", "Cancelled"),
            state="readonly", width=25,
        ).pack(pady=8, ipady=5)

        def save_status():
            new_status = status_var.get()
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "UPDATE appointments SET status=%s WHERE id=%s",
                    (new_status, appointment["id"]),
                )
                titles = {
                    "Confirmed": ("Accepted", "Appointment accepted",
                                  f"PawPerfect accepted your {appointment['service']} appointment."),
                    "Paid": ("Paid", "Payment confirmed",
                             f"Payment for your {appointment['service']} appointment was confirmed."),
                    "Completed": ("Completed", "Appointment completed",
                                  f"Your {appointment['service']} appointment has been completed."),
                    "Cancelled": ("Cancelled", "Appointment cancelled",
                                  f"Your {appointment['service']} appointment was cancelled."),
                }
                if new_status in titles:
                    notification_type, title, message = titles[new_status]
                    cursor.execute(
                        "SELECT id FROM notifications WHERE user_id=%s AND appointment_id=%s AND notification_type=%s LIMIT 1",
                        (appointment["user_id"], appointment["id"], notification_type),
                    )
                    if cursor.fetchone() is None:
                        cursor.execute(
                            """
                            INSERT INTO notifications
                                (user_id, appointment_id, notification_type, title, message)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                appointment["user_id"], appointment["id"],
                                notification_type, title, message,
                            ),
                        )
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror("Status Error", str(error))
                return
            appointment["status"] = new_status
            popup.destroy()
            self.show_admin_appointments()

        tk.Button(
            popup, text="Save Status", bg="#4E3021", fg="white",
            font=("Arial", 9, "bold"), relief="flat", padx=20, pady=7,
            command=save_status,
        ).pack(pady=18)

    def show_dashboard(self):
        self.clear_page()
        self.create_sidebar("Dashboard")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=30, pady=25)
        content.pack(side="right", fill="both", expand=True)

        top_bar = tk.Frame(content, bg="#FFF5EB")
        top_bar.pack(fill="x", pady=(0, 10))
        tk.Label(
            content, text=f"Welcome {self.current_user}!",
            font=("Arial", 16, "bold"), fg="#5C3A21", bg="#FFF5EB",
        ).pack(anchor="w")
        tk.Label(
            content, text="Book appointment now !", font=("Arial", 10),
            fg="#888", bg="#FFF5EB",
        ).pack(anchor="w", pady=(0, 25))

        stats_row = tk.Frame(content, bg="#FFF5EB")
        stats_row.pack(fill="x", pady=(0, 25))
        upcoming_count = sum(
            appointment["status"] in ("Pending", "Paid", "Confirmed")
            for appointment in self.appointments
        )
        completed_count = sum(
            appointment["status"] == "Completed"
            for appointment in self.appointments
        )
        self.stat_card(stats_row, "📅", "Upcoming\nAppointment", upcoming_count)
        self.stat_card(stats_row, "🐾", "My Pets", len(self.pets))
        self.stat_card(
            stats_row, "✔", "Completed\nAppointment", completed_count,
        )

        section = tk.Frame(
            content, bg="#FFF5EB", relief="solid", bd=1, padx=20, pady=20,
        )
        section.pack(fill="x")
        section_header = tk.Frame(section, bg="#FFF5EB")
        section_header.pack(fill="x", pady=(0, 15))
        tk.Label(
            section_header, text="Upcoming Appointment",
            font=("Arial", 13, "bold"), fg="#5C3A21", bg="#FFF5EB",
        ).pack(side="left")
        tk.Button(
            section_header, text="View All", bg="#FFF5EB", fg="#8B5A2B",
            relief="flat", font=("Arial", 9, "underline"),
            command=lambda: self.show_appointments_tab("Upcoming"),
        ).pack(side="right")

        appointment = next(
            (
                item for item in self.appointments
                if item["status"] in ("Confirmed", "Pending", "Paid")
            ),
            None,
        )
        if appointment:
            card = tk.Frame(
                section, bg="#FFFFFF", relief="solid", bd=1, padx=15, pady=15,
            )
            card.pack(fill="x")
            pet_photo = tk.Label(
                card, text="🐕", font=("Arial", 45), bg="#FFFFFF",
            )
            pet_photo.pack(side="left", padx=(0, 15))
            photo_path = appointment.get("photo_path")
            if photo_path:
                try:
                    image = Image.open(photo_path)
                    image.thumbnail((90, 90), Image.Resampling.LANCZOS)
                    photo_image = ImageTk.PhotoImage(image)
                    self.photo_images.append(photo_image)
                    pet_photo.configure(
                        image=photo_image, text="", width=90, height=90,
                        bg="#FFFFFF",
                    )
                except Exception:
                    pass
            info = tk.Frame(card, bg="#FFFFFF")
            info.pack(side="left", fill="both", expand=True)
            tk.Label(
                info, text=appointment["pet_name"],
                font=("Arial", 12, "bold"), fg="#5C3A21", bg="#FFFFFF",
            ).pack(anchor="w")
            tk.Label(
                info, text=appointment["service"], font=("Arial", 10),
                fg="#666", bg="#FFFFFF",
            ).pack(anchor="w")
            tk.Label(
                info, text=f"{appointment['date']} • {appointment['time']}",
                font=("Arial", 9), fg="#888", bg="#FFFFFF",
            ).pack(anchor="w", pady=(5, 0))
            actions = tk.Frame(card, bg="#FFFFFF")
            actions.pack(side="right")
            status_color = (
                "#C8F0C0" if appointment["status"] == "Confirmed"
                else "#FFE4B5"
            )
            tk.Label(
                actions, text=appointment["status"], bg=status_color,
                fg="#2F4F2F", font=("Arial", 9, "bold"), padx=15, pady=4,
            ).pack(pady=(0, 8))
            tk.Button(
                actions, text="Reschedule", bg="#8B5A2B", fg="white",
                font=("Arial", 9, "bold"), relief="flat", padx=20, pady=5,
                command=lambda: self.show_appointments_tab("Upcoming"),
            ).pack()

    def show_appointments_tab(self, tab_name):
        if tab_name == "Add Appointment":
            self.show_add_appointment_form()
            return
        self.active_tab = tab_name
        self.show_appointments()

    def show_appointments(self):
        self.clear_page()
        self.create_sidebar("Appointments")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=20)
        content.pack(side="right", fill="both", expand=True)

        top_bar = tk.Frame(content, bg="#FFF5EB")
        top_bar.pack(fill="x", pady=(0, 15))
        tk.Label(
            top_bar, text=f"Appointments ({self.active_tab} Appointment)",
            font=("Arial", 12, "bold"), fg="#5C3A21", bg="#FFF5EB",
        ).pack(side="left")

        tabs_frame = tk.Frame(content, bg="#FFF5EB")
        tabs_frame.pack(fill="x", pady=(0, 20))
        for tab in ("Upcoming", "Completed", "Cancelled"):
            is_active = tab == self.active_tab
            tk.Button(
                tabs_frame, text=tab,
                bg="#E8D4C0" if is_active else "#FFFFFF",
                fg="#5C3A21",
                font=("Arial", 10, "bold" if is_active else "normal"),
                relief="solid", bd=1, padx=25, pady=8,
                command=lambda selected=tab: self.show_appointments_tab(selected),
            ).pack(side="left", padx=5)

        tk.Button(
            tabs_frame, text="Add Appointment", bg="#FFFFFF", fg="#5C3A21",
            font=("Arial", 10, "bold"), relief="solid", bd=1, padx=20, pady=8,
            command=self.show_add_appointment_form,
        ).pack(side="right")

        cards_container = tk.Frame(content, bg="#FFF5EB")
        cards_container.pack(fill="both", expand=True)
        if self.active_tab == "Upcoming":
            filtered = [
                appointment for appointment in self.appointments
                if appointment["status"] in ("Pending", "Paid", "Confirmed")
            ]
        else:
            filtered = [
                appointment for appointment in self.appointments
                if appointment["status"] == self.active_tab
            ]

        if not filtered:
            tk.Label(
                cards_container,
                text=f"No {self.active_tab.lower()} appointments.",
                bg="#FFF5EB", fg="#888", font=("Arial", 11),
            ).pack(pady=30)
            return

        status_colors = {
            "Pending": ("#F2B866", "#5C3A21"),
            "Paid": ("#90EE90", "#2F4F2F"),
            "Confirmed": ("#90EE90", "#2F4F2F"),
            "Completed": ("#B8D8B8", "#2F4F2F"),
            "Cancelled": ("#E8C8C8", "#8B2F2F"),
        }
        for appointment in filtered:
            self._render_appointment_card(
                cards_container, appointment, status_colors,
            )

    def show_add_appointment_form(self):
        self.active_tab = "Add Appointment"
        self.clear_page()
        self.create_sidebar("Appointments")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=20)
        content.pack(side="right", fill="both", expand=True)

        header = tk.Frame(content, bg="#FFF5EB")
        header.pack(fill="x", pady=(0, 15))
        tk.Label(
            header, text="Appointments (Add Appointment)",
            font=("Arial", 12, "bold"), fg="#5C3A21", bg="#FFF5EB",
        ).pack(side="left")

        tabs = tk.Frame(content, bg="#FFF5EB")
        tabs.pack(fill="x", pady=(0, 20))
        for tab in ("Upcoming", "Completed", "Cancelled", "Add Appointment"):
            tk.Button(
                tabs,
                text=tab,
                bg="#E8D4C0" if tab == self.active_tab else "#FFFFFF",
                fg="#5C3A21",
                font=("Arial", 10, "bold" if tab == self.active_tab else "normal"),
                relief="solid",
                bd=1,
                padx=20,
                pady=8,
                command=lambda selected=tab: self.show_appointments_tab(selected),
            ).pack(side="left", padx=5)

        form = tk.Frame(
            content, bg="#FFFFFF", relief="solid", bd=1, padx=30, pady=25,
        )
        form.pack(fill="x", pady=10)
        label_style = {
            "font": ("Arial", 10, "bold"),
            "fg": "#5C3A21",
            "bg": "#FFFFFF",
        }
        combo_style = {
            "font": ("Arial", 10),
            "width": 40,
            "state": "readonly",
        }

        options = (
            ("Select Pet", "pet_var", [pet["name"] for pet in self.pets]),
            ("Select Service", "service_var", self.services),
            ("Choose Pet Size", "size_var", self.pet_sizes),
        )
        defaults = {
            "pet_var": self.pets[0]["name"] if self.pets else "",
            "service_var": self.services[0],
            "size_var": "Large (11-16kg)",
        }
        for label, variable_name, values in options:
            tk.Label(form, text=label, **label_style).pack(
                anchor="w", pady=(0, 5),
            )
            variable = tk.StringVar(value=defaults[variable_name])
            setattr(self, variable_name, variable)
            ttk.Combobox(
                form, textvariable=variable, values=values, **combo_style,
            ).pack(fill="x", pady=(0, 15))

        tk.Label(form, text="Choose Date", **label_style).pack(
            anchor="w", pady=(0, 5),
        )
        self.date_var = tk.StringVar(
            value=f"{calendar.month_name[calendar_date.today().month]} "
                  f"{calendar_date.today().day}, {calendar_date.today().year}",
        )
        date_row = tk.Frame(form, bg="#FFFFFF")
        date_row.pack(fill="x", pady=(0, 15))
        date_entry = ttk.Entry(
            date_row, textvariable=self.date_var, width=40,
        )
        date_entry.pack(side="left", fill="x", expand=True)
        tk.Button(
            date_row, text="📅", bg="#F9EDE0", fg="#5C3A21",
            relief="solid", bd=1, command=self.show_calendar_popup,
        ).pack(side="left", padx=(5, 0))

        tk.Label(form, text="Select Available Time", **label_style).pack(
            anchor="w", pady=(0, 5),
        )
        time_slots = (
            "8:00am", "9:00am", "10:00am", "11:00am", "12:00nn",
            "1:00pm", "2:00pm", "3:00pm", "4:00pm", "5:00pm", "6:00pm",
        )
        self.time_var = tk.StringVar()
        time_row = tk.Frame(form, bg="#FFFFFF")
        time_row.pack(fill="x")
        ttk.Combobox(
            time_row, textvariable=self.time_var, values=time_slots,
            font=("Arial", 10), state="readonly",
        ).pack(fill="x", expand=True)
        
        buttons = tk.Frame(form, bg="#FFFFFF")
        buttons.pack()
        tk.Button(
            buttons, text="Cancel", bg="#F9EDE0", fg="#5C3A21",
            font=("Arial", 10, "bold"), relief="solid", bd=1, padx=30, pady=8,
            command=lambda: self.show_appointments_tab("Upcoming"),
        ).pack(side="left", padx=10)
        tk.Button(
            buttons, text="Proceed", bg="#D9C7B8", fg="#5C3A21",
            font=("Arial", 10, "bold"), relief="solid", bd=1, padx=30, pady=8,
            command=self.submit_appointment,
        ).pack(side="left", padx=10)

    def show_calendar_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Select Date")
        popup.geometry("350x330")
        popup.configure(bg="#FFF5EB")
        popup.transient(self.root)

        header = tk.Frame(popup, bg="#FFF5EB")
        header.pack(fill="x", padx=12, pady=10)
        try:
            selected = self._parse_appointment_date(self.date_var.get())
        except ValueError:
            selected = calendar_date.today()
        month_state = [selected.year, selected.month]
        previous_button = tk.Button(
            header, text="‹", bg="#F9EDE0",
            command=lambda: change_month(-1),
        )
        previous_button.pack(side="left")
        month_label = tk.Label(
            header, font=("Arial", 12, "bold"),
            fg="#5C3A21", bg="#FFF5EB",
        )
        month_label.pack(side="left", expand=True)
        next_button = tk.Button(
            header, text="›", bg="#F9EDE0",
            command=lambda: change_month(1),
        )
        next_button.pack(side="right")
        days_frame = tk.Frame(popup, bg="#FFF5EB")
        days_frame.pack()

        def change_month(offset):
            year, month = month_state
            month_index = month - 1 + offset
            month_state[0] = year + month_index // 12
            month_state[1] = month_index % 12 + 1
            show_month(*month_state)

        def show_month(year, month):
            month_label.configure(text=f"{calendar.month_name[month]} {year}")
            for child in days_frame.winfo_children():
                child.destroy()

            for column, day_name in enumerate(
                ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
            ):
                tk.Label(
                    days_frame, text=day_name,
                    font=("Arial", 9, "bold"),
                    bg="#FFF5EB", fg="#8B5A2B",
                ).grid(row=0, column=column, padx=5, pady=5)

            month_calendar = calendar.Calendar(
                firstweekday=calendar.SUNDAY,
            ).monthdayscalendar(year, month)
            for row, week in enumerate(month_calendar, start=1):
                for column, day in enumerate(week):
                    if day:
                        tk.Button(
                            days_frame,
                            text=str(day),
                            width=4,
                            command=lambda selected_day=day: self.select_date(
                                popup, selected_day, month, year,
                            ),
                        ).grid(row=row, column=column, padx=2, pady=2)

        show_month(*month_state)

    def select_date(self, popup, day, month, year):
        self.date_var.set(f"{calendar.month_name[month]} {day}, {year}")
        popup.destroy()

    @staticmethod
    def _parse_appointment_date(value):
        for date_format in ("%B %d, %Y", "%B %d %Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), date_format).date()
            except ValueError:
                continue
        raise ValueError("Enter a valid date, such as November 4, 2026.")

    def get_appointment_price(self, service, pet_size):
        size = "Small"
        if pet_size.startswith("Medium"):
            size = "Medium"
        elif pet_size.startswith("Large") or pet_size.startswith("Extra Large"):
            size = "Large"
        amount = self.service_catalog.get(service, {}).get(size, Decimal("0"))
        return f"P{amount:,.2f}"

    def add_notification(self, appointment_id, notification_type, title, message):
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO notifications
                    (user_id, appointment_id, notification_type, title, message)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    self.user_id, appointment_id, notification_type, title, message,
                ),
            )
            self.db.commit()
            cursor.close()
        except mysql.connector.Error as error:
            self.db.rollback()
            print(f"Unable to save notification: {error}")

    def submit_appointment(self):
        pet_name = self.pet_var.get()
        service = self.service_var.get()
        date_input = self.date_var.get().strip()
        time_input = self.time_var.get().strip()
        pet_size = self.size_var.get()
        if not all((pet_name, service, date_input, time_input, pet_size)):
            messagebox.showwarning(
                "Warning", "Please complete all appointment fields.",
            )
            return

        try:
            selected_date = self._parse_appointment_date(date_input)
        except ValueError:
            messagebox.showwarning(
                "Invalid Date",
                "Enter a valid date such as November 4, 2026, or choose one from the calendar.",
            )
            return
        date = (
            f"{calendar.month_name[selected_date.month]} "
            f"{selected_date.day}, {selected_date.year}"
        )
        self.date_var.set(date)

        try:
            normalized_time = time_input.replace("nn", "pm").upper()
            time = datetime.strptime(
                normalized_time, "%I:%M%p",
            ).strftime("%I:%M %p")
        except ValueError:
            messagebox.showwarning(
                "Invalid Time",
                "Enter a valid time such as 2:30 PM or 14:30.",
            )
            return

        pet = next(
            (item for item in self.pets if item["name"] == pet_name), None,
        )
        if pet is None:
            messagebox.showwarning("Warning", "Please select a valid pet.")
            return

        appointment_price = self.get_appointment_price(service, pet_size)

        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO appointments
                    (user_id, pet_id, service, pet_size, appointment_date,
                     appointment_time, status, price)
                VALUES (%s, %s, %s, %s, %s, %s, 'Pending', %s)
                """,
                (
                    self.user_id, pet["id"], service, pet_size, date, time,
                    appointment_price,
                ),
            )
            appointment_id = cursor.lastrowid
            self.db.commit()
            cursor.close()
            self.add_notification(
                appointment_id,
                "Booked",
                "Appointment booked",
                f"Your {service} appointment for {pet['name']} on {date} at {time} was submitted.",
            )
        except mysql.connector.Error as error:
            self.db.rollback()
            messagebox.showerror(
                "Database Error", f"Unable to save appointment:\n{error}",
            )
            return

        self.appointments.insert(
            0,
            {
                "id": appointment_id,
                "pet_name": pet["name"],
                "breed": pet["breed"],
                "gender": pet["gender"],
                "age": pet["age"],
                "service": service,
                "date": date,
                "time": time,
                "status": "Pending",
                "price": appointment_price,
                "pet_size": pet_size,
                "photo_path": pet.get("photo_path"),
            },
        )
        messagebox.showinfo("Success", "Appointment request added.")
        self.show_appointments_tab("Upcoming")

    def _render_appointment_card(self, parent, appointment, status_colors):
        card = tk.Frame(
            parent, bg="#FFFFFF", relief="solid", bd=1, padx=15, pady=15,
        )
        card.pack(fill="x", pady=8)
        pet_photo = tk.Label(
            card, text="🐕", font=("Arial", 55), bg="#FFFFFF",
        )
        pet_photo.pack(side="left", padx=(0, 15))
        photo_path = appointment.get("photo_path")
        if photo_path:
            try:
                image = Image.open(photo_path)
                image.thumbnail((100, 100), Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(image)
                self.photo_images.append(photo_image)
                pet_photo.configure(
                    image=photo_image, text="", width=100, height=100,
                    bg="#FFFFFF",
                )
            except Exception:
                pass
        info = tk.Frame(card, bg="#FFFFFF")
        info.pack(side="left", fill="both", expand=True)
        tk.Label(
            info, text=appointment["pet_name"],
            font=("Arial", 12, "bold"), fg="#5C3A21", bg="#FFFFFF",
        ).pack(anchor="w")
        tk.Label(
            info,
            text=(
                f"{appointment['breed']} • {appointment['gender']} "
                f"• {appointment['age']}"
            ),
            fg="#888", bg="#FFFFFF", font=("Arial", 9),
        ).pack(anchor="w")
        tk.Frame(info, bg="#D9C7B8", height=1).pack(fill="x", pady=5)
        tk.Label(
            info, text=appointment["service"], font=("Arial", 10),
            fg="#5C3A21", bg="#FFFFFF",
        ).pack(anchor="w")
        tk.Label(
            info, text=appointment["price"], font=("Arial", 9, "bold"),
            fg="#5C3A21", bg="#FFFFFF",
        ).pack(anchor="w", pady=(3, 0))
        tk.Label(
            info, text=f"{appointment['date']} • {appointment['time']}",
            font=("Arial", 9), fg="#888", bg="#FFFFFF",
        ).pack(anchor="w", pady=(5, 0))

        actions = tk.Frame(card, bg="#FFFFFF")
        actions.pack(side="right")
        background, foreground = status_colors.get(
            appointment["status"], ("#DDD", "#555"),
        )
        tk.Label(
            actions, text=appointment["status"], bg=background,
            fg=foreground, font=("Arial", 9, "bold"), padx=20, pady=5,
        ).pack(pady=(0, 10))
        tk.Button(
            actions, text="View Details", bg="#F9EDE0", fg="#5C3A21",
            font=("Arial", 9), relief="solid", bd=1, padx=20, pady=5,
            command=lambda item=appointment: messagebox.showinfo(
                "Details",
                f"Details for:\n{item['pet_name']}\n{item['service']}",
            ),
        ).pack(fill="x", pady=3)
        if appointment["status"] in ("Pending", "Paid", "Confirmed"):
            tk.Button(
                actions, text="Edit Appointment", bg="#8B5A2B",
                fg="white", font=("Arial", 9, "bold"), relief="flat",
                padx=20, pady=5,
                command=lambda item=appointment: self.edit_appointment(item),
            ).pack(fill="x", pady=3)
            tk.Button(
                actions, text="Cancel Appointment", bg="#F9EDE0",
                fg="#5C3A21", font=("Arial", 9), relief="solid", bd=1,
                padx=20, pady=5,
                command=lambda item=appointment: self.cancel_appointment(item),
            ).pack(fill="x", pady=3)
    def edit_appointment(self, appointment):
        popup = tk.Toplevel(self.root)
        popup.title("Edit Appointment")
        popup.geometry("460x540")
        popup.configure(bg="#FFF5EB")
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(
            popup, text="Edit Appointment",
            font=("Arial", 14, "bold"), fg="#4E3021", bg="#FFF5EB",
        ).pack(pady=(18, 12))

        form = tk.Frame(popup, bg="#FFFFFF", padx=25, pady=20, relief="solid", bd=1)
        form.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        label_style = {"font": ("Arial", 9, "bold"), "fg": "#5C3A21", "bg": "#FFFFFF"}

        pet_names = [pet["name"] for pet in self.pets]
        pet_var = tk.StringVar(
            value=appointment["pet_name"] if appointment["pet_name"] in pet_names else ""
        )
        service_var = tk.StringVar(value=appointment["service"])
        size_var = tk.StringVar(value=appointment.get("pet_size", self.pet_sizes[0]))
        date_var = tk.StringVar(value=appointment["date"])

        tk.Label(form, text="Select Pet", **label_style).pack(anchor="w")
        ttk.Combobox(
            form, textvariable=pet_var, values=pet_names,
            state="readonly", width=38, font=("Arial", 10),
        ).pack(anchor="w", pady=(3, 12))

        tk.Label(form, text="Select Service", **label_style).pack(anchor="w")
        ttk.Combobox(
            form, textvariable=service_var, values=self.services,
            state="readonly", width=38, font=("Arial", 10),
        ).pack(anchor="w", pady=(3, 12))

        tk.Label(form, text="Choose Pet Size", **label_style).pack(anchor="w")
        ttk.Combobox(
            form, textvariable=size_var, values=self.pet_sizes,
            state="readonly", width=38, font=("Arial", 10),
        ).pack(anchor="w", pady=(3, 12))

        tk.Label(form, text="Appointment Date", **label_style).pack(anchor="w")
        date_row = tk.Frame(form, bg="#FFFFFF")
        date_row.pack(anchor="w", pady=(3, 12))
        self.date_var = date_var
        date_entry = ttk.Entry(date_row, textvariable=date_var, width=31, state="readonly")
        date_entry.pack(side="left")
        date_entry.bind("<Button-1>", lambda _event: self.show_calendar_popup())
        tk.Button(
            date_row, text="Calendar", bg="#F9EDE0", fg="#5C3A21",
            relief="solid", bd=1, command=self.show_calendar_popup,
        ).pack(side="left", padx=(5, 0))

        tk.Label(form, text="Preferred Time", **label_style).pack(anchor="w")
        original_time = appointment["time"]
        try:
            parsed_time = datetime.strptime(original_time, "%I:%M %p")
            default_time = parsed_time.strftime("%I:%M")
            default_period = parsed_time.strftime("%p")
        except ValueError:
            default_time = original_time
            default_period = "AM"

        time_row = tk.Frame(form, bg="#FFFFFF")
        time_row.pack(anchor="w", pady=(3, 12))
        time_var = tk.StringVar(value=default_time)
        period_var = tk.StringVar(value=default_period)
        tk.Entry(
            time_row, textvariable=time_var, font=("Arial", 10), width=24,
        ).pack(side="left")
        ttk.Combobox(
            time_row, textvariable=period_var, values=("AM", "PM"),
            state="readonly", width=6, font=("Arial", 10),
        ).pack(side="left", padx=(5, 0))

        def save_appointment_changes():
            pet_name = pet_var.get().strip()
            service = service_var.get().strip()
            pet_size = size_var.get().strip()
            date = date_var.get().strip()
            time_text = time_var.get().strip()
            if not all((pet_name, service, pet_size, date, time_text)):
                messagebox.showwarning("Warning", "Please complete all appointment fields.")
                return

            try:
                formatted_time = datetime.strptime(
                    f"{time_text} {period_var.get()}", "%I:%M %p",
                ).strftime("%I:%M %p")
            except ValueError:
                messagebox.showwarning(
                    "Invalid Time", "Enter a valid time such as 2:30 PM.",
                )
                return

            pet = next((item for item in self.pets if item["name"] == pet_name), None)
            if pet is None:
                messagebox.showwarning("Warning", "Please select a valid pet.")
                return

            new_price = self.get_appointment_price(service, pet_size)
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    """
                    UPDATE appointments
                    SET pet_id=%s, service=%s, pet_size=%s,
                        appointment_date=%s, appointment_time=%s,
                        price=%s
                    WHERE id=%s AND user_id=%s
                    """,
                    (
                        pet["id"], service, pet_size, date, formatted_time,
                        new_price, appointment["id"], self.user_id,
                    ),
                )
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror("Database Error", str(error))
                return

            self._load_sample_data()
            popup.destroy()
            self.show_appointments_tab(self.active_tab)
            messagebox.showinfo("Success", "Appointment updated successfully.")

        buttons = tk.Frame(form, bg="#FFFFFF")
        buttons.pack(fill="x", pady=(4, 0))
        tk.Button(
            buttons, text="Cancel", bg="#F9EDE0", fg="#5C3A21",
            relief="solid", bd=1, font=("Arial", 9, "bold"),
            padx=18, pady=7, command=popup.destroy,
        ).pack(side="left", expand=True, padx=5)
        tk.Button(
            buttons, text="Save Changes", bg="#4E3021", fg="white",
            relief="flat", font=("Arial", 9, "bold"),
            padx=18, pady=7, command=save_appointment_changes,
        ).pack(side="left", expand=True, padx=5)

    def cancel_appointment(self, appointment):
        if not messagebox.askyesno(
            "Cancel Appointment",
            f"Cancel this appointment?\n"
            f"{appointment['pet_name']} - {appointment['service']}",
        ):
            return
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE appointments SET status='Cancelled' WHERE id=%s AND user_id=%s",
                (appointment["id"], self.user_id),
            )
            self.db.commit()
            cursor.close()
        except mysql.connector.Error as error:
            self.db.rollback()
            messagebox.showerror("Database Error", str(error))
            return
        self._load_sample_data()
        messagebox.showinfo("Cancelled", "Appointment has been cancelled.")
        self.show_appointments_tab("Cancelled")

    def show_payment_page(self, appointment):
        PawPerfectPaymentUI(self, appointment)

    def show_mypets(self):
        self.clear_page()
        self.create_sidebar("My Pets")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="My Pets", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w")

        action = tk.Frame(content, bg="#FFF5EB")
        action.pack(fill="x", pady=(12, 10))
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            action, textvariable=search_var, font=("Arial", 10),
            relief="solid", bd=1, fg="#4E3021",
        )
        search_entry.pack(side="left", fill="x", expand=True, ipady=7)
        tk.Button(
            action, text="Add New Pet", bg="#4E3021", fg="white",
            font=("Arial", 10, "bold"), relief="flat", padx=18, pady=7,
            command=self.show_add_pet_form,
        ).pack(side="right", padx=(10, 0))

        cards = tk.Frame(content, bg="#FFF5EB")
        cards.pack(fill="both", expand=True)

        def view_pet_profile(pet):
            popup = tk.Toplevel(self.root)
            popup.title(f"{pet['name']} Profile")
            popup.geometry("420x420")
            popup.configure(bg="#FFF5EB")
            popup.transient(self.root)
            popup.grab_set()

            tk.Label(
                popup, text="Pet Profile", font=("Arial", 16, "bold"),
                fg="#4E3021", bg="#FFF5EB",
            ).pack(pady=(18, 10))
            photo_label = tk.Label(
                popup, text="🐕", font=("Arial", 55),
                bg="#D6BFA4", width=7, height=3,
            )
            photo_label.pack(pady=(0, 12))
            photo_path = pet.get("photo_path")
            if photo_path:
                try:
                    image = Image.open(photo_path)
                    image.thumbnail((180, 180), Image.Resampling.LANCZOS)
                    photo_image = ImageTk.PhotoImage(image)
                    self.photo_images.append(photo_image)
                    photo_label.configure(
                        image=photo_image, text="", width=180, height=180,
                        bg="#FFF5EB",
                    )
                except Exception:
                    pass

            profile = tk.Frame(
                popup, bg="#FFFFFF", padx=20, pady=12, relief="solid", bd=1,
            )
            profile.pack(fill="x", padx=30)
            for label, value in (
                ("Name", pet["name"]),
                ("Breed", pet["breed"]),
                ("Gender", pet["gender"]),
                ("Age", pet["age"]),
            ):
                row = tk.Frame(profile, bg="#FFFFFF")
                row.pack(fill="x", pady=3)
                tk.Label(
                    row, text=f"{label}:", width=10, anchor="w",
                    font=("Arial", 9, "bold"), fg="#6A5A50", bg="#FFFFFF",
                ).pack(side="left")
                tk.Label(
                    row, text=value, anchor="w", font=("Arial", 9),
                    fg="#4E3021", bg="#FFFFFF",
                ).pack(side="left", fill="x", expand=True)

        def edit_pet_info(pet):
            popup = tk.Toplevel(self.root)
            popup.title(f"Edit {pet['name']}")
            popup.geometry("420x380")
            popup.configure(bg="#FFF5EB")
            popup.transient(self.root)
            popup.grab_set()
            selected_photo = {"path": pet.get("photo_path")}

            tk.Label(
                popup, text="Edit Pet Information", font=("Arial", 14, "bold"),
                fg="#4E3021", bg="#FFF5EB",
            ).pack(pady=(16, 10))
            form = tk.Frame(popup, bg="#FFF5EB", padx=25)
            form.pack(fill="both", expand=True)
            fields = {}
            for label, value in (
                ("Pet Name", pet["name"]),
                ("Breed", pet["breed"]),
                ("Gender", pet["gender"]),
                ("Age", pet["age"]),
            ):
                tk.Label(
                    form, text=label, font=("Arial", 9),
                    fg="#6A5A50", bg="#FFF5EB",
                ).pack(anchor="w")
                entry = tk.Entry(
                    form, font=("Arial", 10), relief="solid", bd=1,
                    fg="#4E3021", bg="#FFFFFF",
                )
                entry.insert(0, value)
                entry.pack(fill="x", pady=(3, 8), ipady=4)
                fields[label] = entry

            photo_preview = tk.Label(
                form, text="Change Photo", font=("Arial", 8, "bold"),
                fg="#4E3021", bg="#D6BFA4", width=18, pady=8,
            )
            photo_preview.pack(pady=(2, 8))

            def choose_photo():
                path = filedialog.askopenfilename(
                    title="Select New Pet Photo",
                    filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")],
                )
                if path:
                    selected_photo["path"] = path
                    try:
                        image = Image.open(path)
                        image.thumbnail((80, 80), Image.Resampling.LANCZOS)
                        preview = ImageTk.PhotoImage(image)
                        self.photo_images.append(preview)
                        photo_preview.configure(
                            image=preview, text="", width=80, height=80,
                            bg="#FFF5EB",
                        )
                    except Exception:
                        pass

            tk.Button(
                form, text="Choose Photo", bg="#FFFFFF", fg="#4E3021",
                relief="solid", bd=1, font=("Arial", 8),
                command=choose_photo,
            ).pack()

            def save_changes():
                values = {label: entry.get().strip() for label, entry in fields.items()}
                if not all(values.values()):
                    messagebox.showwarning(
                        "Warning", "Please complete all pet information fields.",
                    )
                    return
                try:
                    cursor = self.db.cursor()
                    cursor.execute(
                        """
                        UPDATE pets
                        SET name=%s, breed=%s, gender=%s, age=%s, photo_path=%s
                        WHERE id=%s AND user_id=%s
                        """,
                        (
                            values["Pet Name"], values["Breed"], values["Gender"],
                            values["Age"], selected_photo["path"],
                            pet["id"], self.user_id,
                        ),
                    )
                    self.db.commit()
                    cursor.close()
                except mysql.connector.Error as error:
                    self.db.rollback()
                    messagebox.showerror("Database Error", str(error))
                    return
                pet.update({
                    "name": values["Pet Name"],
                    "breed": values["Breed"],
                    "gender": values["Gender"],
                    "age": values["Age"],
                    "photo_path": selected_photo["path"],
                })
                # Reload database-backed pets and appointments so Dashboard and
                # Appointments immediately see the new photo and pet details.
                self._load_sample_data()
                popup.destroy()
                self.show_mypets()
                messagebox.showinfo("Success", "Pet information updated.")

            tk.Button(
                popup, text="Save Changes", bg="#4E3021", fg="white",
                font=("Arial", 9, "bold"), relief="flat", padx=20, pady=7,
                command=save_changes,
            ).pack(pady=10)

        def delete_pet(pet):
            if not messagebox.askyesno(
                "Delete Pet",
                f"Delete {pet['name']} permanently?\n"
                "Related appointments will also be removed.",
            ):
                return
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "DELETE FROM pets WHERE id=%s AND user_id=%s",
                    (pet["id"], self.user_id),
                )
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror("Database Error", str(error))
                return
            self.pets.remove(pet)
            render_pets()
            messagebox.showinfo("Deleted", f"{pet['name']} was deleted.")

        def render_pets(*args):
            for widget in cards.winfo_children():
                widget.destroy()
            query = search_var.get().strip().lower()
            if query == "search pets...":
                query = ""
            visible = 0
            for pet in self.pets:
                searchable = (
                    pet["name"] + " " + pet["breed"] + " " +
                    pet["gender"] + " " + pet["age"]
                ).lower()
                if query and query not in searchable:
                    continue
                visible += 1
                card = tk.Frame(
                    cards, bg="#FFFFFF", relief="solid", bd=1,
                    highlightthickness=1, highlightbackground="#9A704F",
                )
                card.pack(fill="x", pady=7)
                photo_label = tk.Label(
                    card, text="🐕", font=("Arial", 42),
                    bg="#D6BFA4", width=5, height=2, relief="flat",
                )
                photo_label.pack(side="left", padx=12, pady=10)
                photo_path = pet.get("photo_path")
                if photo_path:
                    try:
                        image = Image.open(photo_path)
                        image.thumbnail((100, 100), Image.Resampling.LANCZOS)
                        photo_image = ImageTk.PhotoImage(image)
                        self.photo_images.append(photo_image)
                        photo_label.configure(
                            image=photo_image, text="", width=100, height=100,
                            bg="#FFFFFF",
                        )
                    except Exception:
                        pass
                details = tk.Frame(card, bg="#FFFFFF")
                details.pack(side="left", fill="both", expand=True, pady=12)
                tk.Label(
                    details, text=pet["name"], font=("Arial", 12, "bold"),
                    fg="#4E3021", bg="#FFFFFF",
                ).pack(anchor="w")
                tk.Label(
                    details,
                    text=f"{pet['breed']}  •  {pet['gender']}  •  {pet['age']}",
                    font=("Arial", 9), fg="#6A5A50", bg="#FFFFFF",
                ).pack(anchor="w", pady=(3, 0))
                buttons = tk.Frame(card, bg="#FFFFFF")
                buttons.pack(side="right", padx=12)
                tk.Button(
                    buttons, text="View Profile", bg="#FFFFFF", fg="#4E3021",
                    font=("Arial", 9, "bold"), relief="solid", bd=1,
                    padx=18, pady=5, width=12,
                    command=lambda item=pet: view_pet_profile(item),
                ).pack(pady=2)
                tk.Button(
                    buttons, text="Edit Info", bg="#FFFFFF", fg="#4E3021",
                    font=("Arial", 9, "bold"), relief="solid", bd=1,
                    padx=18, pady=5, width=12,
                    command=lambda item=pet: edit_pet_info(item),
                ).pack(pady=2)
                tk.Button(
                    buttons, text="Delete Pet", bg="#E99595", fg="#FFFFFF",
                    font=("Arial", 9, "bold"), relief="flat",
                    padx=18, pady=5, width=12,
                    command=lambda item=pet: delete_pet(item),
                ).pack(pady=2)
            if visible == 0:
                tk.Label(
                    cards, text="No pets found.", font=("Arial", 10),
                    fg="#6A5A50", bg="#FFF5EB",
                ).pack(pady=30)

        search_entry.insert(0, "Search pets...")
        search_entry.bind("<FocusIn>", lambda event: search_entry.delete(0, tk.END)
                          if search_entry.get() == "Search pets..." else None)
        search_entry.bind("<FocusOut>", lambda event: search_entry.insert(0, "Search pets...")
                          if not search_entry.get() else None)
        search_var.trace_add("write", render_pets)
        render_pets()

    def show_add_pet_form(self):
        self.clear_page()
        self.create_sidebar("My Pets")
        content = tk.Frame(self.root, bg="#FBF4E9", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="My Pets (Add New Pet)", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FBF4E9",
        ).pack(anchor="w")

        row = tk.Frame(content, bg="#FBF4E9")
        row.pack(fill="x", pady=24)
        form = tk.Frame(
            row, bg="#FFFFFF", padx=20, pady=18, relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        form.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(
            form, text="Pet Information", font=("Arial", 12, "bold"),
            fg="#4E3021", bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 12))

        fields = {}
        for label in ("Pet Name", "Breed", "Gender", "Age"):
            tk.Label(
                form, text=label, font=("Arial", 9),
                fg="#6A5A50", bg="#FFFFFF",
            ).pack(anchor="w")
            entry = tk.Entry(
                form, font=("Arial", 10), relief="solid", bd=1,
                fg="#4E3021", bg="#FFFFFF",
            )
            entry.pack(fill="x", pady=(3, 10), ipady=4)
            fields[label] = entry

        photo = tk.Frame(
            row, bg="#FFFFFF", width=260, relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        photo.pack(side="right", fill="y")
        photo.pack_propagate(False)
        photo_preview = tk.Label(
            photo, text="🐕", font=("Arial", 55), bg="#D6BFA4",
            width=6, height=3,
        )
        photo_preview.pack(pady=18)
        selected_photo = {"path": None}

        def choose_photo():
            path = filedialog.askopenfilename(
                title="Select Pet Photo",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                    ("All files", "*.*"),
                ],
            )
            if not path:
                return
            try:
                image = Image.open(path)
                image.thumbnail((180, 180), Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(image)
                self.photo_images.append(photo_image)
                photo_preview.configure(
                    image=photo_image, text="", width=180, height=180,
                    bg="#FFFFFF",
                )
                selected_photo["path"] = path
            except Exception as error:
                messagebox.showerror(
                    "Photo Error", f"Unable to open this image:\n{error}",
                )

        tk.Button(
            photo, text="Upload a Photo", bg="#FFFFFF", fg="#4E3021",
            relief="solid", bd=1, padx=12, pady=5,
            command=choose_photo,
        ).pack()

        def save_pet():
            values = {name: entry.get().strip() for name, entry in fields.items()}
            if not all(values.values()):
                messagebox.showwarning("Warning", "Please fill in all pet fields.")
                return
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    """
                    INSERT INTO pets
                        (user_id, name, breed, gender, age, photo_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.user_id,
                        values["Pet Name"],
                        values["Breed"],
                        values["Gender"],
                        values["Age"],
                        selected_photo["path"],
                    ),
                )
                pet_id = cursor.lastrowid
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror(
                    "Database Error", f"Unable to save pet:\n{error}",
                )
                return

            self.pets.append({
                "id": pet_id,
                "name": values["Pet Name"],
                "breed": values["Breed"],
                "gender": values["Gender"],
                "age": values["Age"],
                "photo_path": selected_photo["path"],
            })
            messagebox.showinfo("Success", "Pet added successfully.")
            self.show_mypets()

        tk.Button(
            content, text="Save Pet", bg="#4E3021", fg="white",
            font=("Arial", 10, "bold"), relief="flat", padx=24, pady=8,
            command=save_pet,
        ).place(relx=1.0, rely=1.0, x=-5, y=-10, anchor="se")

    def show_services(self):
        self.clear_page()
        self.create_sidebar("Services")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        header = tk.Frame(content, bg="#FFF5EB")
        header.pack(fill="x")
        tk.Label(
            header, text="Services", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(side="left")
        if self.user_role == "admin":
            tk.Button(
                header, text="Add Service", bg="#4E3021", fg="white",
                font=("Arial", 9, "bold"), relief="flat", padx=16, pady=7,
                command=self.show_add_service_dialog,
            ).pack(side="right")
        service_cards = tk.Frame(content, bg="#FFF5EB")
        service_cards.pack(fill="both", expand=True, pady=18)
        for index, name in enumerate(self.services):
            service = self.service_catalog[name]
            card = tk.Frame(
                service_cards, bg="#FFFFFF", relief="solid", bd=1,
                highlightthickness=1, highlightbackground="#9A704F",
                padx=10, pady=8,
            )
            row, column = divmod(index, 3)
            card.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")
            service_cards.grid_columnconfigure(column, weight=1)
            service_cards.grid_rowconfigure(row, weight=1)
            if self.user_role == "admin":
                card_header = tk.Frame(card, bg="#FFFFFF")
                card_header.pack(fill="x")
                service_menu = tk.Menu(card, tearoff=False)
                service_menu.add_command(
                    label="Edit", command=lambda item=name: self.show_add_service_dialog(item),
                )
                service_menu.add_command(
                    label="Delete", command=lambda item=name: self.delete_service(item),
                )
                menu_button = tk.Button(
                    card_header, text="⋮", bg="#FFFFFF", fg="#4E3021",
                    font=("Arial", 14, "bold"), relief="flat", bd=0,
                    cursor="hand2",
                )
                menu_button.configure(
                    command=lambda m=service_menu, b=menu_button:
                        self._post_service_menu(m, b),
                )
                menu_button.pack(side="right")
            icon = ("🛁" if "Bath" in name else "✂️" if "Grooming" in name
                    else "🐾" if "Nail" in name else "🦷" if "Teeth" in name
                    else "🐶")
            tk.Label(
                card, text=icon, font=("Arial", 28), bg="#FFFFFF",
            ).pack()
            tk.Label(
                card, text=name, font=("Arial", 10, "bold"),
                fg="#4E3021", bg="#FFFFFF",
            ).pack(pady=(3, 2))
            tk.Label(
                card, text=service["description"], font=("Arial", 8),
                fg="#6A5A50", bg="#FFFFFF", wraplength=180,
            ).pack()
            prices = tk.Frame(card, bg="#FFFFFF")
            prices.pack(pady=(6, 0), fill="x")
            for column, size in enumerate(("Small", "Medium", "Large")):
                column_frame = tk.Frame(prices, bg="#FFFFFF")
                column_frame.grid(row=0, column=column, sticky="ew", padx=2)
                prices.grid_columnconfigure(column, weight=1)
                tk.Label(
                    column_frame, text=size, font=("Arial", 7),
                    fg="#6A5A50", bg="#FFFFFF",
                ).pack()
                tk.Label(
                    column_frame, text=f"P{service[size]:,.2f}",
                    font=("Arial", 8, "bold"),
                    fg="#4E3021", bg="#FFFFFF",
                ).pack(pady=(3, 0))

    @staticmethod
    def _post_service_menu(menu, button):
        try:
            menu.tk_popup(
                button.winfo_rootx(),
                button.winfo_rooty() + button.winfo_height(),
            )
        finally:
            menu.grab_release()

    def show_add_service_dialog(self, service_name=None):
        editing = service_name is not None
        existing_service = self.service_catalog.get(service_name, {})
        popup = tk.Toplevel(self.root)
        popup.title("Edit Service" if editing else "Add Service")
        popup.geometry("480x500")
        popup.configure(bg="#FFF5EB")
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(
            popup, text="Edit Service" if editing else "Add Service",
            font=("Arial", 14, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(pady=(18, 12))

        form = tk.Frame(
            popup, bg="#FFFFFF", padx=22, pady=18, relief="solid", bd=1,
        )
        form.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        entries = {}
        for label in ("Service Name", "Description"):
            tk.Label(
                form, text=label, font=("Arial", 9, "bold"),
                fg="#5C3A21", bg="#FFFFFF",
            ).pack(anchor="w", pady=(4, 3))
            if label == "Description":
                description = tk.Text(
                    form, height=3, font=("Arial", 10), relief="solid", bd=1,
                )
                description.pack(fill="x", pady=(0, 8))
                entries[label] = description
            else:
                entry = tk.Entry(form, font=("Arial", 10), relief="solid", bd=1)
                entry.pack(fill="x", pady=(0, 8), ipady=4)
                entries[label] = entry

        if editing:
            entries["Service Name"].insert(0, service_name)
            entries["Description"].insert(
                "1.0", existing_service.get("description", ""),
            )

        price_entries = {}
        for size in ("Small", "Medium", "Large"):
            label = f"{size} Price"
            tk.Label(
                form, text=label, font=("Arial", 9, "bold"),
                fg="#5C3A21", bg="#FFFFFF",
            ).pack(anchor="w", pady=(4, 3))
            entry = tk.Entry(form, font=("Arial", 10), relief="solid", bd=1)
            entry.pack(fill="x", pady=(0, 6), ipady=4)
            if editing and size in existing_service:
                entry.insert(0, str(existing_service[size]))
            price_entries[size] = entry

        tk.Label(
            form, text="Enter amounts like 350, P350, ₱350, or 1,000.50.",
            font=("Arial", 8), fg="#888", bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 4))

        def save_service():
            name = entries["Service Name"].get().strip()
            description = entries["Description"].get("1.0", "end").strip()
            if not name or not description:
                messagebox.showwarning(
                    "Invalid Service",
                    "Enter both a service name and description.",
                    parent=popup,
                )
                return

            prices = {}
            try:
                for size, entry in price_entries.items():
                    amount = entry.get().strip().replace(",", "")
                    amount = re.sub(r"^(?:₱|PHP|P)\s*", "", amount, flags=re.IGNORECASE)
                    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", amount):
                        raise InvalidOperation
                    price = Decimal(amount)
                    if (
                        not price.is_finite()
                        or price <= 0
                        or price > Decimal("99999999.99")
                    ):
                        raise InvalidOperation
                    prices[size] = price.quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError):
                messagebox.showwarning(
                    "Invalid Price",
                    "Enter a positive amount up to P99,999,999.99 for each size. "
                    "You may include P, ₱, PHP, or thousands separators.",
                    parent=popup,
                )
                return

            try:
                cursor = self.db.cursor()
                if editing:
                    cursor.execute(
                        """
                        UPDATE services
                        SET name=%s, description=%s, small_price=%s,
                            medium_price=%s, large_price=%s
                        WHERE name=%s
                        """,
                        (
                            name, description, prices["Small"],
                            prices["Medium"], prices["Large"], service_name,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO services
                            (name, description, small_price, medium_price, large_price)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            name, description, prices["Small"],
                            prices["Medium"], prices["Large"],
                        ),
                    )
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror(
                    "Service Error",
                    f"Unable to add service:\n{error}",
                    parent=popup,
                )
                return

            if editing:
                self.services.remove(service_name)
                self.service_catalog.pop(service_name, None)
            self.services.append(name)
            self.services.sort()
            self.service_catalog[name] = {
                "description": description,
                **prices,
            }
            popup.destroy()
            messagebox.showinfo(
                "Service Updated" if editing else "Service Added",
                "The service was updated." if editing else "The service was added.",
            )
            self.show_services()

        buttons = tk.Frame(form, bg="#FFFFFF")
        buttons.pack(pady=(12, 0))
        tk.Button(
            buttons, text="Cancel", bg="#F9EDE0", fg="#5C3A21",
            relief="solid", bd=1, padx=20, pady=7, command=popup.destroy,
        ).pack(side="left", padx=6)
        tk.Button(
            buttons, text="Save Changes" if editing else "Add Service",
            bg="#4E3021", fg="white",
            font=("Arial", 9, "bold"), relief="flat", padx=20, pady=7,
            command=save_service,
        ).pack(side="left", padx=6)

    def delete_service(self, service_name):
        if not messagebox.askyesno(
            "Delete Service",
            f"Delete '{service_name}'? Existing appointments will remain unchanged.",
            parent=self.root,
        ):
            return

        try:
            cursor = self.db.cursor()
            cursor.execute(
                "DELETE FROM services WHERE name=%s", (service_name,),
            )
            self.db.commit()
            cursor.close()
        except mysql.connector.Error as error:
            self.db.rollback()
            messagebox.showerror(
                "Service Error",
                f"Unable to delete service:\n{error}",
                parent=self.root,
            )
            return

        self.services.remove(service_name)
        self.service_catalog.pop(service_name, None)
        messagebox.showinfo(
            "Service Deleted", f"'{service_name}' was deleted.",
        )
        self.show_services()

    def _show_user_notifications(self):
        self.clear_page()
        self.create_sidebar("Message")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="Notifications", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w")

        search_var = tk.StringVar()
        search_entry = tk.Entry(
            content, textvariable=search_var, font=("Arial", 9),
            relief="solid", bd=1, fg="#4E3021",
        )
        search_entry.pack(fill="x", ipady=7, pady=(12, 10))
        search_entry.insert(0, "Search notifications...")
        search_entry.bind("<FocusIn>", lambda event: search_entry.delete(0, tk.END)
                          if search_entry.get() == "Search notifications..." else None)
        search_entry.bind("<FocusOut>", lambda event: search_entry.insert(0, "Search notifications...")
                          if not search_entry.get() else None)

        filter_value = {"value": "All"}
        filter_frame = tk.Frame(content, bg="#FFF5EB")
        filter_frame.pack(fill="x", pady=(0, 10))
        buttons = {}
        cards_frame = tk.Frame(content, bg="#FFF5EB")
        cards_frame.pack(fill="both", expand=True)

        def ensure_notification(appointment, notification_type, title, message):
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT id FROM notifications
                WHERE user_id=%s AND appointment_id=%s AND notification_type=%s
                LIMIT 1
                """,
                (self.user_id, appointment["id"], notification_type),
            )
            exists = cursor.fetchone()
            if exists is None:
                cursor.execute(
                    """
                    INSERT INTO notifications
                        (user_id, appointment_id, notification_type, title, message)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        self.user_id, appointment["id"], notification_type,
                        title, message,
                    ),
                )
                self.db.commit()
            cursor.close()

        for appointment in self.appointments:
            ensure_notification(
                appointment, "Booked", "Appointment booked",
                f"Your {appointment['service']} appointment for "
                f"{appointment['pet_name']} is booked for "
                f"{appointment['date']} at {appointment['time']}.",
            )
            status = appointment["status"]
            if status == "Confirmed":
                ensure_notification(
                    appointment, "Accepted", "Appointment accepted",
                    f"PawPerfect accepted the {appointment['service']} appointment for "
                    f"{appointment['pet_name']} on {appointment['date']}.",
                )
            elif status == "Paid":
                ensure_notification(
                    appointment, "Paid", "Payment confirmed",
                    f"Payment for the {appointment['service']} appointment was recorded.",
                )
            elif status == "Completed":
                ensure_notification(
                    appointment, "Completed", "Appointment completed",
                    f"The {appointment['service']} appointment for "
                    f"{appointment['pet_name']} has been completed.",
                )
            elif status == "Cancelled":
                ensure_notification(
                    appointment, "Cancelled", "Appointment cancelled",
                    f"The {appointment['service']} appointment on "
                    f"{appointment['date']} was cancelled.",
                )

            if status in ("Pending", "Paid", "Confirmed"):
                try:
                    appointment_date = datetime.strptime(
                        appointment["date"], "%B %d, %Y",
                    ).date()
                    days_left = (appointment_date - calendar_date.today()).days
                    if 0 <= days_left <= 3:
                        ensure_notification(
                            appointment, "Reminder", "Appointment reminder",
                            f"Reminder: {appointment['pet_name']} has {appointment['service']} "
                            f"on {appointment['date']} at {appointment['time']}.",
                        )
                except ValueError:
                    pass

        def render_notifications(*args):
            for widget in cards_frame.winfo_children():
                widget.destroy()
            for name, button in buttons.items():
                button.configure(bg="#CDAF8A" if filter_value["value"] == name else "#FFFFFF")

            query = search_var.get().strip().lower()
            if query == "search notifications...":
                query = ""

            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, notification_type, title, message, is_read, created_at
                FROM notifications
                WHERE user_id=%s
                ORDER BY created_at DESC, id DESC
                """,
                (self.user_id,),
            )
            rows = cursor.fetchall()
            cursor.close()

            visible = 0
            for row in rows:
                if filter_value["value"] == "Unread" and row["is_read"]:
                    continue
                searchable = (
                    row["notification_type"] + " " + row["title"] + " " + row["message"]
                ).lower()
                if query and query not in searchable:
                    continue

                visible += 1
                icon = {
                    "Accepted": "✓",
                    "Reminder": "🔔",
                    "Paid": "💳",
                    "Completed": "✔",
                    "Cancelled": "✕",
                    "Booked": "📅",
                }.get(row["notification_type"], "📌")
                card = tk.Frame(
                    cards_frame, bg="#FFFFFF", relief="solid", bd=1,
                    highlightthickness=1, highlightbackground="#9A704F",
                    padx=12, pady=10,
                )
                card.pack(fill="x", pady=5)
                tk.Label(
                    card, text=icon, font=("Arial", 16),
                    bg="#FFFFFF", fg="#4E3021", width=3,
                ).pack(side="left", padx=(0, 10))
                text_frame = tk.Frame(card, bg="#FFFFFF")
                text_frame.pack(side="left", fill="x", expand=True)
                tk.Label(
                    text_frame, text=row["title"], font=("Arial", 9, "bold"),
                    fg="#4E3021", bg="#FFFFFF", anchor="w",
                ).pack(fill="x")
                tk.Label(
                    text_frame, text=row["message"], font=("Arial", 8),
                    fg="#6A5A50", bg="#FFFFFF", anchor="w", wraplength=650,
                    justify="left",
                ).pack(fill="x", pady=(3, 0))

                time_text = row["created_at"].strftime("%b %d, %I:%M %p")
                tk.Label(
                    card, text=time_text, font=("Arial", 7),
                    fg="#888888", bg="#FFFFFF",
                ).pack(side="right", anchor="n")

                if not row["is_read"]:
                    tk.Button(
                        card, text="Mark read", bg="#CDAF8A", fg="#4E3021",
                        relief="flat", font=("Arial", 7, "bold"),
                        command=lambda notification_id=row["id"]: mark_notification_read(
                            notification_id,
                        ),
                    ).pack(side="right", padx=(8, 0))

            if visible == 0:
                tk.Label(
                    cards_frame, text="No notifications found.",
                    bg="#FFF5EB", fg="#6A5A50",
                ).pack(pady=30)

        def mark_notification_read(notification_id):
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "UPDATE notifications SET is_read=TRUE WHERE id=%s AND user_id=%s",
                    (notification_id, self.user_id),
                )
                self.db.commit()
                cursor.close()
                render_notifications()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror("Notification Error", str(error))

        def choose_filter(name):
            filter_value["value"] = name
            render_notifications()

        for index, name in enumerate(("All", "Unread")):
            button = tk.Button(
                filter_frame, text=name, bg="#FFFFFF", fg="#4E3021",
                font=("Arial", 8, "bold"), relief="solid", bd=1, padx=18, pady=6,
                command=lambda value=name: choose_filter(value),
            )
            button.grid(row=0, column=index, sticky="ew", padx=(0, 8))
            filter_frame.grid_columnconfigure(index, weight=1)
            buttons[name] = button

        search_var.trace_add("write", render_notifications)
        render_notifications()

    def show_messages(self):
        if self.user_role != "admin":
            self._show_user_notifications()
            return
        self.clear_page()
        self.create_sidebar("Message")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="Messages", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w")
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            content, textvariable=search_var, font=("Arial", 9),
            relief="solid", bd=1, fg="#4E3021",
        )
        search_entry.pack(fill="x", ipady=7, pady=(12, 10))
        search_entry.insert(0, "Search messages...")
        search_entry.bind("<FocusIn>", lambda event: search_entry.delete(0, tk.END)
                          if search_entry.get() == "Search messages..." else None)
        search_entry.bind("<FocusOut>", lambda event: search_entry.insert(0, "Search messages...")
                          if not search_entry.get() else None)

        filters = {"value": "All"}
        selected = {"value": None}
        selected_message = {"id": None}
        filter_frame = tk.Frame(content, bg="#FFF5EB")
        filter_frame.pack(fill="x", pady=(0, 10))
        filter_buttons = {}
        for index, name in enumerate(("All", "Unread", "Archived")):
            button = tk.Button(
                filter_frame, text=name, bg="#FFFFFF", fg="#4E3021",
                font=("Arial", 8), relief="solid", bd=1, padx=12, pady=5,
            )
            button.grid(row=0, column=index, sticky="ew", padx=(0, 8))
            filter_frame.grid_columnconfigure(index, weight=1)
            filter_buttons[name] = button

        cards_frame = tk.Frame(content, bg="#FFF5EB")
        cards_frame.pack(fill="both", expand=True)

        def load_contacts():
            cursor = self.db.cursor(dictionary=True)
            if self.user_role == "admin":
                cursor.execute(
                    "SELECT id, fullname FROM users WHERE role='user' ORDER BY fullname"
                )
            else:
                cursor.execute(
                    "SELECT id, fullname FROM users WHERE role='admin' ORDER BY id LIMIT 1"
                )
            rows = cursor.fetchall()
            cursor.close()
            return rows

        def delete_user_message(message_id, contact_id):
            if not messagebox.askyesno(
                "Delete Message",
                "Delete this message from the user's conversation?",
                parent=self.root,
            ):
                return

            try:
                cursor = self.db.cursor()
                cursor.execute(
                    """
                    DELETE FROM messages
                    WHERE id=%s AND sender_id=%s AND receiver_id=%s
                    """,
                    (message_id, contact_id, self.user_id),
                )
                if cursor.rowcount == 0:
                    self.db.rollback()
                    cursor.close()
                    messagebox.showwarning(
                        "Message Not Deleted",
                        "The selected user message no longer exists.",
                        parent=self.root,
                    )
                    return
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror(
                    "Message Error", f"Unable to delete message:\n{error}",
                    parent=self.root,
                )
                return

            selected_message["id"] = None
            render_inbox()

        def render_inbox(*args):
            for widget in cards_frame.winfo_children():
                widget.destroy()
            for name, button in filter_buttons.items():
                button.configure(bg="#CDAF8A" if filters["value"] == name else "#FFFFFF")

            query_text = search_var.get().strip().lower()
            if query_text == "search messages...":
                query_text = ""

            try:
                contacts = load_contacts()
            except mysql.connector.Error as error:
                messagebox.showerror(
                    "Message Error", f"Unable to load message contacts:\n{error}",
                )
                return

            if selected["value"] is None and contacts:
                selected["value"] = contacts[0]

            visible = 0
            for contact in contacts:
                cursor = self.db.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT id, sender_id, receiver_id, message, is_read,
                           is_archived, created_at
                    FROM messages
                    WHERE (sender_id=%s AND receiver_id=%s)
                       OR (sender_id=%s AND receiver_id=%s)
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """,
                    (self.user_id, contact["id"], contact["id"], self.user_id),
                )
                latest = cursor.fetchone()
                cursor.execute(
                    """
                    SELECT COUNT(*) AS unread_count
                    FROM messages
                    WHERE sender_id=%s AND receiver_id=%s AND is_read=FALSE
                    """,
                    (contact["id"], self.user_id),
                )
                unread_count = cursor.fetchone()["unread_count"]
                cursor.close()

                if latest:
                    preview = latest["message"]
                    timestamp = latest["created_at"]
                    archived = bool(latest["is_archived"])
                else:
                    preview = "Start a conversation with PawPerfect."
                    timestamp = None
                    archived = False

                if filters["value"] == "Unread" and unread_count == 0:
                    continue
                if filters["value"] == "Archived" and not archived:
                    continue
                if filters["value"] == "All" and archived:
                    continue
                if query_text and query_text not in (
                    contact["fullname"].lower() + " " + preview.lower()
                ):
                    continue

                visible += 1
                title = "PawPerfect Team" if self.user_role == "user" else contact["fullname"]
                card = tk.Frame(
                    cards_frame, bg="#FFFFFF", relief="solid", bd=1,
                    highlightthickness=1, highlightbackground="#9A704F",
                )
                card.pack(fill="x", pady=4)

                header = tk.Frame(card, bg="#FFFFFF", padx=12, pady=7)
                header.pack(fill="x")
                title_label = tk.Label(
                    header, text=title, font=("Arial", 9, "bold"),
                    fg="#4E3021", bg="#FFFFFF",
                )
                title_label.pack(side="left")
                time_text = timestamp.strftime("%I:%M %p") if timestamp else ""
                time_label = tk.Label(
                    header, text=time_text, font=("Arial", 7),
                    fg="#6A5A50", bg="#FFFFFF",
                )
                time_label.pack(side="right")

                preview_label = tk.Label(
                    card, text=preview, font=("Arial", 8), fg="#6A5A50",
                    bg="#FFFFFF", wraplength=650, anchor="w", justify="left",
                    padx=12,
                )
                preview_label.pack(fill="x", pady=(0, 7))

                if unread_count:
                    tk.Frame(card, bg="#E99595", width=7, height=7).place(
                        relx=1.0, x=-10, y=38, anchor="e",
                    )

                def open_thread(event=None, row=contact):
                    selected["value"] = row
                    try:
                        cursor = self.db.cursor()
                        cursor.execute(
                            """
                            UPDATE messages SET is_read=TRUE
                            WHERE sender_id=%s AND receiver_id=%s
                            """,
                            (row["id"], self.user_id),
                        )
                        self.db.commit()
                        cursor.close()
                    except mysql.connector.Error as error:
                        self.db.rollback()
                        messagebox.showerror(
                            "Message Error",
                            f"Unable to mark messages as read:\n{error}",
                        )
                        return
                    render_inbox()

                card.bind("<Button-1>", open_thread, add="+")
                header.bind("<Button-1>", open_thread, add="+")
                title_label.bind("<Button-1>", open_thread, add="+")
                time_label.bind("<Button-1>", open_thread, add="+")
                preview_label.bind("<Button-1>", open_thread, add="+")
                card.configure(cursor="hand2")
                header.configure(cursor="hand2")
                title_label.configure(cursor="hand2")
                time_label.configure(cursor="hand2")
                preview_label.configure(cursor="hand2")

                tk.Button(
                    card,
                    text="Open conversation",
                    bg="#CDAF8A",
                    fg="#4E3021",
                    font=("Arial", 8, "bold"),
                    relief="flat",
                    padx=10,
                    pady=4,
                    cursor="hand2",
                    command=lambda row=contact: open_thread(row=row),
                ).pack(anchor="e", padx=12, pady=(0, 8))

                if selected["value"] and selected["value"]["id"] == contact["id"]:
                    contact_id = contact["id"]
                    detail = tk.Frame(card, bg="#FAF5EE", padx=10, pady=8)
                    detail.pack(fill="x", padx=10, pady=(0, 10))
                    cursor = self.db.cursor(dictionary=True)
                    cursor.execute(
                        """
                        SELECT id, sender_id, message, created_at
                        FROM messages
                        WHERE (sender_id=%s AND receiver_id=%s)
                           OR (sender_id=%s AND receiver_id=%s)
                        ORDER BY created_at, id
                        """,
                        (self.user_id, contact["id"], contact["id"], self.user_id),
                    )
                    messages = cursor.fetchall()
                    cursor.close()
                    if not messages:
                        tk.Label(
                            detail, text="No messages yet.",
                            bg="#FAF5EE", fg="#888",
                        ).pack(pady=5)
                    for row in messages:
                        is_user_message = row["sender_id"] == contact_id
                        align = "w" if is_user_message else "e"
                        is_selected = selected_message["id"] == row["id"]
                        bubble_color = (
                            "#F2D8D8" if is_selected
                            else "#FFFFFF" if is_user_message
                            else "#D7C0A5"
                        )
                        message_row = tk.Frame(detail, bg="#FAF5EE")
                        message_row.pack(fill="x", pady=3)
                        bubble = tk.Label(
                            message_row, text=row["message"], bg=bubble_color,
                            fg="#4E3021", padx=8, pady=6, wraplength=520,
                            justify="left",
                            cursor="hand2" if is_user_message else "",
                        )
                        bubble.pack(side="left" if is_user_message else "right")
                        if is_user_message:
                            bubble.bind(
                                "<Button-1>",
                                lambda _event, message_id=row["id"]:
                                    select_user_message(message_id),
                            )
                            if is_selected:
                                tk.Button(
                                    message_row, text="Delete",
                                    bg="#A94442", fg="white",
                                    font=("Arial", 8, "bold"), relief="flat",
                                    padx=8, pady=3,
                                    command=lambda message_id=row["id"],
                                                   recipient_id=contact_id:
                                        delete_user_message(message_id, recipient_id),
                                ).pack(side="left", padx=(6, 0))

                    def select_user_message(message_id):
                        selected_message["id"] = message_id
                        render_inbox()

                    composer = tk.Frame(detail, bg="#FAF5EE")
                    composer.pack(fill="x", pady=(8, 0))
                    entry = tk.Entry(composer, relief="solid", bd=1)
                    entry.pack(side="left", fill="x", expand=True, ipady=5)

                    def send_message(
                        recipient_id=contact_id, message_entry=entry,
                    ):
                        message = message_entry.get().strip()
                        if not message:
                            return
                        try:
                            cursor = self.db.cursor()
                            cursor.execute(
                                """
                                INSERT INTO messages (sender_id, receiver_id, message)
                                VALUES (%s, %s, %s)
                                """,
                                (self.user_id, recipient_id, message),
                            )
                            self.db.commit()
                            cursor.close()
                            render_inbox()
                        except mysql.connector.Error as error:
                            self.db.rollback()
                            messagebox.showerror("Message Error", str(error))

                    tk.Button(
                        composer, text="Send", bg="#4E3021", fg="white",
                        relief="flat", padx=12, command=send_message,
                    ).pack(side="right", padx=(6, 0))
                    entry.bind("<Return>", lambda _event: send_message())
                    tk.Button(
                        composer,
                        text="Restore" if archived else "Archive",
                        bg="#B9A58E", fg="#FFFFFF", relief="flat", padx=8,
                        command=lambda row=contact: archive_thread(row),
                    ).pack(side="right")

            if visible == 0:
                tk.Label(
                    cards_frame, text="No messages found.",
                    bg="#FFF5EB", fg="#6A5A50",
                ).pack(pady=30)

        def archive_thread(contact):
            try:
                cursor = self.db.cursor()
                cursor.execute(
                    """
                    UPDATE messages SET is_archived=NOT is_archived
                    WHERE (sender_id=%s AND receiver_id=%s)
                       OR (sender_id=%s AND receiver_id=%s)
                    """,
                    (self.user_id, contact["id"], contact["id"], self.user_id),
                )
                self.db.commit()
                cursor.close()
                selected["value"] = None
                filters["value"] = "Archived" if filters["value"] == "All" else filters["value"]
                render_inbox()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror("Message Error", str(error))

        def choose_filter(name):
            filters["value"] = name
            selected["value"] = None
            render_inbox()

        for name, button in filter_buttons.items():
            button.configure(command=lambda value=name: choose_filter(value))
        search_var.trace_add("write", render_inbox)
        render_inbox()

    def show_settings(self):
        if self.user_role == "admin":
            self.show_admin_settings()
        else:
            self.show_user_settings()

    def show_user_settings(self):
        self.clear_page()
        self.create_sidebar("Settings")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="User Settings", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w", pady=(0, 15))

        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT fullname FROM users WHERE id=%s", (self.user_id,),
            )
            account = cursor.fetchone()
            cursor.execute(
                """
                SELECT preference_key, preference_value
                FROM user_preferences WHERE user_id=%s
                """,
                (self.user_id,),
            )
            preferences = dict(cursor.fetchall())
            cursor.close()
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Settings Error", f"Unable to load account settings:\n{error}",
            )
            return

        if account is None:
            messagebox.showerror(
                "Settings Error", "Unable to find the current user account.",
            )
            return

        account_card = tk.Frame(
            content, bg="#FFFFFF", padx=18, pady=15, relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        account_card.pack(fill="x")
        tk.Label(
            account_card, text="Account Settings", font=("Arial", 10, "bold"),
            fg="#4E3021", bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 10))
        tk.Label(
            account_card, text="Name", font=("Arial", 8),
            fg="#6A5A50", bg="#FFFFFF",
        ).pack(anchor="w", pady=(2, 2))
        name_entry = tk.Entry(
            account_card, font=("Arial", 10), relief="solid", bd=1,
            fg="#4E3021",
        )
        name_entry.insert(0, account[0])
        name_entry.pack(fill="x", pady=(0, 7), ipady=4)

        tk.Label(
            account_card, text="Account Preferences",
            font=("Arial", 10, "bold"), fg="#4E3021", bg="#FFFFFF",
        ).pack(anchor="w", pady=(12, 8))
        preference_vars = {}
        for label, key, values, default in (
            ("Language", "language", ("English", "Filipino"), "English"),
            (
                "Time Zone", "time_zone",
                ("Philippine Standard Time (UTC+8)",),
                "Philippine Standard Time (UTC+8)",
            ),
        ):
            tk.Label(
                account_card, text=label, font=("Arial", 8),
                fg="#6A5A50", bg="#FFFFFF",
            ).pack(anchor="w", pady=(2, 2))
            variable = tk.StringVar(value=preferences.get(key, default))
            preference_vars[key] = variable
            ttk.Combobox(
                account_card, textvariable=variable, values=values,
                state="readonly", font=("Arial", 9),
            ).pack(fill="x", pady=(0, 7), ipady=4)

        security_card = tk.Frame(
            content, bg="#FFFFFF", padx=18, pady=15, relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        security_card.pack(fill="x", pady=(12, 0))
        tk.Label(
            security_card, text="Security and Login",
            font=("Arial", 10, "bold"), fg="#4E3021", bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            security_card,
            text="Leave both password fields blank to keep your current password.",
            font=("Arial", 8), fg="#6A5A50", bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 5))

        password_entries = {}
        for label in ("New Password", "Confirm Password"):
            tk.Label(
                security_card, text=label, font=("Arial", 8),
                fg="#6A5A50", bg="#FFFFFF",
            ).pack(anchor="w", pady=(2, 2))
            password_row = tk.Frame(security_card, bg="#FFFFFF")
            password_row.pack(fill="x", pady=(0, 7))
            password_entry = tk.Entry(
                password_row, font=("Arial", 10), relief="solid", bd=1,
                fg="#4E3021", show="*",
            )
            password_entry.pack(side="left", fill="x", expand=True, ipady=4)
            password_entries[label] = password_entry

            def toggle_password(field=password_entry, button=None):
                visible = field.cget("show") == "*"
                field.configure(show="" if visible else "*")
                if button is not None:
                    button.configure(text="??" if visible else "??")

            eye_button = tk.Button(
                password_row, text="??", width=3, bg="#FFFFFF",
                fg="#8B5A2B", relief="flat", bd=0,
                activebackground="#FFFFFF", cursor="hand2",
            )
            eye_button.configure(
                command=lambda field=password_entry, button=eye_button:
                    toggle_password(field, button),
            )
            eye_button.pack(side="right", padx=(5, 0))

        def save_user_settings():
            name = name_entry.get().strip()
            new_password = password_entries["New Password"].get()
            confirm_password = password_entries["Confirm Password"].get()
            if not name:
                messagebox.showwarning(
                    "Invalid Settings", "Name cannot be empty.",
                )
                return
            if new_password or confirm_password:
                if not new_password or not confirm_password:
                    messagebox.showwarning(
                        "Password Confirmation Required",
                        "Enter and confirm the new password.",
                    )
                    return
                if new_password != confirm_password:
                    messagebox.showwarning(
                        "Passwords Do Not Match",
                        "The new password and confirmation must match.",
                    )
                    return
                if len(new_password) < 4:
                    messagebox.showwarning(
                        "Invalid Password",
                        "Password must be at least 4 characters.",
                    )
                    return

            try:
                cursor = self.db.cursor()
                if new_password:
                    cursor.execute(
                        "UPDATE users SET fullname=%s, password=%s WHERE id=%s",
                        (name, new_password, self.user_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE users SET fullname=%s WHERE id=%s",
                        (name, self.user_id),
                    )
                for key, variable in preference_vars.items():
                    cursor.execute(
                        """
                        INSERT INTO user_preferences
                            (user_id, preference_key, preference_value)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            preference_value=VALUES(preference_value)
                        """,
                        (self.user_id, key, variable.get()),
                    )
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror(
                    "Settings Error", f"Unable to save account settings:\n{error}",
                )
                return

            self.current_user = name
            messagebox.showinfo("Settings Saved", "Your settings were saved.")
            self.show_user_settings()

        tk.Button(
            content, text="Save Changes", bg="#4E3021", fg="white",
            font=("Arial", 10, "bold"), relief="flat", padx=24, pady=8,
            command=save_user_settings,
        ).pack(anchor="w", pady=(12, 0))

    def show_admin_settings(self):
        self.clear_page()
        self.create_sidebar("Settings")
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=18)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text="Settings", font=("Arial", 16, "bold"),
            fg="#4E3021", bg="#FFF5EB",
        ).pack(anchor="w")

        left = tk.Frame(content, bg="#FFF5EB")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(content, bg="#FFF5EB")
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        try:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT fullname, password FROM users WHERE id=%s",
                (self.user_id,),
            )
            account_row = cursor.fetchone()
            cursor.execute("SELECT setting_key, setting_value FROM app_settings")
            saved_settings = dict(cursor.fetchall())
            cursor.close()
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Settings Error", f"Unable to load settings:\n{error}",
            )
            return

        if account_row is None:
            messagebox.showerror(
                "Settings Error", "Unable to find the current user account.",
            )
            return
        account_name, account_password = account_row
        is_admin = self.user_role == "admin"
        setting_entries = {}
        preference_vars = {}

        def settings_card(parent, title, fields):
            card = tk.Frame(
                parent, bg="#FFFFFF", padx=18, pady=15, relief="solid", bd=1,
                highlightthickness=1, highlightbackground="#9A704F",
            )
            card.pack(fill="x", pady=(0, 12))
            tk.Label(
                card, text=title, font=("Arial", 10, "bold"),
                fg="#4E3021", bg="#FFFFFF",
            ).pack(anchor="w", pady=(0, 10))
            for label, value in fields:
                tk.Label(
                    card, text=label, font=("Arial", 8),
                    fg="#6A5A50", bg="#FFFFFF",
                ).pack(anchor="w", pady=(2, 2))
                is_password = label == "Password"
                is_system_setting = label in (
                    "Business Hours",
                    "Maximum Appointments per day",
                    "Cancellation Policy",
                )
                password_row = None
                if is_password:
                    password_row = tk.Frame(card, bg="#FFFFFF")
                    password_row.pack(fill="x", pady=(0, 7))
                entry = tk.Entry(
                    password_row or card,
                    font=("Arial", 10), relief="solid", bd=1,
                    fg="#4E3021",
                    show="*" if is_password else "",
                )
                entry.insert(0, value)
                if is_system_setting and not is_admin:
                    entry.configure(state="readonly")
                setting_entries[label] = entry
                if is_password:
                    entry.pack(
                        side="left", fill="x", expand=True, ipady=4,
                    )

                    def toggle_visibility(field=entry, button=None):
                        visible = field.cget("show") == "*"
                        field.configure(show="" if visible else "*")
                        if button is not None:
                            button.configure(text="🙈" if visible else "👁")

                    visibility_button = tk.Button(
                        password_row, text="👁", width=3, bg="#FFFFFF",
                        fg="#8B5A2B", relief="flat", bd=0,
                        activebackground="#FFFFFF", cursor="hand2",
                    )
                    visibility_button.configure(
                        command=lambda field=entry, button=visibility_button:
                            toggle_visibility(field, button),
                    )
                    visibility_button.pack(side="right", padx=(5, 0))
                else:
                    entry.pack(fill="x", pady=(0, 7), ipady=4)
            return card

        settings_card(left, "General Settings", (
            ("Username", account_name),
            ("Password", account_password),
            ("Business Hours", saved_settings.get(
                "business_hours", "9:00 AM - 6:00 PM",
            )),
        ))
        settings_card(left, "Appointment Settings", (
            ("Maximum Appointments per day", saved_settings.get(
                "maximum_appointments_per_day", "25",
            )),
            ("Cancellation Policy", saved_settings.get(
                "cancellation_policy",
                "Minimum 2 hours before the scheduled appointment",
            )),
        ))

        card = tk.Frame(
            right, bg="#FFFFFF", padx=18, pady=15, relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#9A704F",
        )
        card.pack(fill="both", expand=True, pady=(0, 12))
        tk.Label(
            card, text="System Preferences", font=("Arial", 10, "bold"),
            fg="#4E3021", bg="#FFFFFF",
        ).pack(anchor="w", pady=(0, 10))
        for label, key, values, default in (
            ("Language", "language", ("English", "Filipino"), "English"),
            (
                "Time Zone", "time_zone",
                ("Philippine Standard Time (UTC+8)",),
                "Philippine Standard Time (UTC+8)",
            ),
        ):
            tk.Label(
                card, text=label, font=("Arial", 8),
                fg="#6A5A50", bg="#FFFFFF",
            ).pack(anchor="w", pady=(4, 2))
            variable = tk.StringVar(value=saved_settings.get(key, default))
            preference_vars[key] = variable
            ttk.Combobox(
                card, textvariable=variable, values=values,
                state="readonly" if is_admin else "disabled",
                font=("Arial", 9),
            ).pack(fill="x", ipady=5, pady=(0, 8))

        def save_settings():
            username = setting_entries["Username"].get().strip()
            password = setting_entries["Password"].get()
            if not username:
                messagebox.showwarning(
                    "Invalid Settings", "Username cannot be empty.",
                )
                return
            if len(password) < 4:
                messagebox.showwarning(
                    "Invalid Settings",
                    "Password must be at least 4 characters.",
                )
                return

            settings_to_save = {}
            if is_admin:
                business_hours = setting_entries["Business Hours"].get().strip()
                max_appointments = setting_entries[
                    "Maximum Appointments per day"
                ].get().strip()
                cancellation_policy = setting_entries[
                    "Cancellation Policy"
                ].get().strip()
                if not business_hours or not cancellation_policy:
                    messagebox.showwarning(
                        "Invalid Settings",
                        "Complete all appointment and business settings.",
                    )
                    return
                try:
                    if int(max_appointments) < 1:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning(
                        "Invalid Settings",
                        "Maximum appointments per day must be a positive number.",
                    )
                    return
                settings_to_save = {
                    "business_hours": business_hours,
                    "maximum_appointments_per_day": max_appointments,
                    "cancellation_policy": cancellation_policy,
                    **{
                        key: variable.get()
                        for key, variable in preference_vars.items()
                    },
                }

            try:
                cursor = self.db.cursor()
                cursor.execute(
                    "UPDATE users SET fullname=%s, password=%s WHERE id=%s",
                    (username, password, self.user_id),
                )
                for key, value in settings_to_save.items():
                    cursor.execute(
                        """
                        INSERT INTO app_settings (setting_key, setting_value)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value)
                        """,
                        (key, value),
                    )
                self.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.db.rollback()
                messagebox.showerror(
                    "Settings Error", f"Unable to save settings:\n{error}",
                )
                return

            self.current_user = username
            messagebox.showinfo("Settings Saved", "Your settings were saved.")
            self.show_settings()

        tk.Button(
            left, text="Save Changes", bg="#4E3021", fg="white",
            font=("Arial", 10, "bold"), relief="flat", padx=24, pady=8,
            command=save_settings,
        ).pack(anchor="w", pady=(0, 12))

        tk.Button(
            card, text="Logout", bg="#B9A58E", fg="#FFFFFF",
            font=("Arial", 10, "bold"), relief="flat", pady=7,
            command=self.logout,
        ).pack(side="bottom", fill="x")

    def _show_placeholder_page(self, active_page, title):
        self.clear_page()
        self.create_sidebar(active_page)
        content = tk.Frame(self.root, bg="#FFF5EB", padx=25, pady=20)
        content.pack(side="right", fill="both", expand=True)
        tk.Label(
            content, text=title, font=("Arial", 16, "bold"),
            fg="#5C3A21", bg="#FFF5EB",
        ).pack(pady=50)


class PawPerfectPaymentUI:
    def __init__(self, app, appointment):
        self.app = app
        self.root = app.root
        self.appointment = appointment
        self.payment_method = tk.StringVar(
            value=appointment.get("payment_method", "gcash"),
        )
        self.app.clear_page()
        self.root.configure(bg="#FAF3E9")
        self.create_sidebar()
        self.create_main_content()

    def create_sidebar(self):
        self.app.create_sidebar("Appointments")

    def create_main_content(self):
        """Main content area"""
        main_frame = tk.Frame(self.root, bg="#FAF3E9")
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top header with user name
        header_frame = tk.Frame(main_frame, bg="#FAF3E9")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            header_frame,
            text="Selecting Payment Method",
            font=("Arial", 14, "bold"),
            bg="#FAF3E9",
            fg="#4A3520"
        ).pack(side=tk.LEFT)
        
        # Two-column content
        content_frame = tk.Frame(main_frame, bg="#FAF3E9")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Appointment Summary Card ---
        summary_card = tk.Frame(
            content_frame,
            bg="#F2E4D4",
            padx=20,
            pady=20,
            relief=tk.RAISED,
            bd=1
        )
        summary_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(
            summary_card,
            text="Appointment Summary",
            font=("Arial", 12, "bold"),
            bg="#F2E4D4",
            fg="#4A3520"
        ).pack(pady=(0, 10))
        
        # Pet info row
        pet_info_frame = tk.Frame(summary_card, bg="#F2E4D4")
        pet_info_frame.pack(fill=tk.X, pady=5)
        
        # Placeholder for dog image
        pet_img = tk.Label(
            pet_info_frame,
            text="🐕",
            font=("Arial", 40),
            bg="#E8D4C0",
            width=6,
            height=3
        )
        pet_img.pack(side=tk.LEFT, padx=(0, 15))
        photo_path = self.appointment.get("photo_path")
        if photo_path:
            try:
                image = Image.open(photo_path)
                image.thumbnail((100, 100), Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(image)
                self.app.photo_images.append(photo_image)
                pet_img.configure(
                    image=photo_image, text="", width=100, height=100,
                    bg="#E8D4C0",
                )
            except Exception:
                pass
        
        pet_details = (
            f"{self.appointment['pet_name']}\n"
            f"{self.appointment['breed']}\n"
            f"{self.appointment['gender']}\n"
            f"{self.appointment['age']}"
        )
        tk.Label(
            pet_info_frame,
            text=pet_details,
            font=("Arial", 11),
            bg="#F2E4D4",
            fg="#4A3520",
            justify=tk.LEFT
        ).pack(side=tk.LEFT)
        
        # Service details
        details = [
            ("Service", self.appointment["service"]),
            ("Date", self.appointment["date"]),
            ("Time", self.appointment["time"]),
            ("Pet Size", self.appointment.get("pet_size", "Not specified")),
            ("Price", self.appointment["price"]),
        ]
        
        for label_text, value_text in details:
            row = tk.Frame(summary_card, bg="#F2E4D4")
            row.pack(fill=tk.X, pady=3)
            tk.Label(
                row, text=label_text, font=("Arial", 10, "bold"),
                bg="#F2E4D4", fg="#4A3520", width=12, anchor="w"
            ).pack(side=tk.LEFT)
            tk.Label(
                row, text=value_text, font=("Arial", 10),
                bg="#F2E4D4", fg="#4A3520", anchor="w"
            ).pack(side=tk.LEFT)
        
        # Divider
        ttk.Separator(summary_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Total amount
        tk.Label(
            summary_card,
            text="Total Amount",
            font=("Arial", 10),
            bg="#F2E4D4",
            fg="#4A3520"
        ).pack()
        tk.Label(
            summary_card,
            text=self.appointment["price"],
            font=("Arial", 24, "bold"),
            bg="#F2E4D4",
            fg="#8B4513"
        ).pack(pady=5)
        
        # --- Payment Method Card ---
        payment_card = tk.Frame(
            content_frame,
            bg="#F2E4D4",
            padx=20,
            pady=20,
            relief=tk.RAISED,
            bd=1
        )
        payment_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(
            payment_card,
            text="Select Payment Method",
            font=("Arial", 12, "bold"),
            bg="#F2E4D4",
            fg="#4A3520"
        ).pack(pady=(0, 15))
        
        # GCash Option
        gcash_frame = tk.Frame(
            payment_card,
            bg="#E8D4C0",
            padx=15,
            pady=15,
            relief=tk.RIDGE,
            bd=1
        )
        gcash_frame.pack(fill=tk.X, pady=8)
        tk.Radiobutton(
            gcash_frame,
            text="Gcash",
            variable=self.payment_method,
            value="gcash",
            font=("Arial", 11, "bold"),
            bg="#E8D4C0",
            fg="#4A3520",
            selectcolor="#D4B99C",
            activebackground="#E8D4C0"
        ).pack(anchor=tk.W)
        tk.Label(
            gcash_frame,
            text="Pay Securely using your Gcash Account",
            font=("Arial", 9),
            bg="#E8D4C0",
            fg="#5C4033"
        ).pack(anchor=tk.W)
        
        # Cash Option
        cash_frame = tk.Frame(
            payment_card,
            bg="#FAF3E9",
            padx=15,
            pady=15,
            relief=tk.RIDGE,
            bd=1
        )
        cash_frame.pack(fill=tk.X, pady=8)
        tk.Radiobutton(
            cash_frame,
            text="Cash",
            variable=self.payment_method,
            value="cash",
            font=("Arial", 11, "bold"),
            bg="#FAF3E9",
            fg="#4A3520",
            selectcolor="#D4B99C",
            activebackground="#FAF3E9"
        ).pack(anchor=tk.W)
        tk.Label(
            cash_frame,
            text="Pay in person at the store",
            font=("Arial", 9),
            bg="#FAF3E9",
            fg="#5C4033"
        ).pack(anchor=tk.W)
        
        # Bottom action buttons
        btn_frame = tk.Frame(main_frame, bg="#FAF3E9")
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 10),
            bg="#E0C4A8",
            fg="#4A3520",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=lambda: self.app.show_appointments_tab("Upcoming"),
        ).pack(side=tk.LEFT)
        
        tk.Button(
            btn_frame,
            text="Proceed",
            font=("Arial", 10, "bold"),
            bg="#D4A76A",
            fg="white",
            relief=tk.FLAT,
            padx=30,
            pady=8,
            command=self.proceed,
        ).pack(side=tk.RIGHT)

    def proceed(self):
        self.appointment["payment_method"] = self.payment_method.get()
        if self.appointment.get("id"):
            try:
                cursor = self.app.db.cursor()
                cursor.execute(
                    """
                    UPDATE appointments
                    SET payment_method=%s
                    WHERE id=%s AND user_id=%s
                    """,
                    (
                        self.appointment["payment_method"],
                        self.appointment["id"],
                        self.app.user_id,
                    ),
                )
                self.app.db.commit()
                cursor.close()
            except mysql.connector.Error as error:
                self.app.db.rollback()
                messagebox.showerror(
                    "Database Error",
                    f"Unable to save payment method:\n{error}",
                )
                return
        messagebox.showinfo(
            "Payment Method Saved",
            "Your payment method was saved. Payment processing is not "
            "connected yet, so the appointment remains pending.",
        )
        self.app.show_appointments_tab("Upcoming")

if __name__ == "__main__":
    root = tk.Tk()
    PawPerfectApp(root)
    root.mainloop()