from database import get_db, init_db
from auth import hash_password
from datetime import datetime, timedelta

SAMPLE_USERS = [
    {
        'username': 'admin',
        'password': 'Admin@2026!',
        'full_name': 'Aditya Verma (Chief Admin)',
        'role': 'Admin',
        'email': 'admin@aditya-enterprises.in'
    },
    {
        'username': 'inventory_mgr',
        'password': 'Inventory#2026',
        'full_name': 'Rajesh Patel (Stock Manager)',
        'role': 'Inventory Manager',
        'email': 'rajesh.stock@aditya-enterprises.in'
    },
    {
        'username': 'clerk_priya',
        'password': 'Billing$2026',
        'full_name': 'Priya Sharma (Billing Clerk)',
        'role': 'Billing Clerk',
        'email': 'priya.billing@aditya-enterprises.in'
    },
    {
        'username': 'store_rahul',
        'password': 'StoreKeeper*2026',
        'full_name': 'Rahul Sharma (Dispatch & Store)',
        'role': 'Storekeeper',
        'email': 'rahul.store@aditya-enterprises.in'
    }
]

SAMPLE_ITEMS = [
    # --- Fans ---
    {
        'sku': 'FAN-CRM-1200',
        'name': 'Crompton Aura Prime 1200mm Ceiling Fan (High Speed)',
        'category': 'Ceiling Fans',
        'unit': 'Pieces',
        'cost_price': 1850.00,
        'selling_price': 2450.00,
        'quantity': 28,
        'min_threshold': 8,
        'location': 'Aisle 1-A',
        'description': '3-blade 1200mm high speed aerodynamically balanced ceiling fan with 100% copper motor.'
    },
    {
        'sku': 'FAN-HAV-PED400',
        'name': 'Havells Swing LX 400mm Pedestal Standing Fan',
        'category': 'Standing Fans',
        'unit': 'Pieces',
        'cost_price': 2200.00,
        'selling_price': 2890.00,
        'quantity': 15,
        'min_threshold': 5,
        'location': 'Aisle 1-B',
        'description': '400mm sweep oscillating pedestal fan with 3-speed control and thermal overload protector.'
    },
    {
        'sku': 'FAN-USH-EXH300',
        'name': 'Usha Maxx Air 300mm Wall Mount Exhaust Fan',
        'category': 'Exhaust Fans',
        'unit': 'Pieces',
        'cost_price': 1150.00,
        'selling_price': 1550.00,
        'quantity': 22,
        'min_threshold': 6,
        'location': 'Aisle 1-C',
        'description': 'Heavy-duty metallic shutter exhaust fan for kitchens and commercial ventilation.'
    },
    {
        'sku': 'FAN-BLDC-REM12',
        'name': 'Orient Smart 1200mm BLDC Fan with Remote',
        'category': 'Ceiling Fans',
        'unit': 'Pieces',
        'cost_price': 2650.00,
        'selling_price': 3490.00,
        'quantity': 14,
        'min_threshold': 4,
        'location': 'Aisle 1-A',
        'description': 'Energy-saving 28W brushless DC motor with RF wireless remote and boost mode.'
    },
    {
        'sku': 'FAN-ATOM-REN12',
        'name': 'Atomberg Renesa 1200mm 5-Star BLDC Fan (Wood Finish)',
        'category': 'Ceiling Fans',
        'unit': 'Pieces',
        'cost_price': 3150.00,
        'selling_price': 4190.00,
        'quantity': 4,  # Intentionally low stock to showcase dynamics!
        'min_threshold': 6,
        'location': 'Aisle 1-A',
        'description': 'Premium wood finish BLDC ceiling fan with smart LED speed indicators.'
    },

    # --- Air Conditioners (ACs) ---
    {
        'sku': 'AC-DAIK-15T5S',
        'name': 'Daikin 1.5 Ton 5-Star Inverter Split AC (PM2.5 Filter)',
        'category': 'Air Conditioners',
        'unit': 'Pieces',
        'cost_price': 36500.00,
        'selling_price': 44990.00,
        'quantity': 8,
        'min_threshold': 3,
        'location': 'Warehouse Bay 3',
        'description': '1.5 ton split AC with copper condenser, Dew Clean technology, and PM 2.5 air filtration.'
    },
    {
        'sku': 'AC-VOLT-10T3S',
        'name': 'Voltas 1.0 Ton 3-Star Window AC (Copper Condenser)',
        'category': 'Air Conditioners',
        'unit': 'Pieces',
        'cost_price': 23500.00,
        'selling_price': 28990.00,
        'quantity': 6,
        'min_threshold': 2,
        'location': 'Warehouse Bay 3',
        'description': 'Compact 1-ton window air conditioner with turbo cooling and anti-bacterial mesh.'
    },
    {
        'sku': 'AC-LG-15T-DUAL',
        'name': 'LG 1.5 Ton Dual Inverter Split AC (6-in-1 AI Convertible)',
        'category': 'Air Conditioners',
        'unit': 'Pieces',
        'cost_price': 37500.00,
        'selling_price': 45990.00,
        'quantity': 11,
        'min_threshold': 4,
        'location': 'Warehouse Bay 3',
        'description': 'Dual inverter compressor with Ocean Black protection and smart diagnosis.'
    },
    {
        'sku': 'AC-BLUE-20T-INV',
        'name': 'Blue Star 2.0 Ton Heavy Duty Inverter Split AC',
        'category': 'Air Conditioners',
        'unit': 'Pieces',
        'cost_price': 49000.00,
        'selling_price': 59990.00,
        'quantity': 2,  # Low stock
        'min_threshold': 3,
        'location': 'Warehouse Bay 4',
        'description': '2.0 ton commercial grade cooling for large halls and conference rooms.'
    },

    # --- Lights & Luminaires ---
    {
        'sku': 'LGT-PHIL-LED9W',
        'name': 'Philips 9W Cool Day LED Bulb (B22 Base, Pack of 4)',
        'category': 'Lighting',
        'unit': 'Packs',
        'cost_price': 280.00,
        'selling_price': 399.00,
        'quantity': 110,
        'min_threshold': 25,
        'location': 'Aisle 2-A',
        'description': '825 Lumens energy-saving cool day white LED bulbs with surge protection up to 4kV.'
    },
    {
        'sku': 'LGT-SYS-TBAT20',
        'name': 'Syska 20W LED T-Bulb Batten (Angle Adjustable)',
        'category': 'Lighting',
        'unit': 'Pieces',
        'cost_price': 240.00,
        'selling_price': 349.00,
        'quantity': 55,
        'min_threshold': 15,
        'location': 'Aisle 2-B',
        'description': 'Unique swivel head T-bulb with wider light throw, 2000 lumens output.'
    },
    {
        'sku': 'LGT-WIP-PANEL15',
        'name': 'Wipro 15W Slim Round Concealed LED Downlight Panel',
        'category': 'Lighting',
        'unit': 'Pieces',
        'cost_price': 320.00,
        'selling_price': 450.00,
        'quantity': 45,
        'min_threshold': 12,
        'location': 'Aisle 2-C',
        'description': 'Ultra-slim die-cast aluminum ceiling concealed panel with flicker-free driver.'
    },
    {
        'sku': 'LGT-HAV-FLOOD50',
        'name': 'Havells 50W Outdoor Industrial LED Flood Light (IP66)',
        'category': 'Lighting',
        'unit': 'Pieces',
        'cost_price': 1450.00,
        'selling_price': 2150.00,
        'quantity': 16,
        'min_threshold': 5,
        'location': 'Aisle 2-D',
        'description': 'Heavy weatherproof IP66 floodlight for building facades, gardens, and security gates.'
    },
    {
        'sku': 'LGT-RGB-STRIP5M',
        'name': 'Smart RGB WiFi 5-Meter Ambient LED Strip Light',
        'category': 'Lighting',
        'unit': 'Rolls',
        'cost_price': 650.00,
        'selling_price': 999.00,
        'quantity': 32,
        'min_threshold': 8,
        'location': 'Aisle 2-E',
        'description': '16-million color adhesive strip light compatible with Alexa and Google Assistant.'
    },

    # --- Switches & Switchgear ---
    {
        'sku': 'SW-ANC-ROM6A',
        'name': 'Anchor Roma 6A 1-Way Modular Switch (Arctic White)',
        'category': 'Switches & Sockets',
        'unit': 'Pieces',
        'cost_price': 32.00,
        'selling_price': 48.00,
        'quantity': 240,
        'min_threshold': 50,
        'location': 'Aisle 3-A',
        'description': 'ISI marked fire-retardant polycarbonate modular click switch.'
    },
    {
        'sku': 'SW-SCH-SOCK16',
        'name': 'Schneider Electric 16A Power Socket with Safety Shutter',
        'category': 'Switches & Sockets',
        'unit': 'Pieces',
        'cost_price': 110.00,
        'selling_price': 165.00,
        'quantity': 115,
        'min_threshold': 25,
        'location': 'Aisle 3-A',
        'description': 'Heavy appliances socket rated for geysers, ACs, and microwaves with child safety.'
    },
    {
        'sku': 'SW-HAV-MCB32A',
        'name': 'Havells 32A Double Pole Miniature Circuit Breaker (MCB)',
        'category': 'Circuit Breakers',
        'unit': 'Pieces',
        'cost_price': 380.00,
        'selling_price': 560.00,
        'quantity': 32,
        'min_threshold': 10,
        'location': 'Aisle 3-C',
        'description': '10kA breaking capacity C-curve double pole circuit breaker for home distribution boards.'
    },
    {
        'sku': 'SW-LT-RCCB63A',
        'name': 'L&T 63A 4-Pole 30mA Residual Current Circuit Breaker (RCCB)',
        'category': 'Circuit Breakers',
        'unit': 'Pieces',
        'cost_price': 2400.00,
        'selling_price': 3250.00,
        'quantity': 8,
        'min_threshold': 3,
        'location': 'Aisle 3-C',
        'description': 'Life-saving earth leakage tripping RCCB for comprehensive electrocution safety.'
    },

    # --- Wires & Cables ---
    {
        'sku': 'WIR-POLY-15MM',
        'name': 'Polycab 1.5 sq mm Flame Retardant Copper Wire (90m Roll)',
        'category': 'Wires & Cables',
        'unit': 'Rolls',
        'cost_price': 1450.00,
        'selling_price': 1950.00,
        'quantity': 38,
        'min_threshold': 10,
        'location': 'Aisle 4-A',
        'description': 'Multi-strand 100% pure electrolytic copper wire with FR PVC insulation.'
    },
    {
        'sku': 'WIR-POLY-25MM',
        'name': 'Polycab 2.5 sq mm FR House Wire (90m Roll, Blue)',
        'category': 'Wires & Cables',
        'unit': 'Rolls',
        'cost_price': 2350.00,
        'selling_price': 3100.00,
        'quantity': 26,
        'min_threshold': 8,
        'location': 'Aisle 4-A',
        'description': 'Rated for power plugs, refrigerators, and heavy continuous residential loads.'
    },
    {
        'sku': 'WIR-FIN-40MM',
        'name': 'Finolex 4.0 sq mm Heavy Duty Cable (90m Roll, Black)',
        'category': 'Wires & Cables',
        'unit': 'Rolls',
        'cost_price': 3600.00,
        'selling_price': 4750.00,
        'quantity': 3,  # Low stock
        'min_threshold': 5,
        'location': 'Aisle 4-B',
        'description': 'Industrial grade high current conductor for air conditioning loops and sub-panels.'
    },

    # --- Stabilizers & Power ---
    {
        'sku': 'PWR-VGUARD-400',
        'name': 'V-Guard VG 400 Voltage Stabilizer for 1.5 Ton AC',
        'category': 'Stabilizers & Power',
        'unit': 'Pieces',
        'cost_price': 2100.00,
        'selling_price': 2850.00,
        'quantity': 15,
        'min_threshold': 4,
        'location': 'Aisle 5-A',
        'description': 'Automatic voltage stabilizer working from 160V to 280V with intelligent time delay.'
    },
    {
        'sku': 'PWR-MICRO-5KVA',
        'name': 'Microtek EML 5090 Digital Mainline Voltage Stabilizer (5kVA)',
        'category': 'Stabilizers & Power',
        'unit': 'Pieces',
        'cost_price': 7800.00,
        'selling_price': 10500.00,
        'quantity': 5,
        'min_threshold': 2,
        'location': 'Aisle 5-B',
        'description': 'Heavy 5kVA digital stabilizer with multi-stage relay regulation for entire homes.'
    }
]

def seed_database():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if users already seeded
        cursor.execute("SELECT COUNT(*) as cnt FROM users")
        if cursor.fetchone()['cnt'] == 0:
            print("Seeding finite set of secured users...")
            for u in SAMPLE_USERS:
                pw_hash = hash_password(u['password'])
                cursor.execute(
                    """INSERT INTO users (username, password_hash, full_name, role, email) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (u['username'], pw_hash, u['full_name'], u['role'], u['email'])
                )
            print("Users seeded successfully.")

        # Check if items already seeded
        cursor.execute("SELECT COUNT(*) as cnt FROM items")
        if cursor.fetchone()['cnt'] == 0:
            print("Seeding sample electrical inventory...")
            for itm in SAMPLE_ITEMS:
                cursor.execute(
                    """INSERT INTO items (sku, name, category, unit, cost_price, selling_price, quantity, min_threshold, location, description)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (itm['sku'], itm['name'], itm['category'], itm['unit'], itm['cost_price'],
                     itm['selling_price'], itm['quantity'], itm['min_threshold'], itm['location'], itm['description'])
                )
                item_id = cursor.lastrowid
                
                # Log initial inventory baseline
                cursor.execute(
                    """INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item_id, itm['name'], itm['sku'], 'INITIAL_STOCK', itm['quantity'], 0, itm['quantity'], 'INIT-SETUP', itm['cost_price'], 'System Admin', 'Initial warehouse stock import')
                )
            print("Items seeded successfully.")

            # Create sample purchase restock bill to demonstrate dynamic inward billing
            cursor.execute("SELECT id, name, sku, cost_price FROM items WHERE sku = 'FAN-CRM-1200'")
            fan = cursor.fetchone()
            if fan:
                bill_no = "BILL-SUP-20261015-01"
                added_qty = 10
                tot = added_qty * fan['cost_price']
                cursor.execute(
                    """INSERT INTO purchase_bills (bill_number, supplier_name, supplier_invoice_ref, item_id, quantity_added, unit_purchase_cost, total_bill_amount, notes, received_by_name, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-3 days'))""",
                    (bill_no, 'Crompton Greaves Consumer Electricals Ltd (Mumbai Depot)', 'CG-INV-2026-9941', fan['id'], added_qty, fan['cost_price'], tot, 'Scheduled monthly restock batch - GST E-way bill verified', 'Rajesh Patel')
                )

            # Create sample sales invoice to demonstrate dynamic outward billing
            cursor.execute("SELECT id, name, sku, selling_price FROM items WHERE sku = 'AC-DAIK-15T5S'")
            ac = cursor.fetchone()
            cursor.execute("SELECT id, name, sku, selling_price FROM items WHERE sku = 'PWR-VGUARD-400'")
            stab = cursor.fetchone()

            if ac and stab:
                inv_no = "INV-20261017-001"
                subtotal = (1 * ac['selling_price']) + (1 * stab['selling_price'])
                tax = round(subtotal * 0.18, 2)
                discount = 1500.00
                grand = subtotal + tax - discount
                cursor.execute(
                    """INSERT INTO invoices (invoice_number, customer_name, customer_phone, customer_email, customer_address, payment_method, subtotal, tax_rate, tax_amount, discount_amount, grand_total, notes, created_by_name, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-1 days'))""",
                    (inv_no, 'Sharma Electricals & Commercial Projects', '+91 98450 12345', 'accounts@sharmaelectricals.in', '#42, 3rd Phase, Peenya Industrial Area, Bengaluru, Karnataka - 560058', 'UPI / QR Payment', subtotal, 18.0, tax, discount, grand, 'HVAC split AC and voltage stabilizer for commercial facility installation', 'Priya Sharma')
                )
                inv_id = cursor.lastrowid
                
                cursor.execute(
                    """INSERT INTO invoice_items (invoice_id, item_id, item_name, item_sku, quantity, unit_price, total_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (inv_id, ac['id'], ac['name'], ac['sku'], 1, ac['selling_price'], ac['selling_price'])
                )
                cursor.execute(
                    """INSERT INTO invoice_items (invoice_id, item_id, item_name, item_sku, quantity, unit_price, total_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (inv_id, stab['id'], stab['name'], stab['sku'], 1, stab['selling_price'], stab['selling_price'])
                )

                # Log the sale in inventory audit trail
                cursor.execute(
                    """INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-1 days'))""",
                    (ac['id'], ac['name'], ac['sku'], 'SALE', -1, 9, 8, inv_no, ac['selling_price'], 'Priya Sharma', 'Customer order fulfilled')
                )
                cursor.execute(
                    """INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-1 days'))""",
                    (stab['id'], stab['name'], stab['sku'], 'SALE', -1, 16, 15, inv_no, stab['selling_price'], 'Priya Sharma', 'Customer order fulfilled')
                )

            print("Sample bills and transactions seeded successfully.")

if __name__ == '__main__':
    seed_database()
