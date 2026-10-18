# ElectroVault - Electrical Inventory Management & Billing System

A robust, full-featured Inventory Management and Billing Web Application built with **Python (Flask)**, **SQLite**, and **Bootstrap 5**.

---

## ⚡ Key Highlights & Features

1. **Finite Set of Authorized Users with Secured Credentials**:
   - Closed-perimeter access control with cryptographically hashed passwords (`werkzeug.security`).
   - Role-Based Access Control (RBAC):
     - **Admin** (`admin`): Full warehouse control, catalog deletions, auditing.
     - **Inventory Manager** (`inventory_mgr`): SKU creation, restock bills, catalog management.
     - **Billing Clerk** (`clerk_sarah`): Customer invoicing, point of sale, dispatch receipts.
     - **Storekeeper** (`store_rahul`): Inward shipment receiving, storage allocation.
   - Interactive 1-click Quick-Fill login panel on the login page for testing.

2. **Add New Items (Product Registration)**:
   - Form to register brand new equipment SKUs.
   - Captures SKU, Model Name, Category, Unit, Cost Price, Selling Price, Starting Stock, Min Alert Threshold, Warehouse Bay/Aisle, and Technical Specifications.
   - Automatic generation of `NEW_ITEM` audit ledger entries.

3. **Add Existing Items (Restock with Inward Purchase Bills)**:
   - Replenish existing products with supplier purchase documentation.
   - Automatically logs supplier name, supplier reference bill number, units received, unit purchase cost, and total inward purchase bill amount.
   - Instant live calculation of total inward purchase bill.
   - Updates stock count and optionally updates standard purchase cost basis.
   - View complete inward restock history in dedicated ledger.

4. **Remove Existing Items with Appropriate Billings (Outward Sales & Invoicing)**:
   - Dynamic Point of Sale / Billing Terminal.
   - Multi-item cart with live stock level checking (prevents overselling beyond current warehouse stock).
   - Real-time calculations: Subtotal, GST/Tax rate (configurable, default 18%), Trade Discounts, Grand Total Net Payable.
   - Customer details: Name, phone, email, delivery address, payment method (Cash, Card, UPI, Wire, Net 30).
   - Generates formal, unique Tax Invoices (`INV-YYYYMMDD-XXXX`).
   - Deducts stock immediately upon bill finalization and records audit entries.
   - **Professional Printable Invoice**: Formatted for browser printing (`Ctrl+P` / Print Bill button) with print-optimized CSS hiding navigation and interface clutter.

5. **Electrical Equipment Dynamics & Seed Data**:
   - Seeded with realistic, high-fidelity electrical items across categories:
     - **Ceiling & Exhaust Fans**: Crompton Aura Prime 1200mm, Havells Pedestal Standing Fan, Usha Maxx Air Exhaust Fan, Orient Smart BLDC Fan, Atomberg Renesa BLDC Fan.
     - **Air Conditioners (ACs)**: Daikin 1.5 Ton 5-Star Inverter Split AC, Voltas 1.0 Ton Window AC, LG 1.5 Ton Dual Inverter Split AC, Blue Star 2.0 Ton Inverter AC.
     - **Lighting**: Philips 9W Cool Day LED Bulbs, Syska 20W LED T-Bulb Battens, Wipro 15W Slim LED Downlights, Havells 50W Outdoor IP66 Flood Lights, Smart RGB 5M Strip Lights.
     - **Switches & Switchgear**: Anchor Roma 6A Modular Switches, Schneider Electric 16A Power Sockets, Havells 32A Double Pole MCBs, L&T 63A 4-Pole RCCBs.
     - **Wires & Cables**: Polycab 1.5 sq mm FR Wire, Polycab 2.5 sq mm FR Cable, Finolex 4.0 sq mm Industrial Cable.
     - **Stabilizers & Power**: V-Guard VG 400 AC Stabilizer, Microtek 5kVA Digital Mainline Stabilizer.

6. **Real-time Inventory Dynamics & Auditing**:
   - Dynamic Dashboard with live KPI counters: Active SKUs, Total Units In Stock, Valuation at Retail & Cost basis, Critical Low Stock Alerts, Billed Sales Revenue.
   - Visual category distribution and valuation progress bars.
   - Immutable audit trail recording every transaction (Sales, Restocks, New SKUs, Detail Updates).

---

## 🔐 Finite Authorized User Credentials

| Username | Password | Full Name | Role |
| :--- | :--- | :--- | :--- |
| `admin` | `Admin@2026!` | Eleanor Vance | System Administrator |
| `inventory_mgr` | `Inventory#2026` | Marcus Brody | Inventory Manager |
| `clerk_sarah` | `Billing$2026` | Sarah Connor | Billing & Sales Clerk |
| `store_rahul` | `StoreKeeper*2026` | Rahul Sharma | Storekeeper & Dispatch |

---

## 🚀 How to Run

From the terminal:

```bash
# Using Python with Flask installed:
python inventory_system\run.py
```

Or using the workspace virtual environment:

```powershell
.venv\Scripts\python.exe inventory_system\run.py
```

Then open your browser at:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Automated Test Suite

A complete verification suite is included:

```powershell
.venv\Scripts\python.exe inventory_system\test_inventory.py -v
```

All 6 test cases verify authentication, inventory dynamics, adding new items, restock purchase billing, customer sales invoicing with stock deductions, and audit trail ledger generation.
