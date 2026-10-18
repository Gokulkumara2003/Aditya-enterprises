import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import get_db, init_db
from auth import hash_password, verify_password, login_required, roles_required, get_current_user
from seed_data import seed_database

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'electrovault-super-secure-key-2026-xyz987')

# Ensure database is initialized and seeded on start
with app.app_context():
    seed_database()

@app.context_processor
def inject_globals():
    user = get_current_user()
    low_stock_count = 0
    if user:
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as cnt FROM items WHERE quantity <= min_threshold")
                low_stock_count = cursor.fetchone()['cnt']
        except Exception:
            low_stock_count = 0
    return {
        'current_user': user,
        'low_stock_count': low_stock_count,
        'now': datetime.now()
    }

# ================= AUTHENTICATION ROUTES =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user and verify_password(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                session['user_role'] = user['role']
                
                # Update last login
                cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
                flash(f"Welcome back, {user['full_name']}! Authenticated as {user['role']}.", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password. Please verify your credentials.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('login'))

# ================= DASHBOARD & DYNAMICS =================

@app.route('/')
@login_required
def dashboard():
    with get_db() as conn:
        cursor = conn.cursor()

        # Overall inventory metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_skus,
                COALESCE(SUM(quantity), 0) as total_units,
                COALESCE(SUM(quantity * cost_price), 0.0) as total_cost_valuation,
                COALESCE(SUM(quantity * selling_price), 0.0) as total_retail_valuation
            FROM items
        """)
        stats = dict(cursor.fetchone())

        # Low stock count
        cursor.execute("SELECT COUNT(*) as cnt FROM items WHERE quantity <= min_threshold")
        stats['low_stock_count'] = cursor.fetchone()['cnt']

        # Sales and Billing metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(grand_total), 0.0) as gross_revenue
            FROM invoices
        """)
        inv_stats = cursor.fetchone()
        stats['total_invoices'] = inv_stats['total_invoices']
        stats['gross_revenue'] = inv_stats['gross_revenue']

        # Purchase Bills metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bills,
                COALESCE(SUM(total_bill_amount), 0.0) as gross_purchases
            FROM purchase_bills
        """)
        pb_stats = cursor.fetchone()
        stats['total_purchase_bills'] = pb_stats['total_bills']
        stats['gross_purchases'] = pb_stats['gross_purchases']

        # Low Stock Alert list (Top 6)
        cursor.execute("""
            SELECT id, sku, name, category, quantity, min_threshold, unit, selling_price
            FROM items 
            WHERE quantity <= min_threshold
            ORDER BY quantity ASC
            LIMIT 6
        """)
        low_stock_items = [dict(r) for r in cursor.fetchall()]

        # Category distribution breakdown
        cursor.execute("""
            SELECT category, COUNT(*) as item_count, SUM(quantity) as units, SUM(quantity * selling_price) as category_value
            FROM items
            GROUP BY category
            ORDER BY category_value DESC
        """)
        categories = [dict(r) for r in cursor.fetchall()]

        # Recent 5 Invoices
        cursor.execute("""
            SELECT id, invoice_number, customer_name, payment_method, grand_total, created_at, created_by_name
            FROM invoices
            ORDER BY id DESC
            LIMIT 5
        """)
        recent_invoices = [dict(r) for r in cursor.fetchall()]

        # Recent 8 Inventory Audit Logs
        cursor.execute("""
            SELECT action_type, item_name, item_sku, quantity_change, previous_stock, new_stock, reference_id, user_name, created_at
            FROM inventory_logs
            ORDER BY id DESC
            LIMIT 8
        """)
        recent_logs = [dict(r) for r in cursor.fetchall()]

    return render_template(
        'dashboard.html',
        stats=stats,
        low_stock_items=low_stock_items,
        categories=categories,
        recent_invoices=recent_invoices,
        recent_logs=recent_logs
    )

# ================= INVENTORY & ITEM MANAGEMENT =================

@app.route('/inventory')
@login_required
def inventory_list():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    filter_status = request.args.get('status', 'all')

    sql = "SELECT * FROM items WHERE 1=1"
    params = []

    if query:
        sql += " AND (name LIKE ? OR sku LIKE ? OR description LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if filter_status == 'low_stock':
        sql += " AND quantity <= min_threshold AND quantity > 0"
    elif filter_status == 'out_of_stock':
        sql += " AND quantity <= 0"
    elif filter_status == 'in_stock':
        sql += " AND quantity > min_threshold"

    sql += " ORDER BY name ASC"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        items = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category ASC")
        all_categories = [r['category'] for r in cursor.fetchall()]

    return render_template(
        'inventory.html',
        items=items,
        categories=all_categories,
        query=query,
        selected_category=category,
        filter_status=filter_status
    )

@app.route('/items/new', methods=['GET', 'POST'])
@login_required
def add_new_item():
    if request.method == 'POST':
        sku = request.form.get('sku', '').strip().upper()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        custom_category = request.form.get('custom_category', '').strip()
        if custom_category:
            category = custom_category

        unit = request.form.get('unit', 'Pieces').strip()
        try:
            cost_price = float(request.form.get('cost_price', 0))
            selling_price = float(request.form.get('selling_price', 0))
            quantity = int(request.form.get('quantity', 0))
            min_threshold = int(request.form.get('min_threshold', 5))
        except ValueError:
            flash("Please enter valid numerical values for prices and stock counts.", "danger")
            return redirect(url_for('add_new_item'))

        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        if not sku or not name or not category:
            flash("SKU, Item Name, and Category are required.", "danger")
            return redirect(url_for('add_new_item'))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM items WHERE sku = ?", (sku,))
            if cursor.fetchone():
                flash(f"SKU '{sku}' already exists in inventory. Please use a unique SKU or restock the existing item.", "danger")
                return redirect(url_for('add_new_item'))

            cursor.execute("""
                INSERT INTO items (sku, name, category, unit, cost_price, selling_price, quantity, min_threshold, location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sku, name, category, unit, cost_price, selling_price, quantity, min_threshold, location, description))
            item_id = cursor.lastrowid

            # Audit Log
            user_name = session.get('full_name', 'Authorized User')
            cursor.execute("""
                INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes)
                VALUES (?, ?, ?, 'NEW_ITEM', ?, 0, ?, 'NEW-SKU-ADD', ?, ?, ?)
            """, (item_id, name, sku, quantity, quantity, cost_price, user_name, f"Initial stock registered: {description[:60]}"))

            flash(f"New item '{name}' (SKU: {sku}) added successfully with {quantity} {unit}!", "success")
            return redirect(url_for('inventory_list'))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category ASC")
        categories = [r['category'] for r in cursor.fetchall()]

    return render_template('item_form.html', item=None, categories=categories, mode='add')

@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            flash("Item not found.", "danger")
            return redirect(url_for('inventory_list'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            category = request.form.get('category', '').strip()
            custom_category = request.form.get('custom_category', '').strip()
            if custom_category:
                category = custom_category

            unit = request.form.get('unit', 'Pieces').strip()
            try:
                cost_price = float(request.form.get('cost_price', item['cost_price']))
                selling_price = float(request.form.get('selling_price', item['selling_price']))
                min_threshold = int(request.form.get('min_threshold', item['min_threshold']))
            except ValueError:
                flash("Invalid price or threshold value.", "danger")
                return redirect(url_for('edit_item', item_id=item_id))

            location = request.form.get('location', '').strip()
            description = request.form.get('description', '').strip()

            cursor.execute("""
                UPDATE items 
                SET name = ?, category = ?, unit = ?, cost_price = ?, selling_price = ?, min_threshold = ?, location = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, category, unit, cost_price, selling_price, min_threshold, location, description, item_id))

            user_name = session.get('full_name', 'Authorized User')
            cursor.execute("""
                INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes)
                VALUES (?, ?, ?, 'UPDATE_DETAILS', 0, ?, ?, 'INFO-EDIT', ?, ?, 'Item details and pricing updated')
            """, (item_id, name, item['sku'], item['quantity'], item['quantity'], selling_price, user_name))

            flash(f"Item '{name}' updated successfully.", "success")
            return redirect(url_for('inventory_list'))

        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category ASC")
        categories = [r['category'] for r in cursor.fetchall()]

    return render_template('item_form.html', item=dict(item), categories=categories, mode='edit')

@app.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin', 'Inventory Manager')
def delete_item(item_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            flash("Item not found.", "danger")
            return redirect(url_for('inventory_list'))

        user_name = session.get('full_name', 'Authorized User')
        cursor.execute("""
            INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes)
            VALUES (?, ?, ?, 'DELETE', ?, ?, 0, 'ITEM-DELETED', ?, ?, 'Item permanently removed from catalog')
        """, (item['id'], item['name'], item['sku'], -item['quantity'], item['quantity'], item['cost_price'], user_name))

        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        flash(f"Item '{item['name']}' (SKU: {item['sku']}) deleted.", "info")

    return redirect(url_for('inventory_list'))

# ================= ADD EXISTING ITEMS (RESTOCK WITH BILLING) =================

@app.route('/restock', methods=['GET', 'POST'])
@login_required
def restock_item():
    preselect_id = request.args.get('item_id', type=int)

    if request.method == 'POST':
        item_id = request.form.get('item_id', type=int)
        try:
            quantity_added = int(request.form.get('quantity_added', 0))
            unit_purchase_cost = float(request.form.get('unit_purchase_cost', 0))
        except ValueError:
            flash("Invalid quantity or purchase cost.", "danger")
            return redirect(url_for('restock_item', item_id=item_id))

        supplier_name = request.form.get('supplier_name', '').strip()
        supplier_invoice_ref = request.form.get('supplier_invoice_ref', '').strip()
        notes = request.form.get('notes', '').strip()
        update_cost_price = request.form.get('update_cost_price') == 'yes'

        if not item_id or quantity_added <= 0 or not supplier_name:
            flash("Please provide a valid item, positive quantity, and supplier name.", "danger")
            return redirect(url_for('restock_item', item_id=item_id))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            item = cursor.fetchone()
            if not item:
                flash("Selected item does not exist.", "danger")
                return redirect(url_for('restock_item'))

            # Generate unique restock bill number
            bill_date_str = datetime.now().strftime("%Y%m%d")
            random_suffix = random.randint(1000, 9999)
            bill_number = f"BILL-RESTOCK-{bill_date_str}-{random_suffix}"
            total_bill_amount = round(quantity_added * unit_purchase_cost, 2)

            prev_stock = item['quantity']
            new_stock = prev_stock + quantity_added

            # Insert inward purchase bill
            user_name = session.get('full_name', 'Authorized User')
            user_id = session.get('user_id')
            cursor.execute("""
                INSERT INTO purchase_bills (bill_number, supplier_name, supplier_invoice_ref, item_id, quantity_added, unit_purchase_cost, total_bill_amount, notes, received_by_user_id, received_by_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (bill_number, supplier_name, supplier_invoice_ref, item_id, quantity_added, unit_purchase_cost, total_bill_amount, notes, user_id, user_name))

            # Update item stock and optionally cost price
            if update_cost_price and unit_purchase_cost > 0:
                cursor.execute("""
                    UPDATE items 
                    SET quantity = ?, cost_price = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (new_stock, unit_purchase_cost, item_id))
            else:
                cursor.execute("""
                    UPDATE items 
                    SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (new_stock, item_id))

            # Audit log
            cursor.execute("""
                INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes)
                VALUES (?, ?, ?, 'RESTOCK', ?, ?, ?, ?, ?, ?, ?)
            """, (item['id'], item['name'], item['sku'], quantity_added, prev_stock, new_stock, bill_number, unit_purchase_cost, user_name, f"Restocked via {supplier_name} (Supplier Ref: {supplier_invoice_ref or 'N/A'})"))

            flash(f"Restocked {quantity_added} {item['unit']} of '{item['name']}'! Inward Purchase Bill #{bill_number} generated.", "success")
            return redirect(url_for('restock_history'))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, sku, name, category, unit, cost_price, selling_price, quantity, min_threshold FROM items ORDER BY name ASC")
        items = [dict(r) for r in cursor.fetchall()]

    return render_template('restock.html', items=items, preselect_id=preselect_id)

@app.route('/restock/history')
@login_required
def restock_history():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pb.*, i.name as item_name, i.sku as item_sku, i.unit as item_unit
            FROM purchase_bills pb
            LEFT JOIN items i ON pb.item_id = i.id
            ORDER BY pb.id DESC
        """)
        bills = [dict(r) for r in cursor.fetchall()]

    return render_template('restock_history.html', bills=bills)

# ================= REMOVE EXISTING ITEMS (BILLING & SALES) =================

@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        customer_address = request.form.get('customer_address', '').strip()
        payment_method = request.form.get('payment_method', 'Cash')
        notes = request.form.get('notes', '').strip()

        try:
            tax_rate = float(request.form.get('tax_rate', 18.0))
            discount_amount = float(request.form.get('discount_amount', 0.0))
        except ValueError:
            tax_rate = 18.0
            discount_amount = 0.0

        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')

        if not customer_name:
            flash("Customer Name is required for billing.", "danger")
            return redirect(url_for('billing'))

        if not item_ids or len(item_ids) == 0:
            flash("Please add at least one item to generate a bill.", "danger")
            return redirect(url_for('billing'))

        # Prepare line items and validate stock
        line_items_data = []
        with get_db() as conn:
            cursor = conn.cursor()

            subtotal = 0.0
            for idx, raw_id in enumerate(item_ids):
                if not raw_id:
                    continue
                try:
                    i_id = int(raw_id)
                    qty = int(quantities[idx])
                    u_price = float(unit_prices[idx])
                except (ValueError, IndexError):
                    continue

                if qty <= 0:
                    continue

                cursor.execute("SELECT * FROM items WHERE id = ?", (i_id,))
                item = cursor.fetchone()
                if not item:
                    flash(f"Item #{i_id} not found in inventory.", "danger")
                    return redirect(url_for('billing'))

                if item['quantity'] < qty:
                    flash(f"Insufficient stock for '{item['name']}'. Requested: {qty}, Available: {item['quantity']}.", "danger")
                    return redirect(url_for('billing'))

                line_total = round(qty * u_price, 2)
                subtotal += line_total
                line_items_data.append({
                    'item': item,
                    'quantity': qty,
                    'unit_price': u_price,
                    'line_total': line_total
                })

            if not line_items_data:
                flash("No valid line items specified with quantity > 0.", "danger")
                return redirect(url_for('billing'))

            tax_amount = round(subtotal * (tax_rate / 100.0), 2)
            grand_total = max(0.0, round(subtotal + tax_amount - discount_amount, 2))

            # Generate invoice number
            inv_date_str = datetime.now().strftime("%Y%m%d")
            cursor.execute("SELECT COUNT(*) as cnt FROM invoices WHERE invoice_number LIKE ?", (f"INV-{inv_date_str}%",))
            daily_count = cursor.fetchone()['cnt'] + 1
            invoice_number = f"INV-{inv_date_str}-{daily_count:04d}"

            user_name = session.get('full_name', 'Authorized User')
            user_id = session.get('user_id')

            # Insert Invoice record
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, customer_name, customer_phone, customer_email, 
                    customer_address, payment_method, subtotal, tax_rate, tax_amount, 
                    discount_amount, grand_total, notes, created_by_user_id, created_by_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_number, customer_name, customer_phone, customer_email,
                customer_address, payment_method, subtotal, tax_rate, tax_amount,
                discount_amount, grand_total, notes, user_id, user_name
            ))
            invoice_id = cursor.lastrowid

            # Insert line items and deduct inventory
            for line in line_items_data:
                itm = line['item']
                qty = line['quantity']
                u_price = line['unit_price']
                tot = line['line_total']

                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, item_id, item_name, item_sku, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (invoice_id, itm['id'], itm['name'], itm['sku'], qty, u_price, tot))

                # Deduct stock
                prev_stock = itm['quantity']
                new_stock = prev_stock - qty
                cursor.execute("UPDATE items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_stock, itm['id']))

                # Audit log
                cursor.execute("""
                    INSERT INTO inventory_logs (item_id, item_name, item_sku, action_type, quantity_change, previous_stock, new_stock, reference_id, unit_price, user_name, notes)
                    VALUES (?, ?, ?, 'SALE', ?, ?, ?, ?, ?, ?, ?)
                """, (itm['id'], itm['name'], itm['sku'], -qty, prev_stock, new_stock, invoice_number, u_price, user_name, f"Customer billing: {customer_name}"))

            flash(f"Invoice #{invoice_number} created successfully! Stock deducted and bill finalized.", "success")
            return redirect(url_for('view_invoice', invoice_id=invoice_id))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, sku, name, category, unit, selling_price, quantity FROM items WHERE quantity > 0 ORDER BY name ASC")
        available_items = [dict(r) for r in cursor.fetchall()]

    return render_template('billing.html', available_items=available_items)

@app.route('/invoices')
@login_required
def invoice_list():
    query = request.args.get('q', '').strip()
    sql = "SELECT * FROM invoices WHERE 1=1"
    params = []
    if query:
        sql += " AND (invoice_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term])

    sql += " ORDER BY id DESC"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        invoices = [dict(r) for r in cursor.fetchall()]

        # Attach item counts to each invoice
        for inv in invoices:
            cursor.execute("SELECT COUNT(*) as cnt, SUM(quantity) as total_qty FROM invoice_items WHERE invoice_id = ?", (inv['id'],))
            item_stats = cursor.fetchone()
            inv['item_count'] = item_stats['cnt']
            inv['total_quantity'] = item_stats['total_qty'] or 0

    return render_template('invoices.html', invoices=invoices, query=query)

@app.route('/invoices/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        invoice = cursor.fetchone()
        if not invoice:
            flash("Invoice not found.", "danger")
            return redirect(url_for('invoice_list'))

        cursor.execute("""
            SELECT ii.*, i.unit as item_unit, i.category as item_category
            FROM invoice_items ii
            LEFT JOIN items i ON ii.item_id = i.id
            WHERE ii.invoice_id = ?
            ORDER BY ii.id ASC
        """, (invoice_id,))
        line_items = [dict(r) for r in cursor.fetchall()]

    return render_template('invoice_detail.html', invoice=dict(invoice), line_items=line_items)

# ================= AUDIT LOGS & REPORTS =================

@app.route('/audit')
@login_required
def audit_logs():
    action = request.args.get('action', '')
    sql = "SELECT * FROM inventory_logs WHERE 1=1"
    params = []
    if action:
        sql += " AND action_type = ?"
        params.append(action)

    sql += " ORDER BY id DESC LIMIT 200"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        logs = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT action_type FROM inventory_logs ORDER BY action_type ASC")
        action_types = [r['action_type'] for r in cursor.fetchall()]

    return render_template('audit.html', logs=logs, action_types=action_types, selected_action=action)

# ================= FINITE USERS DIRECTORY =================

@app.route('/users')
@login_required
def users_list():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, email, created_at, last_login FROM users ORDER BY id ASC")
        users = [dict(r) for r in cursor.fetchall()]

    return render_template('users.html', users=users)

# ================= API HELPER =================

@app.route('/api/item/<int:item_id>')
@login_required
def api_get_item(item_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, sku, name, category, unit, selling_price, cost_price, quantity, min_threshold FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        return jsonify(dict(item))

if __name__ == '__main__':
    # Default port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
