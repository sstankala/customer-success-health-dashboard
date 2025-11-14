# customer-success-health-dashboard
A practical Customer Success health dashboard I use to prioritize accounts and prep QBRs.
# Customer Success Health Dashboard

An interactive Streamlit dashboard to help Customer Success teams:

- Score account health using NPS, CSAT, usage, logins, and support tickets  
- Prioritize accounts by health band, renewal risk, and expansion potential  
- Generate recommended actions for QBRs/EBRs and renewal playbooks  

Built by **Sai Tankala – Sr. Customer Success & Service Experience Leader**.

---

## Features

- 📥 CSV upload (or use bundled `sample_data.csv`)
- 📊 Health scores (0–100) with Green / Yellow / Red bands
- 💰 ARR at risk & renewals in the next 180 days
- 🔍 Filters by Segment, Health Band, and Renewal Risk
- 🧠 Rule-based “AI-style” recommendations per account
- 📈 Visuals for health distribution and ARR by band

---

## Data model

The app expects these columns in the CSV:

- `Customer`
- `Segment` (Enterprise, Mid-Market, SMB, etc.)
- `ARR`
- `Renewal_Date` (YYYY-MM-DD)
- `NPS`
- `Tickets_Last_90d`
- `CSAT` (1–5)
- `Logins_Last_30d`
- `Active_Users`
- `Total_Seats`

A sample file is included as **`sample_data.csv`**.

---
Disclosure: Used chatgpt to create initial version. Tested and fixed minor defects to make it up and running

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/customer-success-health-dashboard.git
cd customer-success-health-dashboard

# 2. Create virtual env (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dashboard
streamlit run app.py
