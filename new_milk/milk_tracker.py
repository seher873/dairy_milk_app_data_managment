import streamlit as st
import sqlite3
import pandas as pd
from dataclasses import dataclass
import datetime
from io import BytesIO
from fpdf import FPDF

# --------------------------- DATABASE SETUP --------------------------- #
class MilkDatabase:
    def __init__(self, db_name="milk_data.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                date_start TEXT,
                date_end TEXT,
                morning_mound REAL,
                morning_sair INTEGER,
                morning_rate REAL,
                evening_mound REAL,
                evening_sair INTEGER,
                evening_rate REAL,
                rent REAL,
                commission REAL,
                bandi REAL,
                paid_amount REAL
            )
        ''')
        self.conn.commit()

    def insert_entry(self, entry):
        self.cursor.execute('''
            INSERT INTO entries (
                customer_name, date_start, date_end,
                morning_mound, morning_sair, morning_rate,
                evening_mound, evening_sair, evening_rate,
                rent, commission, bandi, paid_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.customer_name, entry.date_start, entry.date_end,
            entry.morning_mound, entry.morning_sair, entry.morning_rate,
            entry.evening_mound, entry.evening_sair, entry.evening_rate,
            entry.rent, entry.commission, entry.bandi, entry.paid_amount))
        self.conn.commit()

    def fetch_all(self):
        self.cursor.execute("SELECT * FROM entries")
        return self.cursor.fetchall()

    def get_monthly_report(self, month):
        self.cursor.execute("SELECT * FROM entries WHERE strftime('%Y-%m', date_start) = ?", (month,))
        return self.cursor.fetchall()

    def get_daily_report(self, date):
        self.cursor.execute("SELECT * FROM entries WHERE date_start = ?", (date,))
        return self.cursor.fetchall()

# --------------------------- DATA STRUCTURE --------------------------- #
@dataclass
class MilkEntry:
    customer_name: str
    date_start: str
    date_end: str
    morning_mound: float
    morning_sair: int
    morning_rate: float
    evening_mound: float
    evening_sair: int
    evening_rate: float
    rent: float
    commission: float
    bandi: float
    paid_amount: float

# --------------------------- PDF UTILITY --------------------------- #
def generate_pdf(df, title="Milk Entry Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    col_width = pdf.w / (len(df.columns) + 1)
    for col in df.columns:
        pdf.cell(col_width, 10, col, border=1)
    pdf.ln()
    for i in range(len(df)):
        for item in df.iloc[i]:
            pdf.cell(col_width, 10, str(item), border=1)
        pdf.ln()

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes

# --------------------------- STREAMLIT APP --------------------------- #
def main():
    # Password protection section
    st.sidebar.title("🍼 Malik Dairy")
    password = st.sidebar.text_input("Enter Password", type="password")

    # Correct password (you can change this)
    correct_password = "obob"  # Change this to your desired password

    if password != correct_password:
        st.sidebar.warning("Please enter the correct password to access the app.")
        return  # Exit the app if the password is incorrect

    # Database connection and rest of the app logic
    db = MilkDatabase()

    choice = st.sidebar.selectbox("Select View", ["Home", "Add Entry", "Daily Report", "Monthly Report"])

    if choice == "Home":
        st.title("🌿 Malik Dairy - Dashboard")

        st.markdown("""
            <div style='padding:10px; background-color:#f1f3f5; border-radius:10px;'>
                <h3>Welcome to your Daily Milk Tracker 📒</h3>
                <p>Use the sidebar to add entries or generate reports easily.</p>
            </div>
        """, unsafe_allow_html=True)

        today = datetime.date.today().strftime("%Y-%m-%d")
        daily_data = db.get_daily_report(today)

        if daily_data:
            df = pd.DataFrame(daily_data, columns=[
                "ID", "Customer Name", "Start Date", "End Date",
                "Morning Mound", "Morning Sair", "Morning Rate",
                "Evening Mound", "Evening Sair", "Evening Rate",
                "Rent", "Commission", "Bandi", "Paid Amount"
            ])

            total_morning = df["Morning Mound"].sum()
            total_evening = df["Evening Mound"].sum()
            total_paid = df["Paid Amount"].sum()
            total_milk = total_morning + total_evening

            # Calculate average mandi rate
            mandi_rates = []
            for _, row in df.iterrows():
                milk_qty = row["Morning Mound"] + row["Evening Mound"]
                if milk_qty > 0:
                    total_payment = (row["Morning Mound"] * row["Morning Rate"]) + (row["Evening Mound"] * row["Evening Rate"])
                    mandi_rate = total_payment / milk_qty
                    mandi_rates.append(mandi_rate)

            avg_mandi_rate = sum(mandi_rates) / len(mandi_rates) if mandi_rates else 0

            st.markdown("### 📊 Today’s Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Morning Mound", f"{total_morning} M")
            col2.metric("Evening Mound", f"{total_evening} M")
            col3.metric("Total Milk", f"{total_milk} M")
            col4.metric("Avg. Mandi Rate", f"Rs {avg_mandi_rate:.2f}")
        else:
            st.info("No data found for today.")

    elif choice == "Add Entry":
        st.title("📥 Add Milk Entry")
        customer_name = st.text_input("Customer Name")
        date_start = st.date_input("Date Start")
        date_end = st.date_input("Date End")

        st.subheader("🌅 Morning")
        col1, col2, col3 = st.columns(3)
        morning_mound = col1.number_input("Milk Amount Morning (Mound)", 0.0)
        morning_sair = col2.number_input("Sair Morning", 0)
        morning_rate = col3.number_input("Rate Morning", 0.0)

        st.subheader("🌇 Evening")
        col4, col5, col6 = st.columns(3)
        evening_mound = col4.number_input("Milk Amount Evening (Mound)", 0.0)
        evening_sair = col5.number_input("Sair Evening", 0)
        evening_rate = col6.number_input("Rate Evening", 0.0)

        st.subheader("💰 Other Details")
        rent = st.number_input("Rent", 0.0)
        commission = st.number_input("Commission", 0.0)
        bandi = st.number_input("Bandi", 0.0)
        paid_amount = st.number_input("Paid Amount", 0.0)

        if st.button("Save Entry"):
            entry = MilkEntry(
                customer_name, str(date_start), str(date_end),
                morning_mound, morning_sair, morning_rate,
                evening_mound, evening_sair, evening_rate,
                rent, commission, bandi, paid_amount
            )
            db.insert_entry(entry)
            st.success("Entry added successfully!")

    elif choice == "Daily Report":
        st.title("📅 Daily Report")
        date = st.date_input("Select Date", datetime.date.today())
        daily_data = db.get_daily_report(str(date))
        if daily_data:
            df = pd.DataFrame(daily_data, columns=[
                "ID", "Customer Name", "Start Date", "End Date",
                "Morning Mound", "Morning Sair", "Morning Rate",
                "Evening Mound", "Evening Sair", "Evening Rate",
                "Rent", "Commission", "Bandi", "Paid Amount"
            ])

            df["Total Milk"] = df["Morning Mound"] + df["Evening Mound"]

            # Calculate totals
            total_morning = df["Morning Mound"].sum()
            total_evening = df["Evening Mound"].sum()
            total_paid = df["Paid Amount"].sum()
            total_milk = df["Total Milk"].sum()

            # Calculate average mandi rate
            mandi_rates = []
            for _, row in df.iterrows():
                milk_qty = row["Morning Mound"] + row["Evening Mound"]
                if milk_qty > 0:
                    total_payment = (row["Morning Mound"] * row["Morning Rate"]) + (row["Evening Mound"] * row["Evening Rate"])
                    mandi_rate = total_payment / milk_qty
                    mandi_rates.append(mandi_rate)

            avg_mandi_rate = sum(mandi_rates) / len(mandi_rates) if mandi_rates else 0

            st.markdown("### 📊 Daily Totals")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Morning Mound", f"{total_morning} M")
            col2.metric("Evening Mound", f"{total_evening} M")
            col3.metric("Total Milk", f"{total_milk} M")
            col4.metric("Avg. Mandi Rate", f"Rs {avg_mandi_rate:.2f}")

            st.dataframe(df)

            st.download_button("Download PDF", data=generate_pdf(df), file_name=f"daily_report_{date}.pdf")
        else:
            st.info("No data found for selected date.")

    elif choice == "Monthly Report":
        st.title("📅 Monthly Report")
        month = st.text_input("Enter Month (YYYY-MM)", datetime.date.today().strftime("%Y-%m"))
        monthly_data = db.get_monthly_report(month)

        if monthly_data:
            df = pd.DataFrame(monthly_data, columns=[
                "ID", "Customer Name", "Start Date", "End Date",
                "Morning Mound", "Morning Sair", "Morning Rate",
                "Evening Mound", "Evening Sair", "Evening Rate",
                "Rent", "Commission", "Bandi", "Paid Amount"
            ])
            st.dataframe(df)

            st.download_button("Download PDF", data=generate_pdf(df), file_name=f"monthly_report_{month}.pdf")
        else:
            st.info("No data found for selected month.")

if __name__ == "__main__":
    main()
