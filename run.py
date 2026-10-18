import os
import sys

# Ensure local directory is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" ElectroVault - Inventory Management & Billing System")
    print(f" Running at: http://127.0.0.1:{port}")
    print(f" Authorized accounts: admin, inventory_mgr, clerk_sarah, store_rahul")
    print(f"=======================================================\n")
    app.run(host='127.0.0.1', port=port, debug=False)
