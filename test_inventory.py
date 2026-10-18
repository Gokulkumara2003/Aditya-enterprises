import unittest
import sys
import os
import time

# Add inventory_system directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import get_db

class InventorySystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_01_login_credentials(self):
        """Test finite user authentication with valid and invalid credentials"""
        # Failed login
        res = self.login('admin', 'WrongPassword123')
        self.assertIn(b"Invalid username or password", res.data)

        # Successful admin login
        res = self.login('admin', 'Admin@2026!')
        self.assertIn(b"Inventory Dynamics & Operations", res.data)
        self.assertIn(b"Eleanor Vance", res.data)

        # Successful clerk login
        res = self.login('clerk_sarah', 'Billing$2026')
        self.assertIn(b"Sarah Connor", res.data)
        self.assertIn(b"Billing Clerk", res.data)

    def test_02_dashboard_and_seeded_items(self):
        """Test that seeded electrical equipment items are present and dynamic metrics calculate"""
        self.login('admin', 'Admin@2026!')
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Active Catalog", res.data)
        self.assertIn(b"Ceiling Fans", res.data)
        self.assertIn(b"Air Conditioners", res.data)
        self.assertIn(b"Lighting", res.data)

    def test_03_add_new_item(self):
        """Test adding a brand new electrical item with unique SKU"""
        self.login('admin', 'Admin@2026!')
        unique_suffix = int(time.time() * 1000) % 100000
        new_sku = f'FAN-AERO-{unique_suffix}'
        res = self.client.post('/items/new', data=dict(
            sku=new_sku,
            name='Orient Aeroquiet 1200mm Silent Ceiling Fan',
            category='Ceiling Fans',
            unit='Pieces',
            cost_price='48.00',
            selling_price='68.00',
            quantity='15',
            min_threshold='5',
            location='Aisle 1-D',
            description='Aerodynamic PU finish curved blade super silent ceiling fan'
        ), follow_redirects=True)

        self.assertIn(b"added successfully", res.data)

        # Verify in database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items WHERE sku = ?", (new_sku,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row['quantity'], 15)
            self.assertEqual(row['selling_price'], 68.00)

    def test_04_restock_existing_item(self):
        """Test replenishing an existing item with inward purchase bill"""
        self.login('inventory_mgr', 'Inventory#2026')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, quantity, cost_price FROM items WHERE sku = 'FAN-CRM-1200'")
            item = cursor.fetchone()
            item_id = item['id']
            initial_qty = item['quantity']

        # Restock 10 units
        res = self.client.post('/restock', data=dict(
            item_id=item_id,
            quantity_added='10',
            unit_purchase_cost='41.50',
            supplier_name='Crompton National Warehousing',
            supplier_invoice_ref='CNW-2026-OCT-88',
            update_cost_price='yes',
            notes='Pre-festival inventory replenishment batch'
        ), follow_redirects=True)

        self.assertIn(b"Inward Purchase Bill #", res.data)

        # Verify stock increment
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantity, cost_price FROM items WHERE id = ?", (item_id,))
            updated_item = cursor.fetchone()
            self.assertEqual(updated_item['quantity'], initial_qty + 10)
            self.assertEqual(updated_item['cost_price'], 41.50)

    def test_05_customer_billing_and_stock_removal(self):
        """Test removing stock with customer invoice and tax calculations"""
        self.login('clerk_sarah', 'Billing$2026')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, quantity, selling_price FROM items WHERE sku = 'LGT-PHIL-LED9W'")
            bulb = cursor.fetchone()
            bulb_initial_qty = bulb['quantity']

        # Create invoice for 2 packs
        res = self.client.post('/billing', data={
            'customer_name': 'Horizon Electrical Contractors',
            'customer_phone': '+1 (555) 987-6543',
            'customer_email': 'procurement@horizonelec.com',
            'customer_address': '45 Industrial Blvd, Sector 8',
            'payment_method': 'Credit Card',
            'tax_rate': '18.0',
            'discount_amount': '2.50',
            'item_id[]': [str(bulb['id'])],
            'quantity[]': ['2'],
            'unit_price[]': [str(bulb['selling_price'])],
            'notes': 'Supplied for office floor lighting renovation'
        }, follow_redirects=True)

        self.assertIn(b"ORIGINAL TAX INVOICE", res.data)
        self.assertIn(b"Horizon Electrical Contractors", res.data)

        # Verify stock decrement
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM items WHERE id = ?", (bulb['id'],))
            updated_bulb = cursor.fetchone()
            self.assertEqual(updated_bulb['quantity'], bulb_initial_qty - 2)

    def test_06_audit_trail_recorded(self):
        """Test that all operations created immutable audit ledger entries"""
        self.login('admin', 'Admin@2026!')
        res = self.client.get('/audit')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Inventory Audit Trail", res.data)
        self.assertIn(b"RESTOCK", res.data)
        self.assertIn(b"SALE", res.data)

if __name__ == '__main__':
    unittest.main()
