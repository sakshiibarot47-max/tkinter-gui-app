Full Source Code
"""
GYM MEMBERSHIP MANAGEMENT SYSTEM (MySQL Edition)
-------------------------------------------------
A desktop GUI app built with Tkinter (GUI) + MySQL
 (storage).
Features:
- Members : Register / View / Update / Delete gym
 members
- Plans : Create / View / Update / Delete
 subscription plans
- Payments : Record / View / Delete member payments
- Renewals : Auto-calculated list of members due /
 overdue for renewal
- Colorful UI: styled tabs, buttons, headers, and
 status-coded rows
SETUP (do this once)
---------------------
1. Install the MySQL connector:
 pip install mysql-connector-python
2. Make sure a MySQL server is running locally (or
 update DB_CONFIG below
 to point at your server/host).
3. Update the DB_CONFIG dictionary below with your
 MySQL username/password.
 You do NOT need to create the database or tables
 yourself - the app
 creates the "gym_db" database and all tables
 automatically on first run.
HOW TO RUN
----------
Option A - Jupyter Notebook:
 1. Paste this whole file's code into a single
 Jupyter cell.
 2. Run the cell. A separate GUI window will
 open.
 3. NOTE: Tkinter's mainloop() blocks the kernel
 while the window is open.
 Close the GUI window when done and the cell
 will finish executing.
Option B - Plain Python:
 python gym_management_system_mysql.py
FIX APPLIED IN THIS VERSION
----------------------------
Previously, if you renamed a member (or a plan)
 using "Update Selected", the
Payments tab's Member dropdown (or Members tab's
 Plan dropdown) could keep
showing the OLD name as leftover text. That old
 name was no longer a valid
key in the internal name->id lookup dict, so
 submitting the form incorrectly
showed "Select a valid member." even though a name
 was visibly typed in the
box. refresh_member_combo() and
 refresh_plan_combo() now clear the field
automatically if its current text is no longer a
 valid, existing name.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import mysql.connector
from mysql.connector import errorcode
#
 ================================================
 ==================
# MYSQL CONNECTION CONFIG -- EDIT THESE VALUES FOR
 YOUR SETUP
#
 ================================================
 ==================
DB_CONFIG = {
 "host": "localhost",
 "user": "root",
 "password": "", # XAMPP's default MySQL root
 user has NO password
"port": 3306, # XAMPP's default MySQL port
}
DB_NAME = "gym_db"
#
 ================================================
 ==================
# COLOR PALETTE (used throughout the GUI)
#
 ================================================
 ==================
COLORS = {
 "bg": "#eef2f5", # window / frame
 background
 "header": "#2c3e50", # dark navy -
 headers, tab headings
 "header_text": "#ffffff",
 "accent": "#2980b9", # blue accent
 "add": "#27ae60", # green
 "update": "#f39c12", # orange/amber
 "delete": "#c0392b", # red
 "clear": "#7f8c8d", # grey
 "row_odd": "#ffffff",
 "row_even": "#f4f6f7",
 "overdue": "#f5b7b1", # soft red
 "duesoon": "#fbeeb2", # soft yellow
 "active": "#c9f0d3", # soft green
}
#
 ================================================
 ==================
# DATABASE LAYER (MySQL)
#
 ================================================
 ==================
class Database:
 """Handles all MySQL setup and queries (the
 'model' layer)."""
 def __init__(self, config=DB_CONFIG,
 db_name=DB_NAME):
 try:
 # Connect without a specific database
 first so we can create it
 self.conn =
 mysql.connector.connect(**config)
 except mysql.connector.Error as err:
 raise SystemExit(
 f"Could not connect to MySQL
 server: {err}\n"
 f"Check host/user/password in
 DB_CONFIG at the top of this
 file."
 )
 self.create_database(db_name)
 self.conn.database = db_name
 self.create_tables()
 self.seed_default_plans()
 def create_database(self, db_name):
 cur = self.conn.cursor()
 cur.execute(
 f"CREATE DATABASE IF NOT EXISTS
 `{db_name}` "
 f"CHARACTER SET utf8mb4 COLLATE
 utf8mb4_unicode_ci"
 )
 self.conn.commit()
 cur.close()
 def create_tables(self):
 cur = self.conn.cursor()
 # PLANS: name must be unique,
 duration/price must be positive
 cur.execute("""
 CREATE TABLE IF NOT EXISTS plans (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE,
 duration_months INT NOT NULL,
 price DECIMAL(10,2) NOT NULL,
 CONSTRAINT chk_plan_duration CHECK
 (duration_months > 0),
 CONSTRAINT chk_plan_price CHECK
 (price >= 0)
 ) ENGINE=InnoDB
 """)
   # MEMBERS: name/join_date required, plan is
 optional FK
 cur.execute("""
 CREATE TABLE IF NOT EXISTS members (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 phone VARCHAR(20),
 email VARCHAR(150),
 join_date DATE NOT NULL,
 plan_id INT,
 CONSTRAINT fk_member_plan
 FOREIGN KEY (plan_id)
 REFERENCES plans(id)
 ON DELETE SET NULL
 ON UPDATE CASCADE
 ) ENGINE=InnoDB
 """)
 # PAYMENTS: amount must be positive, tied
 to a member (required FK)
 cur.execute("""
 CREATE TABLE IF NOT EXISTS payments (
 id INT AUTO_INCREMENT PRIMARY KEY,
 member_id INT NOT NULL,
 amount DECIMAL(10,2) NOT NULL,
 payment_date DATE NOT NULL,
 method
 ENUM('Cash','Card','UPI','Bank
 Transfer') DEFAULT 'Cash',
 CONSTRAINT fk_payment_member
 FOREIGN KEY (member_id)
 REFERENCES members(id)
 ON DELETE CASCADE
 ON UPDATE CASCADE,
 CONSTRAINT chk_payment_amount CHECK
 (amount > 0)
 ) ENGINE=InnoDB
 """)
 self.conn.commit()
 cur.close()
 def seed_default_plans(self):
 cur = self.conn.cursor()
 cur.execute("SELECT COUNT(*) FROM plans")
 if cur.fetchone()[0] == 0:
 defaults = [
 ("Monthly", 1, 1000.0),
 ("Quarterly", 3, 2700.0),
 ("Half-Yearly", 6, 5000.0),
 ("Annual", 12, 9000.0),
 ]
 cur.executemany(
 "INSERT INTO plans (name,
 duration_months, price) VALUES
 (%s,%s,%s)",
 defaults,
 )
 self.conn.commit()
 cur.close()
 # ---------------- PLANS ----------------
 def add_plan(self, name, duration, price):
 cur = self.conn.cursor()
 cur.execute(
 "INSERT INTO plans (name,
 duration_months, price) VALUES
 (%s,%s,%s)",
 (name, duration, price),
 )
 self.conn.commit()
 cur.close()
 def update_plan(self, plan_id, name, duration,
 price):
 cur = self.conn.cursor()
 cur.execute(
 "UPDATE plans SET name=%s,
 duration_months=%s, price=%s WHERE
 id=%s",
 (name, duration, price, plan_id),
 )
 self.conn.commit()
 cur.close()
 def delete_plan(self, plan_id):
 cur = self.conn.cursor()
 cur.execute("DELETE FROM plans WHERE
 id=%s", (plan_id,))
self.conn.commit()
 cur.close()
 def get_plans(self):
 cur = self.conn.cursor()
 cur.execute("SELECT * FROM plans ORDER BY
 id")
 rows = cur.fetchall()
 cur.close()
 return rows
 def get_plan_names(self):
 cur = self.conn.cursor()
 cur.execute("SELECT id, name FROM plans
 ORDER BY name")
 rows = cur.fetchall()
 cur.close()
 return rows
 # ---------------- MEMBERS ----------------
 def add_member(self, name, phone, email,
 join_date, plan_id):
 cur = self.conn.cursor()
 cur.execute(
 "INSERT INTO members (name, phone,
 email, join_date, plan_id) "
 "VALUES (%s,%s,%s,%s,%s)",
 (name, phone, email, join_date,
 plan_id),
 )
 self.conn.commit()
 cur.close()
 def update_member(self, member_id, name, phone,
 email, join_date, plan_id):
 cur = self.conn.cursor()
 cur.execute(
 "UPDATE members SET name=%s, phone=%s,
 email=%s, join_date=%s, plan_id=%s "
 "WHERE id=%s",
 (name, phone, email, join_date,
 plan_id, member_id),
 )
 self.conn.commit()
 cur.close()
 def delete_member(self, member_id):
 cur = self.conn.cursor()
 cur.execute("DELETE FROM members WHERE
 id=%s", (member_id,))
 self.conn.commit()
 cur.close()
 def get_members(self):
 cur = self.conn.cursor()
 cur.execute("""
 SELECT members.id, members.name,
 members.phone, members.email,
 members.join_date, plans.name,
 plans.duration_months,
 members.plan_id
 FROM members
 LEFT JOIN plans ON members.plan_id =
 plans.id
 ORDER BY members.id
 """)
 rows = cur.fetchall()
 cur.close()
 return rows
 def get_member_names(self):
 cur = self.conn.cursor()
 cur.execute("SELECT id, name FROM members
 ORDER BY name")
 rows = cur.fetchall()
 cur.close()
 return rows
 # ---------------- PAYMENTS ----------------
 def add_payment(self, member_id, amount,
 payment_date, method):
 cur = self.conn.cursor()
 cur.execute(
 "INSERT INTO payments (member_id,
 amount, payment_date, method) "
 "VALUES (%s,%s,%s,%s)",
 (member_id, amount, payment_date,
 method),
 )
 self.conn.commit()
   cur.close()
 def delete_payment(self, payment_id):
 cur = self.conn.cursor()
 cur.execute("DELETE FROM payments WHERE
 id=%s", (payment_id,))
 self.conn.commit()
 cur.close()
 def get_payments(self):
 cur = self.conn.cursor()
 cur.execute("""
 SELECT payments.id, members.name,
 payments.amount,
 payments.payment_date,
 payments.method,
 payments.member_id
 FROM payments
 JOIN members ON payments.member_id =
 members.id
 ORDER BY payments.payment_date DESC
 """)
 rows = cur.fetchall()
 cur.close()
 return rows
 # ---------------- RENEWALS (derived, no
 separate table needed) ----------------
 def get_renewals(self):
 """
 For every member with a plan, compute the
 expiry date
 (join_date + plan duration) and the days
 remaining.
 """
 cur = self.conn.cursor()
 cur.execute("""
 SELECT members.id, members.name,
 members.phone, members.join_date,
 plans.name, plans.duration_months
 FROM members
 JOIN plans ON members.plan_id = plans.id
 """)
 rows = cur.fetchall()
 cur.close()
 results = []
 today = date.today()
 for m_id, name, phone, join_dt, plan_name,
 duration in rows:
 # join_dt comes back as a datetime.date
 from MySQL already
 if isinstance(join_dt, str):
 join_dt =
 datetime.strptime(join_dt,
 "%Y-%m-%d").date()
 month = join_dt.month - 1 + duration
 year = join_dt.year + month // 12
 month = month % 12 + 1
 day = min(join_dt.day, 28)
 expiry = date(year, month, day)
 days_left = (expiry - today).days
 if days_left < 0:
 status = "OVERDUE"
 elif days_left <= 7:
 status = "DUE SOON"
 else:
 status = "ACTIVE"
 results.append((m_id, name, phone,
 plan_name, expiry.isoformat(),
 days_left, status))
 results.sort(key=lambda r: r[5])
 return results
#
 ================================================
 ==================
# GUI LAYER
#
 ================================================
 ==================
class GymApp:
 def __init__(self, root):
 self.root = root
 self.root.title("Gym Membership Management
 System")
 self.root.geometry("1000x620")
 self.root.configure(bg=COLORS["bg"])
 # Track which record (if any) is currently
  selected for edit
 self.selected_member_id = None
 self.selected_plan_id = None
 self.selected_payment_id = None
 self.db = Database()
 self.setup_styles()
 # ---- Header bar ----
 header = tk.Frame(root,
 bg=COLORS["header"], height=56)
 header.pack(fill="x", side="top")
 tk.Label(
 header, text="\U0001F3CB Gym Membership
 Management System",
 bg=COLORS["header"],
 fg=COLORS["header_text"],
 font=("Segoe UI", 16, "bold"), pady=12
 ).pack(side="left", padx=16)
 notebook = ttk.Notebook(root,
 style="Colored.TNotebook")
 notebook.pack(fill="both", expand=True,
 padx=8, pady=8)
 self.members_tab = ttk.Frame(notebook,
 style="Body.TFrame")
 self.plans_tab = ttk.Frame(notebook,
 style="Body.TFrame")
 self.payments_tab = ttk.Frame(notebook,
 style="Body.TFrame")
 self.renewals_tab = ttk.Frame(notebook,
 style="Body.TFrame")
 notebook.add(self.members_tab, text="
 Members ")
 notebook.add(self.plans_tab, text=" Plans ")
 notebook.add(self.payments_tab, text="
 Payments ")
 notebook.add(self.renewals_tab, text="
 Renewal Reminders ")
 self.build_members_tab()
 self.build_plans_tab()
 self.build_payments_tab()
 self.build_renewals_tab()
 self.refresh_all()
 #
 --------------------------------------------
 -------------------
 # STYLES / COLORS
 #
 --------------------------------------------
 -------------------
 def setup_styles(self):
 style = ttk.Style()
 try:
 style.theme_use("clam")
 except tk.TclError:
 pass
 style.configure("Body.TFrame",
 background=COLORS["bg"])
 style.configure("TLabelframe",
 background=COLORS["bg"], borderwidth=2)
 style.configure("TLabelframe.Label",
 background=COLORS["bg"],
 foreground=COLORS["header"]
 , font=("Segoe UI",
 10, "bold"))
 style.configure("TLabel",
 background=COLORS["bg"], font=("Segoe
 UI", 9))
 # Notebook tabs
 style.configure("Colored.TNotebook",
 background=COLORS["bg"], borderwidth=0)
 style.configure("Colored.TNotebook.Tab",
 background="#d5dbdb",
 foreground=COLORS["header"]
 , font=("Segoe UI",
 10, "bold"),
 padding=[14, 8])
 style.map("Colored.TNotebook.Tab",
 background=[("selected",
 COLORS["accent"])]
   foreground=[("selected",
 "#ffffff")])
 # Treeview (tables)
 style.configure("Treeview",
 background="#ffffff",
 fieldbackground="#ffffff",
 rowheight=26, font=("Segoe
 UI", 9))
 style.configure("Treeview.Heading",
 background=COLORS["header"],
 foreground="#ffffff",
 font=("Segoe UI", 9,
 "bold"))
 style.map("Treeview.Heading",
 background=[("active",
 COLORS["accent"])])
 # Colored action buttons
 for tag, color in (("Add", COLORS["add"]),
 ("Update", COLORS["update"]),
 ("Delete",
 COLORS["delete"]),
 ("Clear",
 COLORS["clear"])):
 style.configure(f"{tag}.TButton",
 background=color,
 foreground="white",
 font=("Segoe UI", 9,
 "bold"),
 padding=6,
 borderwidth=0)
 style.map(f"{tag}.TButton",
 background=[("active", color),
 ("pressed", color)])
 style.configure("Accent.TButton",
 background=COLORS["accent"],
 foreground="white",
 font=("Segoe UI", 9,
 "bold"), padding=6,
 borderwidth=0)
 style.map("Accent.TButton",
 background=[("active",
 COLORS["accent"])])
 def stripe_rows(self, tree):
 """Apply alternating row colors to any
 Treeview."""
 for i, row in
 enumerate(tree.get_children()):
 base_tag = "evenrow" if i % 2 == 0 else
 "oddrow"
 existing = tree.item(row, "tags")
 # keep any status tag
 (overdue/duesoon/active) already
 applied
 if existing and existing[0] not in
 ("evenrow", "oddrow"):
 continue
 tree.item(row, tags=(base_tag,))
 #
 --------------------------------------------
 -------------------
 # MEMBERS TAB
 #
 --------------------------------------------
 -------------------
 def build_members_tab(self):
 frame = self.members_tab
 form = ttk.LabelFrame(frame, text="Member
 Details")
 form.pack(fill="x", padx=10, pady=10)
 self.m_name = tk.StringVar()
 self.m_phone = tk.StringVar()
 self.m_email = tk.StringVar()
 self.m_join =
 tk.StringVar(value=date.today().isoforma
 t())
 self.m_plan = tk.StringVar()
 ttk.Label(form, text="Name:").grid(row=0,
 column=0, sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.m_name,
 width=25).grid(row=0, column=1, padx=5,
 pady=5)
 ttk.Label(form, text="Phone:").grid(row=0,
   column=2, sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.m_phone,
 width=20).grid(row=0, column=3, padx=5,
 pady=5)
 ttk.Label(form, text="Email:").grid(row=1,
 column=0, sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.m_email,
 width=25).grid(row=1, column=1, padx=5,
 pady=5)
 ttk.Label(form, text="Join Date
 (YYYY-MM-DD):").grid(row=1, column=2,
 sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.m_join,
 width=20).grid(row=1, column=3, padx=5,
 pady=5)
 ttk.Label(form, text="Plan:").grid(row=2,
 column=0, sticky="w", padx=5, pady=5)
 self.m_plan_combo = ttk.Combobox(form,
 textvariable=self.m_plan, width=22,
 state="readonly")
 self.m_plan_combo.grid(row=2, column=1,
 padx=5, pady=5)
 btns = ttk.Frame(form, style="Body.TFrame")
 btns.grid(row=2, column=2, columnspan=2,
 sticky="e", padx=5, pady=5)
 ttk.Button(btns, text="Add",
 style="Add.TButton",
 command=self.add_member).pack(sid
 e="left", padx=3)
 ttk.Button(btns, text="Update Selected",
 style="Update.TButton",
 command=self.update_member).pack(
 side="left", padx=3)
 ttk.Button(btns, text="Delete Selected",
 style="Delete.TButton",
 command=self.delete_member).pack(
 side="left", padx=3)
 ttk.Button(btns, text="Clear Form",
 style="Clear.TButton",
 command=self.clear_member_form).p
 ack(side="left", padx=3)
 cols = ("ID", "Name", "Phone", "Email",
 "Join Date", "Plan", "Duration(mo)")
 self.members_tree = ttk.Treeview(frame,
 columns=cols, show="headings",
 height=14)
 for c in cols:
 self.members_tree.heading(c, text=c)
 self.members_tree.column(c, width=110,
 anchor="center")
 self.members_tree.pack(fill="both",
 expand=True, padx=10, pady=(0, 10))
 self.members_tree.bind("<<TreeviewSelect>>",
 self.on_member_select)
 self.members_tree.tag_configure("oddrow",
 background=COLORS["row_odd"])
 self.members_tree.tag_configure("evenrow",
 background=COLORS["row_even"])
 def clear_member_form(self):
 self.m_name.set("")
 self.m_phone.set("")
 self.m_email.set("")
 self.m_join.set(date.today().isoformat())
 self.m_plan.set("")
 self.selected_member_id = None
 self.members_tree.selection_remove(self.memb
 ers_tree.selection())
 def refresh_plan_combo(self):
 plans = self.db.get_plan_names()
 self._plan_lookup = {name: pid for pid,
 name in plans}
 self.m_plan_combo["values"] =
 list(self._plan_lookup.keys())
 # FIX: if the box is showing a plan name
 that no longer exists
 # (e.g. it was renamed or deleted), clear
 it instead of leaving
 # stale text that will silently fail to map
 to a plan_id.
 current = self.m_plan.get()
 if current and current not in
 self._plan_lookup:
   self.m_plan.set("")
 def add_member(self):
 name = self.m_name.get().strip()
 join_date_str = self.m_join.get().strip()
 plan_name = self.m_plan.get().strip()
 if not name:
 messagebox.showwarning("Validation",
 "Name is required.")
 return
 if not self.validate_date(join_date_str):
 messagebox.showwarning("Validation",
 "Join date must be in YYYY-MM-DD
 format.")
 return
 plan_id = self._plan_lookup.get(plan_name)
 try:
 self.db.add_member(name,
 self.m_phone.get().strip(),
 self.m_email.get().strip(),
 join_date_str,
 plan_id)
 except mysql.connector.Error as err:
 messagebox.showerror("Database Error",
 str(err))
 return
 messagebox.showinfo("Success", f"Member
 '{name}' added.")
 self.clear_member_form()
 self.refresh_all()
 def on_member_select(self, event):
 sel = self.members_tree.selection()
 if not sel:
 return
 values = self.members_tree.item(sel[0],
 "values")
 self.selected_member_id = int(values[0])
 self.m_name.set(values[1])
 self.m_phone.set(values[2])
 self.m_email.set(values[3])
 self.m_join.set(values[4])
 self.m_plan.set(values[5] if values[5] !=
 "None" else "")
 def update_member(self):
 if not self.selected_member_id:
 messagebox.showwarning("Selection",
 "Select a member from the table
 first.")
 return
 name = self.m_name.get().strip()
 join_date_str = self.m_join.get().strip()
 if not name:
 messagebox.showwarning("Validation",
 "Name is required.")
 return
 if not self.validate_date(join_date_str):
 messagebox.showwarning("Validation",
 "Join date must be in YYYY-MM-DD
 format.")
 return
 plan_id =
 self._plan_lookup.get(self.m_plan.get().
 strip())
 try:
 self.db.update_member(self.selected_memb
 er_id, name,
 self.m_phone.get().strip(),
 self.m_email.get(
 ).strip(),
 join_date_str
 , plan_id)
 except mysql.connector.Error as err:
 messagebox.showerror("Database Error",
 str(err))
 return
 messagebox.showinfo("Success", "Member
 updated.")
 self.clear_member_form()
 self.refresh_all()
 def delete_member(self):
 if not self.selected_member_id:
 messagebox.showwarning("Selection",
 "Select a member from the table
 first.")
   return
 if messagebox.askyesno("Confirm", "Delete
 this member? Their payments will also
 be removed."):
 self.db.delete_member(self.selected_memb
 er_id)
 self.clear_member_form()
 self.refresh_all()
 @staticmethod
 def validate_date(s):
 try:
 datetime.strptime(s, "%Y-%m-%d")
 return True
 except ValueError:
 return False
 def refresh_members(self):
 for row in self.members_tree.get_children():
 self.members_tree.delete(row)
 for m in self.db.get_members():
 m_id, name, phone, email, join_date,
 plan_name, duration, plan_id = m
 self.members_tree.insert("", "end",
 values=(
 m_id, name, phone or "", email or
 "", join_date,
 plan_name or "None", duration or ""
 ))
 self.stripe_rows(self.members_tree)
 #
 --------------------------------------------
 -------------------
 # PLANS TAB
 #
 --------------------------------------------
 -------------------
 def build_plans_tab(self):
 frame = self.plans_tab
 form = ttk.LabelFrame(frame, text="Plan
 Details")
 form.pack(fill="x", padx=10, pady=10)
 self.p_name = tk.StringVar()
 self.p_duration = tk.StringVar()
 self.p_price = tk.StringVar()
 ttk.Label(form, text="Plan
 Name:").grid(row=0, column=0,
 sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.p_name,
 width=20).grid(row=0, column=1, padx=5,
 pady=5)
 ttk.Label(form, text="Duration
 (months):").grid(row=0, column=2,
 sticky="w", padx=5, pady=5)
 ttk.Entry(form,
 textvariable=self.p_duration,
 width=10).grid(row=0, column=3, padx=5,
 pady=5)
 ttk.Label(form, text="Price:").grid(row=0,
 column=4, sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.p_price,
 width=10).grid(row=0, column=5, padx=5,
 pady=5)
 btns = ttk.Frame(form, style="Body.TFrame")
 btns.grid(row=1, column=0, columnspan=6,
 pady=8)
 ttk.Button(btns, text="Add",
 style="Add.TButton",
 command=self.add_plan).pack(side=
 "left", padx=3)
 ttk.Button(btns, text="Update Selected",
 style="Update.TButton",
 command=self.update_plan).pack(si
 de="left", padx=3)
 ttk.Button(btns, text="Delete Selected",
 style="Delete.TButton",
 command=self.delete_plan).pack(si
 de="left", padx=3)
 ttk.Button(btns, text="Clear Form",
 style="Clear.TButton",
 command=self.clear_plan_form).pac
 k(side="left", padx=3)
 cols = ("ID", "Name", "Duration (months)",
   "Price")
 self.plans_tree = ttk.Treeview(frame,
 columns=cols, show="headings",
 height=14)
 for c in cols:
 self.plans_tree.heading(c, text=c)
 self.plans_tree.column(c, width=150,
 anchor="center")
 self.plans_tree.pack(fill="both",
 expand=True, padx=10, pady=(0, 10))
 self.plans_tree.bind("<<TreeviewSelect>>",
 self.on_plan_select)
 self.plans_tree.tag_configure("oddrow",
 background=COLORS["row_odd"])
 self.plans_tree.tag_configure("evenrow",
 background=COLORS["row_even"])
 def clear_plan_form(self):
 self.p_name.set("")
 self.p_duration.set("")
 self.p_price.set("")
 self.selected_plan_id = None
 self.plans_tree.selection_remove(self.plans_
 tree.selection())
 def add_plan(self):
 name = self.p_name.get().strip()
 duration = self.p_duration.get().strip()
 price = self.p_price.get().strip()
 if not name or not duration or not price:
 messagebox.showwarning("Validation",
 "All plan fields are required.")
 return
 try:
 duration = int(duration)
 price = float(price)
 except ValueError:
 messagebox.showwarning("Validation",
 "Duration must be an integer, price
 a number.")
 return
 if duration <= 0 or price < 0:
 messagebox.showwarning("Validation",
 "Duration must be > 0 and price
 must be >= 0.")
 return
 try:
 self.db.add_plan(name, duration, price)
 except mysql.connector.Error as err:
 if err.errno == errorcode.ER_DUP_ENTRY:
 messagebox.showerror("Error", "A
 plan with this name already
 exists.")
 else:
 messagebox.showerror("Database
 Error", str(err))
 return
 messagebox.showinfo("Success", f"Plan
 '{name}' added.")
 self.clear_plan_form()
 self.refresh_all()
 def on_plan_select(self, event):
 sel = self.plans_tree.selection()
 if not sel:
 return
 values = self.plans_tree.item(sel[0],
 "values")
 self.selected_plan_id = int(values[0])
 self.p_name.set(values[1])
 self.p_duration.set(values[2])
 self.p_price.set(values[3])
 def update_plan(self):
 if not self.selected_plan_id:
 messagebox.showwarning("Selection",
 "Select a plan from the table
 first.")
 return
 try:
 duration =
 int(self.p_duration.get().strip())
 price =
 float(self.p_price.get().strip())
 except ValueError:
 messagebox.showwarning("Validation",
 "Duration must be an integer, price
 a number.")
 return
 try:
 self.db.update_plan(self.selected_plan_i
 d, self.p_name.get().strip(),
 duration, price)
 except mysql.connector.Error as err:
 messagebox.showerror("Database Error",
 str(err))
 return
 messagebox.showinfo("Success", "Plan
 updated.")
 self.clear_plan_form()
 self.refresh_all()
 def delete_plan(self):
 if not self.selected_plan_id:
 messagebox.showwarning("Selection",
 "Select a plan from the table
 first.")
 return
 if messagebox.askyesno("Confirm", "Delete
 this plan? Members using it will show
 'No Plan'."):
 self.db.delete_plan(self.selected_plan_i
 d)
 self.clear_plan_form()
 self.refresh_all()
 def refresh_plans(self):
 for row in self.plans_tree.get_children():
 self.plans_tree.delete(row)
 for p in self.db.get_plans():
 self.plans_tree.insert("", "end",
 values=p)
 self.stripe_rows(self.plans_tree)
 #
 --------------------------------------------
 -------------------
 # PAYMENTS TAB
 #
 --------------------------------------------
 -------------------
 def build_payments_tab(self):
 frame = self.payments_tab
 form = ttk.LabelFrame(frame, text="Record
 Payment")
 form.pack(fill="x", padx=10, pady=10)
 self.pay_member = tk.StringVar()
 self.pay_amount = tk.StringVar()
 self.pay_date =
 tk.StringVar(value=date.today().isoforma
 t())
 self.pay_method = tk.StringVar(value="Cash")
 ttk.Label(form, text="Member:").grid(row=0,
 column=0, sticky="w", padx=5, pady=5)
 self.pay_member_combo = ttk.Combobox(form,
 textvariable=self.pay_member, width=22,
 state="readonly")
 self.pay_member_combo.grid(row=0, column=1,
 padx=5, pady=5)
 ttk.Label(form, text="Amount:").grid(row=0,
 column=2, sticky="w", padx=5, pady=5)
 ttk.Entry(form,
 textvariable=self.pay_amount,
 width=12).grid(row=0, column=3, padx=5,
 pady=5)
 ttk.Label(form, text="Date
 (YYYY-MM-DD):").grid(row=1, column=0,
 sticky="w", padx=5, pady=5)
 ttk.Entry(form, textvariable=self.pay_date,
 width=22).grid(row=1, column=1, padx=5,
 pady=5)
 ttk.Label(form, text="Method:").grid(row=1,
 column=2, sticky="w", padx=5, pady=5)
 ttk.Combobox(form,
 textvariable=self.pay_method, width=12,
 state="readonly",
 values=["Cash", "Card", "UPI",
 "Bank
 Transfer"]).grid(row=1,
 column=3, padx=5, pady=5)
 btns = ttk.Frame(form, style="Body.TFrame")
 btns.grid(row=2, column=0, column
 pady=8)
 ttk.Button(btns, text="Add Payment",
 style="Add.TButton",
 command=self.add_payment).pack(si
 de="left", padx=3)
 ttk.Button(btns, text="Delete Selected",
 style="Delete.TButton",
 command=self.delete_payment).pack
 (side="left", padx=3)
 ttk.Button(btns, text="Clear Form",
 style="Clear.TButton",
 command=self.clear_payment_form).
 pack(side="left", padx=3)
 cols = ("ID", "Member", "Amount", "Date",
 "Method")
 self.payments_tree = ttk.Treeview(frame,
 columns=cols, show="headings",
 height=14)
 for c in cols:
 self.payments_tree.heading(c, text=c)
 self.payments_tree.column(c, width=140,
 anchor="center")
 self.payments_tree.pack(fill="both",
 expand=True, padx=10, pady=(0, 10))
 self.payments_tree.bind("<<TreeviewSelect>>"
 , self.on_payment_select)
 self.payments_tree.tag_configure("oddrow",
 background=COLORS["row_odd"])
 self.payments_tree.tag_configure("evenrow",
 background=COLORS["row_even"])
 def clear_payment_form(self):
 self.pay_member.set("")
 self.pay_amount.set("")
 self.pay_date.set(date.today().isoformat())
 self.pay_method.set("Cash")
 self.selected_payment_id = None
 self.payments_tree.selection_remove(self.pay
 ments_tree.selection())
 def refresh_member_combo(self):
 members = self.db.get_member_names()
 self._member_lookup = {name: mid for mid,
 name in members}
 self.pay_member_combo["values"] =
 list(self._member_lookup.keys())
 # FIX: this is the bug you hit. If a member
 was renamed (or deleted)
 # after this box already had their old name
 typed into it, that old
 # name is no longer a key in
 _member_lookup. Previously the box just
 # kept showing the stale text, so "Add
 Payment" always failed with
 # "Select a valid member." even though
 something was visibly typed.
 # Now we clear it so you're prompted to
 reselect a real member.
 current = self.pay_member.get()
 if current and current not in
 self._member_lookup:
 self.pay_member.set("")
 def add_payment(self):
 member_name = self.pay_member.get().strip()
 amount = self.pay_amount.get().strip()
 pay_date = self.pay_date.get().strip()
 if not member_name or member_name not in
 self._member_lookup:
 messagebox.showwarning("Validation",
 "Select a valid member.")
 return
 if not amount:
 messagebox.showwarning("Validation",
 "Amount is required.")
 return
 try:
 amount = float(amount)
 except ValueError:
 messagebox.showwarning("Validation",
 "Amount must be a number.")
 return
 if amount <= 0:
 messagebox.showwarning("Validation",
 "Amount must be greater than 0.")
 return
 if not self.validate_date(pay_date):
 messagebox.showwarning("Validation",
 "Date must be in YYYY-MM-DD
 format.")
 return
 member_id = self._member_lookup[member_name]
 try:
 self.db.add_payment(member_id, amount,
 pay_date, self.pay_method.get())
 except mysql.connector.Error as err:
 messagebox.showerror("Database Error",
 str(err))
 return
 messagebox.showinfo("Success", "Payment
 recorded.")
 self.clear_payment_form()
 self.refresh_all()
 def on_payment_select(self, event):
 sel = self.payments_tree.selection()
 if not sel:
 return
 values = self.payments_tree.item(sel[0],
 "values")
 self.selected_payment_id = int(values[0])
 def delete_payment(self):
 if not self.selected_payment_id:
 messagebox.showwarning("Selection",
 "Select a payment from the table
 first.")
 return
 if messagebox.askyesno("Confirm", "Delete
 this payment record?"):
 self.db.delete_payment(self.selected_pay
 ment_id)
 self.clear_payment_form()
 self.refresh_all()
 def refresh_payments(self):
 for row in
 self.payments_tree.get_children():
 self.payments_tree.delete(row)
 for p in self.db.get_payments():
 pay_id, name, amount, pay_date, method,
 member_id = p
 self.payments_tree.insert("", "end",
 values=(pay_id, name,
 f"{float(amount):.2f}", pay_date,
 method or ""))
 self.stripe_rows(self.payments_tree)
 #
 --------------------------------------------
 -------------------
 # RENEWALS TAB
 #
 --------------------------------------------
 -------------------
 def build_renewals_tab(self):
 frame = self.renewals_tab
 info = ttk.Label(
 frame,
 text="Auto-calculated from Join Date +
 Plan Duration. "
 "OVERDUE = expired, DUE SOON =
 expires within 7 days.",
 wraplength=900, justify="left"
 )
 info.pack(anchor="w", padx=10, pady=(10, 5))
 ttk.Button(frame, text="Refresh",
 style="Accent.TButton",
 command=self.refresh_renewals).pa
 ck(anchor="w", padx=10,
 pady=(0, 5))
 cols = ("Member ID", "Name", "Phone",
 "Plan", "Expiry Date", "Days Left",
 "Status")
 self.renewals_tree = ttk.Treeview(frame,
 columns=cols, show="headings",
 height=16)
 for c in cols:
 self.renewals_tree.heading(c, text=c)
 self.renewals_tree.column(c, width=130,
 anchor="center")
 self.renewals_tree.pack(fill="both",
 expand=True, padx=10, pady=(0, 10))
 self.renewals_tree.tag_configure("overdue",
 background=COLORS["overdue"])
 self.renewals_tree.tag_configure("duesoon",
 background=COLORS["duesoon"])
 self.renewals_tree.tag_configure("active",
 background=COLORS["active"])
 def refresh_renewals(self):
 for row in
 self.renewals_tree.get_children():
 self.renewals_tree.delete(row)
 for r in self.db.get_renewals():
 m_id, name, phone, plan_name, expiry,
 days_left, status = r
 tag = {"OVERDUE": "overdue", "DUE
 SOON": "duesoon", "ACTIVE":
 "active"}[status]
 self.renewals_tree.insert("", "end",
 values=(m_id, name, phone or "",
 plan_name, expiry, days_left,
 status), tags=(tag,))
 #
 --------------------------------------------
 -------------------
 # GLOBAL REFRESH
 #
 --------------------------------------------
 -------------------
 def refresh_all(self):
 self.refresh_plan_combo()
 self.refresh_member_combo()
 self.refresh_members()
 self.refresh_plans()
 self.refresh_payments()
 self.refresh_renewals()
#
 ================================================
 ==================
# ENTRY POINT
#
 ================================================
 ==================
def main():
 root = tk.Tk()
 app = GymApp(root)
 root.mainloop()
if __name__ == "__main__":
 main()
   
