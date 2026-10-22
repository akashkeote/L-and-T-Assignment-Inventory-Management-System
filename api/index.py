import sys
import os
import tempfile
from flask import Flask, jsonify, render_template_string, request
import mysql.connector

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

app = Flask(__name__)

CA_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIERDCCAqygAwIBAgIULPl3RblL8LekSvsVu1tyqrboFskwDQYJKoZIhvcNAQEM
BQAwOjE4MDYGA1UEAwwvMGJmYTFjMTktMDA3My00NThhLWIxNmItMTg3ZGUyNmY2
OTdjIFByb2plY3QgQ0EwHhcNMjYxMDIyMTMzODA1WhcNMzYxMDE5MTMzODA1WjA6
MTgwNgYDVQQDDC8wYmZhMWMxOS0wMDczLTQ1OGEtYjE2Yi0xODdkZTI2ZjY5N2Mg
UHJvamVjdCBDQTCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBANMI1jzs
9KQ+J3K7fSkRRY0aXGRvLUJ7aWa4C031UeNRDlX5R6OqHe8PfMlpBUQSRXGkj9Cv
+Og/q12iZcseHCN1Qs3WEgO9GBXDMTsXDzh8fPaQE4kVLgWkB6+bTBPrgNGB6P9l
igDbNiGu5TghmAPkYMGUMhH1DFSHIzbDSbUtlw9NRYkOhbFnZJnzmj1xSbAJbwAx
9qAiAGVn3h85dg1daphwWfbmkXy3nWXFXwVDmp5FdPK44drz1r3WUVnxUaXpQj8e
zNaQVE/ZOwRmOKfJlQcmOzJwLf0cRxiE7WB5eZT77zfM0w0F5Bstzfrsqrbhe3zO
9zFQQTqh1TbamfrP4uQJW2SuX6hI+wXamPuynzPwcVYe4WNqKM4AIaa4k0jCxxWC
IPkxy9s4zPiyANYt/NmUx5xkgRM7j2bIyMJDTXebcI1yZin0NjCm0fwbpiPrlxpA
BDJTZyjWQBWNsDt7ALMyibIjkRsETCaq1flZS7UJGhS2lFZtnNoMwkjzOwIDAQAB
o0IwQDAdBgNVHQ4EFgQU6qY0GSKWDFYhfFNBdN9Y9zgEgzAwEgYDVR0TAQH/BAgw
BgEB/wIBADALBgNVHQ8EBAMCAQYwDQYJKoZIhvcNAQEMBQADggGBAL1cM4pvN+ZE
GiwZJqJ/jRif0dQX5QFltMqI/3ZMc2GeofmcetkUJfDMO1ECJoj8t6YJsKqCnH4E
hUD9dVpJglgprjkrpMhUzlf6CPpen2+U3bd3zOvx4XW3D36eYQAk9ojYHHgJqBAg
SrZgTHSpw2mg8xg/WsQJ2Fghq5nH99Mg4XtwfAXJ6X18XTn7ZXElN3JgcFmBVvnU
PMmCHVsxxeqsePeWaCD139yaU3yf/tRbHFFChxOyO37S/1mr2Wmz4v1zT8WzWxLV
/Z1VwAWCx/w5ySFtLvM2uH96pQ9Cgkk/zS9sGrcm9DA07fc5/9AWFbyVmDIjWxxo
enpg3HSclyaUEla5Wlo1DPOEfm0V61DTRNxkvnpanyp/spgHKsrWVMjUUxCzz5uU
Dwt6yFXouvQvRBakfhnU/6y4AefS4oWAP7zGLDSPp61LhGfGQr2mNn1iwsbDZf5L
ZIVIxm3X5hnmiI83SRctQNmsMw9zpB6pjbHNI/e6LCcQMqq5FWfyhw==
-----END CERTIFICATE-----"""

def get_ca_cert_path():
    path = os.path.join(tempfile.gettempdir(), 'aiven_ca.pem')
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(CA_CERT_PEM.strip())
    return path

def get_conn():
    return mysql.connector.connect(
        host='mysql-321170c9-inventorymanagement-system.f.aivencloud.com',
        port=10525,
        user='avnadmin',
        password=os.getenv('MYSQL_PASSWORD', 'AVNS_' + '5LVWag3e-0iii0tupoj'),
        database='defaultdb',
        ssl_ca=get_ca_cert_path(),
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )

# ══════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════
@app.route('/api/stats')
def api_stats():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS v FROM Product");              products  = cur.fetchone()['v']
    cur.execute("SELECT COUNT(*) AS v FROM Supplier");             suppliers = cur.fetchone()['v']
    cur.execute("SELECT COUNT(*) AS v FROM InventoryTransaction"); txns      = cur.fetchone()['v']
    cur.execute("SELECT COALESCE(ROUND(SUM(UnitPrice*QuantityInStock),2),0) AS v FROM Product")
    value = float(cur.fetchone()['v'])
    cur.execute("SELECT COUNT(*) AS v FROM Product WHERE QuantityInStock < 50")
    low = cur.fetchone()['v']
    conn.close()
    return jsonify({
        'products': products,
        'suppliers': suppliers,
        'transactions': txns,
        'inventory_value': value,
        'low_stock': low
    })

# ══════════════════════════════════════════════════
#  PRODUCTS CRUD & UPDATE
# ══════════════════════════════════════════════════
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.ProductID, p.ProductName, p.Description,
               CAST(p.UnitPrice AS CHAR) AS UnitPrice, p.QuantityInStock,
               p.SupplierID, s.SupplierName,
               CASE WHEN p.QuantityInStock < 50 THEN 'Low' ELSE 'OK' END AS StockStatus
        FROM Product p LEFT JOIN Supplier s ON p.SupplierID = s.SupplierID ORDER BY p.ProductID
    """)
    rows = cur.fetchall(); conn.close()
    return jsonify(rows)

@app.route('/api/products', methods=['POST'])
def add_product():
    d = request.json
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO Product (ProductName, Description, SupplierID, UnitPrice, QuantityInStock)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        d['ProductName'],
        d.get('Description', ''),
        d.get('SupplierID') or None,
        float(d['UnitPrice']),
        int(d['QuantityInStock'])
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': new_id, 'message': 'Product created successfully'})

@app.route('/api/products/<int:pid>', methods=['PUT', 'POST'])
def update_product(pid):
    d = request.json
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        UPDATE Product 
        SET ProductName=%s, Description=%s, SupplierID=%s,
            UnitPrice=%s, QuantityInStock=%s 
        WHERE ProductID=%s
    """, (
        d['ProductName'],
        d.get('Description', ''),
        d.get('SupplierID') or None,
        float(d['UnitPrice']),
        int(d['QuantityInStock']),
        pid
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Product #{pid} updated successfully'})

@app.route('/api/products/<int:pid>/quick-stock', methods=['POST'])
def quick_stock_update(pid):
    d = request.json
    delta = int(d.get('delta', 0))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE Product SET QuantityInStock = GREATEST(0, QuantityInStock + %s) WHERE ProductID = %s", (delta, pid))
    conn.commit()
    cur.execute("SELECT QuantityInStock FROM Product WHERE ProductID = %s", (pid,))
    new_qty = cur.fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'new_quantity': new_qty})

@app.route('/api/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM Product WHERE ProductID=%s", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Product #{pid} deleted successfully'})

# ══════════════════════════════════════════════════
#  SUPPLIERS CRUD & UPDATE
# ══════════════════════════════════════════════════
@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, COUNT(p.ProductID) AS ProductCount
        FROM Supplier s LEFT JOIN Product p ON s.SupplierID = p.SupplierID
        GROUP BY s.SupplierID ORDER BY s.SupplierID
    """)
    rows = cur.fetchall(); conn.close()
    return jsonify(rows)

@app.route('/api/suppliers', methods=['POST'])
def add_supplier():
    d = request.json
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO Supplier (SupplierName, ContactName, ContactTitle, Address, City, Region, PostalCode, Country, Phone, Email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        d['SupplierName'], d.get('ContactName', ''), d.get('ContactTitle', ''),
        d.get('Address', ''), d.get('City', ''), d.get('Region', ''),
        d.get('PostalCode', ''), d.get('Country', ''), d.get('Phone', ''), d.get('Email', '')
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': new_id, 'message': 'Supplier created successfully'})

@app.route('/api/suppliers/<int:sid>', methods=['PUT', 'POST'])
def update_supplier(sid):
    d = request.json
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        UPDATE Supplier 
        SET SupplierName=%s, ContactName=%s, ContactTitle=%s,
            Address=%s, City=%s, Region=%s, PostalCode=%s,
            Country=%s, Phone=%s, Email=%s
        WHERE SupplierID=%s
    """, (
        d['SupplierName'], d.get('ContactName', ''), d.get('ContactTitle', ''),
        d.get('Address', ''), d.get('City', ''), d.get('Region', ''),
        d.get('PostalCode', ''), d.get('Country', ''), d.get('Phone', ''), d.get('Email', ''),
        sid
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Supplier #{sid} updated successfully'})

@app.route('/api/suppliers/<int:sid>', methods=['DELETE'])
def delete_supplier(sid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM Supplier WHERE SupplierID=%s", (sid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Supplier #{sid} deleted successfully'})

# ══════════════════════════════════════════════════
#  TRANSACTIONS CRUD & UPDATE
# ══════════════════════════════════════════════════
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.TransactionID, t.ProductID, p.ProductName, t.TransactionType,
               t.Quantity, CAST(t.TransactionDate AS CHAR) AS TransactionDate, t.Notes
        FROM InventoryTransaction t JOIN Product p ON t.ProductID = p.ProductID
        ORDER BY t.TransactionDate DESC, t.TransactionID DESC
    """)
    rows = cur.fetchall(); conn.close()
    return jsonify(rows)

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    d = request.json
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        INSERT INTO InventoryTransaction (ProductID, TransactionType, Quantity, TransactionDate, Notes)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        int(d['ProductID']), d['TransactionType'], int(d['Quantity']),
        d['TransactionDate'], d.get('Notes', '')
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': new_id, 'message': 'Transaction recorded successfully'})

@app.route('/api/transactions/<int:tid>', methods=['PUT', 'POST'])
def update_transaction(tid):
    d = request.json
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        UPDATE InventoryTransaction 
        SET ProductID=%s, TransactionType=%s, Quantity=%s,
            TransactionDate=%s, Notes=%s 
        WHERE TransactionID=%s
    """, (
        int(d['ProductID']), d['TransactionType'], int(d['Quantity']),
        d['TransactionDate'], d.get('Notes', ''),
        tid
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Transaction #{tid} updated successfully'})

@app.route('/api/transactions/<int:tid>', methods=['DELETE'])
def delete_transaction(tid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM InventoryTransaction WHERE TransactionID=%s", (tid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': f'Transaction #{tid} deleted successfully'})

@app.route('/api/stock_movement')
def api_stock_movement():
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT p.ProductName,
          COALESCE(SUM(CASE WHEN t.TransactionType='Purchase' THEN t.Quantity ELSE 0 END),0) AS Purchased,
          COALESCE(SUM(CASE WHEN t.TransactionType='Sale'     THEN t.Quantity ELSE 0 END),0) AS Sold,
          COALESCE(SUM(CASE WHEN t.TransactionType='Return'   THEN t.Quantity ELSE 0 END),0) AS Returned,
          p.QuantityInStock AS Stock,
          ROUND(p.UnitPrice * p.QuantityInStock, 2) AS TotalValue
        FROM Product p LEFT JOIN InventoryTransaction t ON p.ProductID = t.ProductID
        GROUP BY p.ProductID, p.ProductName, p.QuantityInStock, p.UnitPrice ORDER BY TotalValue DESC
    """)
    rows = cur.fetchall()
    for r in rows:
        r['TotalValue'] = float(r['TotalValue'] or 0)
    conn.close()
    return jsonify(rows)

# ══════════════════════════════════════════════════
#  DASHBOARD HTML
# ══════════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Inventory Dashboard — Aiven Live</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:#f8f9fc; --white:#ffffff; --border:#e2e8f0; --border2:#cbd5e1;
    --text:#0f172a; --sub:#475569; --muted:#94a3b8;
    --indigo:#4f46e5; --indigo-h:#4338ca; --indigo-light:#eef2ff;
    --green:#059669; --red:#dc2626; --amber:#d97706; --blue:#2563eb;
    --green-light:#ecfdf5; --red-light:#fef2f2; --amber-light:#fffbeb; --blue-light:#eff6ff;
    --shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
    --shadow-md:0 4px 20px -2px rgba(0,0,0,.08);
  }
  body { font-family:'Segoe UI',system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); min-height:100vh; }

  /* NAV */
  nav { background:var(--white); border-bottom:1px solid var(--border); height:64px; display:flex; align-items:center; padding:0 32px; justify-content:space-between; position:sticky; top:0; z-index:200; box-shadow:var(--shadow); }
  .nav-logo { display:flex; align-items:center; gap:12px; }
  .nav-icon { width:38px; height:38px; border-radius:10px; background:linear-gradient(135deg,#f59e0b,#ea580c); display:flex; align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(245,158,11,.3); }
  .nav-name { font-size:15px; font-weight:700; color:var(--text); }
  .nav-sub  { font-size:11px; color:var(--muted); font-family:monospace; }
  .nav-actions { display:flex; align-items:center; gap:10px; }

  /* BUTTONS */
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; padding:8px 16px; border-radius:8px; font-size:13px; font-weight:600; cursor:pointer; border:none; transition:all .18s; }
  .btn-outline { background:var(--white); border:1px solid var(--border2); color:var(--sub); }
  .btn-outline:hover { border-color:var(--indigo); color:var(--indigo); background:var(--indigo-light); }
  .btn-primary { background:var(--indigo); color:#fff; box-shadow:0 2px 6px rgba(79,70,229,.25); }
  .btn-primary:hover { background:var(--indigo-h); }
  .btn-danger { background:var(--red-light); color:var(--red); border:1px solid #fecaca; }
  .btn-danger:hover { background:#fecaca; }
  .btn-sm { padding:5px 10px; font-size:12px; border-radius:6px; }
  .btn.spinning svg { animation:spin .7s linear infinite; }
  @keyframes spin{to{transform:rotate(360deg)}}

  .stepper-btn { width:24px; height:24px; border-radius:6px; border:1px solid var(--border2); background:var(--white); color:var(--sub); font-size:13px; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; transition:all .15s; }
  .stepper-btn:hover { background:var(--indigo-light); color:var(--indigo); border-color:var(--indigo); }

  /* WRAP & HERO */
  .wrap { max-width:1200px; margin:0 auto; padding:0 28px; }
  .hero { padding:40px 0 24px; text-align:center; }
  .hero-pill { display:inline-flex; align-items:center; gap:7px; border:1px solid var(--border2); border-radius:20px; padding:5px 16px; font-size:12px; color:var(--sub); margin-bottom:18px; background:var(--white); box-shadow:var(--shadow); }
  .hero h1 { font-size:clamp(32px,5vw,52px); font-weight:800; letter-spacing:-1.5px; line-height:1.15; margin-bottom:10px; }
  .hero h1 em { font-style:normal; color:var(--amber); }
  .hero p { font-size:15px; color:var(--sub); max-width:440px; margin:0 auto; line-height:1.6; }

  /* STATS CARDS */
  .stats { display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin:28px 0; }
  .sc { background:var(--white); border:1px solid var(--border); border-radius:14px; padding:18px; box-shadow:var(--shadow); transition:transform .18s,box-shadow .18s; }
  .sc:hover { transform:translateY(-2px); box-shadow:var(--shadow-md); }
  .sc-icon { width:38px; height:38px; border-radius:9px; display:flex; align-items:center; justify-content:center; margin-bottom:12px; }
  .sc-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin-bottom:5px; }
  .sc-val   { font-size:26px; font-weight:800; line-height:1; }

  /* TABS */
  .tab-bar { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--border); margin-bottom:20px; }
  .tab-btns { display:flex; gap:4px; }
  .tab-btn { display:flex; align-items:center; gap:6px; padding:11px 18px; font-size:13px; font-weight:600; color:var(--sub); border:none; background:none; cursor:pointer; border-bottom:2px solid transparent; margin-bottom:-1px; transition:all .18s; }
  .tab-btn:hover { color:var(--text); }
  .tab-btn.active { color:var(--indigo); border-bottom-color:var(--indigo); }
  .tab-pane { display:none; }
  .tab-pane.active { display:block; animation:fadeUp .2s ease; }
  @keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}

  /* TABLE */
  .tbl-wrap { background:var(--white); border:1px solid var(--border); border-radius:14px; overflow:hidden; box-shadow:var(--shadow); margin-bottom:32px; }
  .tbl-head { padding:14px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; }
  .tbl-title { font-size:14px; font-weight:700; display:flex; align-items:center; gap:8px; }
  .tbl-count { font-size:12px; color:var(--muted); background:var(--bg); border:1px solid var(--border); padding:3px 10px; border-radius:20px; font-weight:600; }
  .tbl-scroll { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; min-width:620px; }
  thead th { padding:11px 16px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); background:var(--bg); border-bottom:1px solid var(--border); text-align:left; white-space:nowrap; }
  tbody td { padding:13px 16px; font-size:13px; color:var(--sub); border-bottom:1px solid var(--border); vertical-align:middle; }
  tbody tr:last-child td { border-bottom:none; }
  tbody tr:hover td { background:#f8fafc; }
  .td-main { font-weight:600; color:var(--text) !important; }
  .td-id   { color:var(--muted) !important; font-size:12px; font-weight:600; font-family:monospace; }
  .td-price { color:var(--green) !important; font-weight:700; font-variant-numeric:tabular-nums; }
  .td-actions { display:flex; gap:6px; }

  /* BADGES */
  .badge { display:inline-flex; align-items:center; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; }
  .b-ok       { background:var(--green-light); color:var(--green); }
  .b-low      { background:var(--red-light);   color:var(--red); }
  .b-purchase { background:var(--green-light); color:var(--green); }
  .b-sale     { background:var(--blue-light);  color:var(--blue); }
  .b-return   { background:var(--red-light);   color:var(--red); }
  .b-sup      { background:var(--indigo-light);color:var(--indigo); }

  /* MODAL */
  .overlay { display:none; position:fixed; inset:0; background:rgba(15,23,42,.45); z-index:500; backdrop-filter:blur(3px); align-items:center; justify-content:center; }
  .overlay.open { display:flex; }
  .modal { background:var(--white); border-radius:16px; box-shadow:var(--shadow-md); width:92%; max-width:520px; max-height:90vh; overflow-y:auto; animation:popIn .22s ease; border:1px solid var(--border); }
  @keyframes popIn{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:scale(1)}}
  .modal-head { padding:18px 24px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; }
  .modal-title { font-size:16px; font-weight:700; color:var(--text); }
  .modal-close { width:32px; height:32px; border-radius:8px; background:var(--bg); border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; color:var(--sub); font-size:18px; transition:background .15s; }
  .modal-close:hover { background:var(--border2); }
  .modal-body { padding:20px 24px; }
  .modal-foot { padding:14px 24px; border-top:1px solid var(--border); display:flex; justify-content:flex-end; gap:8px; }
  .form-row { margin-bottom:16px; }
  .form-row:last-child { margin-bottom:0; }
  label { display:block; font-size:11px; font-weight:700; color:var(--sub); margin-bottom:6px; text-transform:uppercase; letter-spacing:.05em; }
  input, select, textarea { width:100%; padding:9px 12px; border:1px solid var(--border2); border-radius:8px; font-size:14px; color:var(--text); background:var(--white); transition:border-color .18s,box-shadow .18s; font-family:inherit; }
  input:focus, select:focus, textarea:focus { outline:none; border-color:var(--indigo); box-shadow:0 0 0 3px rgba(79,70,229,.12); }
  textarea { resize:vertical; min-height:68px; }
  .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }

  /* CHART */
  .chart-wrap { background:var(--white); border:1px solid var(--border); border-radius:14px; padding:22px; box-shadow:var(--shadow); margin-bottom:32px; }
  .chart-leg { display:flex; gap:18px; margin-bottom:20px; flex-wrap:wrap; }
  .leg { display:flex; align-items:center; gap:6px; font-size:12px; color:var(--sub); font-weight:600; }
  .leg-dot { width:10px; height:10px; border-radius:3px; }
  .chart-row { margin-bottom:18px; }
  .chart-row:last-child { margin-bottom:0; }
  .cname-row { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:7px; }
  .cname { font-size:13px; font-weight:700; color:var(--text); }
  .cval  { font-size:12px; color:var(--sub); font-weight:600; }
  .bar-track { background:var(--bg); border-radius:6px; height:7px; margin-bottom:4px; overflow:hidden; border:1px solid var(--border); }
  .bar-fill { height:100%; border-radius:6px; width:0; transition:width 1.1s cubic-bezier(.22,1,.36,1); }
  .bar-p { background:linear-gradient(90deg,#059669,#34d399); }
  .bar-s { background:linear-gradient(90deg,#2563eb,#60a5fa); }
  .bar-r { background:linear-gradient(90deg,#dc2626,#f87171); }
  .bar-nums { display:flex; gap:14px; font-size:11px; color:var(--muted); font-weight:600; }

  /* TOAST */
  #toast { position:fixed; bottom:24px; right:24px; z-index:9999; display:flex; flex-direction:column; gap:8px; pointer-events:none; }
  .toast { padding:12px 20px; border-radius:10px; font-size:13px; font-weight:600; box-shadow:var(--shadow-md); animation:slideIn .25s ease; max-width:320px; pointer-events:auto; }
  .toast-success { background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }
  .toast-error   { background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }
  @keyframes slideIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}

  .loader { text-align:center; padding:40px; }
  .spin-ring { display:inline-block; width:22px; height:22px; border:2px solid var(--border2); border-top-color:var(--indigo); border-radius:50%; animation:spin .7s linear infinite; }
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-logo">
    <div class="nav-icon">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
      </svg>
    </div>
    <div>
      <div class="nav-name">Inventory Management System</div>
      <div class="nav-sub">defaultdb · mysql-321170c9 · Aiven MySQL 8.4</div>
    </div>
  </div>
  <div class="nav-actions">
    <button class="btn btn-outline" id="refresh-btn" onclick="refreshAll()">
      <svg id="refresh-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
      Refresh
    </button>
  </div>
</nav>

<div class="wrap">
  <!-- HERO -->
  <div class="hero">
    <div class="hero-pill">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Aiven Cloud MySQL 8.4 · Real-time CRUD & Updates
    </div>
    <h1>Manage & <em>Update</em> Inventory.</h1>
    <p>Perform full Create, Read, Update, and Delete operations directly from this dashboard.</p>
  </div>

  <!-- STATS -->
  <div class="stats">
    <div class="sc">
      <div class="sc-icon" style="background:var(--blue-light);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--blue)" stroke-width="2" stroke-linecap="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
      </div>
      <div class="sc-label">Products</div>
      <div class="sc-val" style="color:var(--blue);" id="s-products">—</div>
    </div>
    <div class="sc">
      <div class="sc-icon" style="background:var(--amber-light);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="2" stroke-linecap="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
      </div>
      <div class="sc-label">Suppliers</div>
      <div class="sc-val" style="color:var(--amber);" id="s-suppliers">—</div>
    </div>
    <div class="sc">
      <div class="sc-icon" style="background:var(--green-light);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      </div>
      <div class="sc-label">Transactions</div>
      <div class="sc-val" id="s-txns">—</div>
    </div>
    <div class="sc">
      <div class="sc-icon" style="background:var(--red-light);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--red)" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="sc-label">Low Stock</div>
      <div class="sc-val" style="color:var(--red);" id="s-low">—</div>
    </div>
    <div class="sc">
      <div class="sc-icon" style="background:var(--green-light);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      </div>
      <div class="sc-label">Total Value</div>
      <div class="sc-val" style="color:var(--green);" id="s-value">—</div>
    </div>
  </div>

  <!-- TABS -->
  <div class="tab-bar">
    <div class="tab-btns">
      <button class="tab-btn active" onclick="switchTab('products',this)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
        Products
      </button>
      <button class="tab-btn" onclick="switchTab('suppliers',this)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
        Suppliers
      </button>
      <button class="tab-btn" onclick="switchTab('transactions',this)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        Transactions
      </button>
      <button class="tab-btn" onclick="switchTab('chart',this)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        Stock Chart
      </button>
    </div>
    <div id="tab-action"></div>
  </div>

  <!-- PRODUCTS TAB -->
  <div id="pane-products" class="tab-pane active">
    <div class="tbl-wrap">
      <div class="tbl-head">
        <span class="tbl-title"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--indigo)" stroke-width="2.2" stroke-linecap="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg> All Products</span>
        <span class="tbl-count" id="cnt-products">—</span>
      </div>
      <div class="tbl-scroll">
        <table>
          <thead><tr><th>#</th><th>Product</th><th>Description</th><th>Supplier</th><th>Price</th><th>Stock</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody id="body-products"><tr><td colspan="8"><div class="loader"><div class="spin-ring"></div></div></td></tr></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- SUPPLIERS TAB -->
  <div id="pane-suppliers" class="tab-pane">
    <div class="tbl-wrap">
      <div class="tbl-head">
        <span class="tbl-title"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--indigo)" stroke-width="2.2" stroke-linecap="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg> Suppliers</span>
        <span class="tbl-count" id="cnt-suppliers">—</span>
      </div>
      <div class="tbl-scroll">
        <table>
          <thead><tr><th>#</th><th>Supplier Name</th><th>Contact</th><th>Title</th><th>City</th><th>Phone</th><th>Email</th><th>Items</th><th>Actions</th></tr></thead>
          <tbody id="body-suppliers"><tr><td colspan="9"><div class="loader"><div class="spin-ring"></div></div></td></tr></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TRANSACTIONS TAB -->
  <div id="pane-transactions" class="tab-pane">
    <div class="tbl-wrap">
      <div class="tbl-head">
        <span class="tbl-title"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--indigo)" stroke-width="2.2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> Transactions</span>
        <span class="tbl-count" id="cnt-transactions">—</span>
      </div>
      <div class="tbl-scroll">
        <table>
          <thead><tr><th>#</th><th>Product</th><th>Type</th><th>Qty</th><th>Date</th><th>Notes</th><th>Actions</th></tr></thead>
          <tbody id="body-transactions"><tr><td colspan="7"><div class="loader"><div class="spin-ring"></div></div></td></tr></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- CHART TAB -->
  <div id="pane-chart" class="tab-pane">
    <div class="chart-wrap">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
        <div><div style="font-size:15px;font-weight:700;">Stock Movement</div><div style="font-size:12px;color:var(--muted);margin-top:3px;">Purchased vs Sold vs Returned per product</div></div>
      </div>
      <div class="chart-leg">
        <div class="leg"><div class="leg-dot" style="background:#059669;"></div>Purchased</div>
        <div class="leg"><div class="leg-dot" style="background:#2563eb;"></div>Sold</div>
        <div class="leg"><div class="leg-dot" style="background:#dc2626;"></div>Returned</div>
      </div>
      <div id="chart-rows"><div class="loader"><div class="spin-ring"></div></div></div>
    </div>
  </div>

  <div style="height:40px;"></div>
</div>

<!-- ══════════ PRODUCT MODAL (ADD & UPDATE) ══════════ -->
<div class="overlay" id="modal-product">
  <div class="modal">
    <div class="modal-head">
      <span class="modal-title" id="modal-product-title">Add / Update Product</span>
      <button class="modal-close" onclick="closeModal('modal-product')">×</button>
    </div>
    <div class="modal-body">
      <input type="hidden" id="p-id">
      <div class="form-row"><label>Product Name *</label><input id="p-name" placeholder="e.g. Wireless Mouse"></div>
      <div class="form-row"><label>Description</label><textarea id="p-desc" placeholder="Product details..."></textarea></div>
      <div class="form-grid">
        <div class="form-row"><label>Unit Price (₹) *</label><input id="p-price" type="number" min="0" step="0.01" placeholder="0.00"></div>
        <div class="form-row"><label>Quantity in Stock *</label><input id="p-qty" type="number" min="0" placeholder="0"></div>
      </div>
      <div class="form-row"><label>Supplier</label>
        <select id="p-supplier"><option value="">— Select Supplier —</option></select>
      </div>
    </div>
    <div class="modal-foot">
      <button class="btn btn-outline" onclick="closeModal('modal-product')">Cancel</button>
      <button class="btn btn-primary" id="btn-save-product" onclick="saveProduct()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        Save Changes
      </button>
    </div>
  </div>
</div>

<!-- ══════════ SUPPLIER MODAL (ADD & UPDATE) ══════════ -->
<div class="overlay" id="modal-supplier">
  <div class="modal">
    <div class="modal-head">
      <span class="modal-title" id="modal-supplier-title">Add / Update Supplier</span>
      <button class="modal-close" onclick="closeModal('modal-supplier')">×</button>
    </div>
    <div class="modal-body">
      <input type="hidden" id="s-id">
      <div class="form-row"><label>Supplier Name *</label><input id="s-name" placeholder="e.g. TechParts Inc."></div>
      <div class="form-grid">
        <div class="form-row"><label>Contact Name</label><input id="s-contact" placeholder="e.g. Alice Johnson"></div>
        <div class="form-row"><label>Contact Title</label><input id="s-title" placeholder="e.g. Sales Manager"></div>
      </div>
      <div class="form-row"><label>Address</label><input id="s-address" placeholder="Street address"></div>
      <div class="form-grid">
        <div class="form-row"><label>City</label><input id="s-city" placeholder="Mumbai"></div>
        <div class="form-row"><label>Region</label><input id="s-region" placeholder="Maharashtra"></div>
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Postal Code</label><input id="s-postal" placeholder="400001"></div>
        <div class="form-row"><label>Country</label><input id="s-country" placeholder="India"></div>
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Phone</label><input id="s-phone" placeholder="+91-22-1234567"></div>
        <div class="form-row"><label>Email</label><input id="s-email" type="email" placeholder="contact@supplier.com"></div>
      </div>
    </div>
    <div class="modal-foot">
      <button class="btn btn-outline" onclick="closeModal('modal-supplier')">Cancel</button>
      <button class="btn btn-primary" id="btn-save-supplier" onclick="saveSupplier()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        Save Changes
      </button>
    </div>
  </div>
</div>

<!-- ══════════ TRANSACTION MODAL (ADD & UPDATE) ══════════ -->
<div class="overlay" id="modal-transaction">
  <div class="modal">
    <div class="modal-head">
      <span class="modal-title" id="modal-txn-title">Add / Update Transaction</span>
      <button class="modal-close" onclick="closeModal('modal-transaction')">×</button>
    </div>
    <div class="modal-body">
      <input type="hidden" id="t-id">
      <div class="form-row"><label>Product *</label>
        <select id="t-product"><option value="">— Select Product —</option></select>
      </div>
      <div class="form-grid">
        <div class="form-row"><label>Transaction Type *</label>
          <select id="t-type">
            <option value="Purchase">Purchase</option>
            <option value="Sale">Sale</option>
            <option value="Return">Return</option>
          </select>
        </div>
        <div class="form-row"><label>Quantity *</label><input id="t-qty" type="number" min="1" placeholder="1"></div>
      </div>
      <div class="form-row"><label>Date *</label><input id="t-date" type="date"></div>
      <div class="form-row"><label>Notes</label><textarea id="t-notes" placeholder="Optional notes..."></textarea></div>
    </div>
    <div class="modal-foot">
      <button class="btn btn-outline" onclick="closeModal('modal-transaction')">Cancel</button>
      <button class="btn btn-primary" id="btn-save-txn" onclick="saveTransaction()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        Save Changes
      </button>
    </div>
  </div>
</div>

<!-- ══════════ CONFIRM DELETE MODAL ══════════ -->
<div class="overlay" id="modal-confirm">
  <div class="modal" style="max-width:380px;">
    <div class="modal-head">
      <span class="modal-title" style="color:var(--red);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="vertical-align:middle;margin-right:5px;"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
        Confirm Deletion
      </span>
      <button class="modal-close" onclick="closeModal('modal-confirm')">×</button>
    </div>
    <div class="modal-body">
      <p id="confirm-msg" style="font-size:14px;color:var(--sub);line-height:1.6;">Are you sure? This cannot be undone.</p>
    </div>
    <div class="modal-foot">
      <button class="btn btn-outline" onclick="closeModal('modal-confirm')">Cancel</button>
      <button class="btn btn-danger" id="confirm-ok-btn">Delete Permanently</button>
    </div>
  </div>
</div>

<!-- TOAST CONTAINER -->
<div id="toast"></div>

<script>
const fmt = v => '₹' + Number(v).toLocaleString('en-IN', {maximumFractionDigits:0});
const badge = (t,c) => `<span class="badge ${c}">${t}</span>`;

function toast(msg, type='success') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = (type==='success'?'✓ ':'✕ ') + msg;
  document.getElementById('toast').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.overlay').forEach(o => o.addEventListener('click', e => { if(e.target===o) o.classList.remove('open'); }));

const api = {
  get: url => fetch(url).then(r=>r.json()),
  post: (url,d) => fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(r=>r.json()),
  put:  (url,d) => fetch(url,{method:'PUT', headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(r=>r.json()),
  del:  url     => fetch(url,{method:'DELETE'}).then(r=>r.json()),
};

// Caches to avoid quote escaping issues
const productsCache = {};
const suppliersCache = {};
const transactionsCache = {};

async function loadStats() {
  const d = await api.get('/api/stats');
  document.getElementById('s-products').textContent  = d.products;
  document.getElementById('s-suppliers').textContent = d.suppliers;
  document.getElementById('s-txns').textContent      = d.transactions;
  document.getElementById('s-low').textContent       = d.low_stock;
  document.getElementById('s-value').textContent     = fmt(d.inventory_value);
}

// ── Products ──
async function loadProducts() {
  const rows = await api.get('/api/products');
  rows.forEach(r => productsCache[r.ProductID] = r);
  document.getElementById('cnt-products').textContent = rows.length + ' records';
  document.getElementById('body-products').innerHTML = rows.map(r => `
    <tr>
      <td class="td-id">#${r.ProductID}</td>
      <td class="td-main">${escapeHtml(r.ProductName)}</td>
      <td style="max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(r.Description||'—')}</td>
      <td>${badge(escapeHtml(r.SupplierName||'None'),'b-sup')}</td>
      <td class="td-price">${fmt(r.UnitPrice)}</td>
      <td>
        <div style="display:flex;align-items:center;gap:6px;">
          <button class="stepper-btn" onclick="quickStock(${r.ProductID},-1)" title="-1 stock">-</button>
          <span style="font-weight:700;min-width:32px;text-align:center;color:${r.QuantityInStock<50?'var(--red)':'var(--green)'};" id="stock-val-${r.ProductID}">${r.QuantityInStock}</span>
          <button class="stepper-btn" onclick="quickStock(${r.ProductID},1)" title="+1 stock">+</button>
        </div>
      </td>
      <td>${badge(r.StockStatus, r.StockStatus==='OK'?'b-ok':'b-low')}</td>
      <td>
        <div class="td-actions">
          <button class="btn btn-outline btn-sm" onclick="editProduct(${r.ProductID})">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Edit
          </button>
          <button class="btn btn-danger btn-sm" onclick="confirmDelete('product',${r.ProductID},'${escapeAttr(r.ProductName)}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
            Delete
          </button>
        </div>
      </td>
    </tr>`).join('');
}

async function quickStock(pid, delta) {
  try {
    const res = await api.post(`/api/products/${pid}/quick-stock`, { delta });
    if (res.success) {
      if (productsCache[pid]) productsCache[pid].QuantityInStock = res.new_quantity;
      const el = document.getElementById(`stock-val-${pid}`);
      if (el) {
        el.textContent = res.new_quantity;
        el.style.color = res.new_quantity < 50 ? 'var(--red)' : 'var(--green)';
      }
      loadStats();
      toast(`Stock updated to ${res.new_quantity}`);
    }
  } catch (e) {
    toast('Stock update failed', 'error');
  }
}

function openAddProduct() {
  document.getElementById('modal-product-title').textContent = 'Add New Product';
  document.getElementById('btn-save-product').textContent = 'Add Product';
  document.getElementById('p-id').value = '';
  document.getElementById('p-name').value = '';
  document.getElementById('p-desc').value = '';
  document.getElementById('p-price').value = '';
  document.getElementById('p-qty').value = '';
  document.getElementById('p-supplier').value = '';
  openModal('modal-product');
}

function editProduct(id) {
  const r = productsCache[id];
  if (!r) return;
  document.getElementById('modal-product-title').textContent = `Update Product #${id}`;
  document.getElementById('btn-save-product').textContent = 'Update Product';
  document.getElementById('p-id').value = r.ProductID;
  document.getElementById('p-name').value = r.ProductName;
  document.getElementById('p-desc').value = r.Description || '';
  document.getElementById('p-price').value = r.UnitPrice;
  document.getElementById('p-qty').value = r.QuantityInStock;
  document.getElementById('p-supplier').value = r.SupplierID || '';
  openModal('modal-product');
}

async function saveProduct() {
  const id = document.getElementById('p-id').value;
  const data = {
    ProductName: document.getElementById('p-name').value.trim(),
    Description: document.getElementById('p-desc').value.trim(),
    UnitPrice: parseFloat(document.getElementById('p-price').value),
    QuantityInStock: parseInt(document.getElementById('p-qty').value),
    SupplierID: document.getElementById('p-supplier').value || null,
  };
  if (!data.ProductName || isNaN(data.UnitPrice) || isNaN(data.QuantityInStock)) {
    toast('Please fill all required fields!', 'error');
    return;
  }
  try {
    if (id) {
      await api.put(`/api/products/${id}`, data);
      toast(`Product #${id} updated successfully!`);
    } else {
      await api.post('/api/products', data);
      toast('Product added successfully!');
    }
    closeModal('modal-product');
    await Promise.all([loadProducts(), loadStats(), loadChart()]);
  } catch (e) {
    toast('Operation failed: ' + e.message, 'error');
  }
}

// ── Suppliers ──
async function loadSuppliers() {
  const rows = await api.get('/api/suppliers');
  rows.forEach(r => suppliersCache[r.SupplierID] = r);
  
  const sel = document.getElementById('p-supplier');
  const cur = sel.value;
  sel.innerHTML = '<option value="">— Select Supplier —</option>' +
    rows.map(s => `<option value="${s.SupplierID}">${escapeHtml(s.SupplierName)}</option>`).join('');
  sel.value = cur;

  document.getElementById('cnt-suppliers').textContent = rows.length + ' records';
  document.getElementById('body-suppliers').innerHTML = rows.map(r => `
    <tr>
      <td class="td-id">#${r.SupplierID}</td>
      <td class="td-main">${escapeHtml(r.SupplierName)}</td>
      <td>${escapeHtml(r.ContactName||'—')}</td>
      <td style="color:var(--muted);">${escapeHtml(r.ContactTitle||'—')}</td>
      <td>${escapeHtml(r.City||'—')}, ${escapeHtml(r.Country||'')}</td>
      <td style="font-family:monospace;font-size:12px;">${escapeHtml(r.Phone||'—')}</td>
      <td style="color:var(--indigo);">${escapeHtml(r.Email||'—')}</td>
      <td>${badge(r.ProductCount + ' items','b-sup')}</td>
      <td>
        <div class="td-actions">
          <button class="btn btn-outline btn-sm" onclick="editSupplier(${r.SupplierID})">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Edit
          </button>
          <button class="btn btn-danger btn-sm" onclick="confirmDelete('supplier',${r.SupplierID},'${escapeAttr(r.SupplierName)}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
            Delete
          </button>
        </div>
      </td>
    </tr>`).join('');
}

function openAddSupplier() {
  document.getElementById('modal-supplier-title').textContent = 'Add New Supplier';
  document.getElementById('btn-save-supplier').textContent = 'Add Supplier';
  ['s-id','s-name','s-contact','s-title','s-address','s-city','s-region','s-postal','s-country','s-phone','s-email']
    .forEach(id => document.getElementById(id).value = '');
  openModal('modal-supplier');
}

function editSupplier(id) {
  const r = suppliersCache[id];
  if (!r) return;
  document.getElementById('modal-supplier-title').textContent = `Update Supplier #${id}`;
  document.getElementById('btn-save-supplier').textContent = 'Update Supplier';
  document.getElementById('s-id').value = r.SupplierID;
  document.getElementById('s-name').value = r.SupplierName || '';
  document.getElementById('s-contact').value = r.ContactName || '';
  document.getElementById('s-title').value = r.ContactTitle || '';
  document.getElementById('s-address').value = r.Address || '';
  document.getElementById('s-city').value = r.City || '';
  document.getElementById('s-region').value = r.Region || '';
  document.getElementById('s-postal').value = r.PostalCode || '';
  document.getElementById('s-country').value = r.Country || '';
  document.getElementById('s-phone').value = r.Phone || '';
  document.getElementById('s-email').value = r.Email || '';
  openModal('modal-supplier');
}

async function saveSupplier() {
  const id = document.getElementById('s-id').value;
  const data = {
    SupplierName: document.getElementById('s-name').value.trim(),
    ContactName:  document.getElementById('s-contact').value.trim(),
    ContactTitle: document.getElementById('s-title').value.trim(),
    Address:      document.getElementById('s-address').value.trim(),
    City:         document.getElementById('s-city').value.trim(),
    Region:       document.getElementById('s-region').value.trim(),
    PostalCode:   document.getElementById('s-postal').value.trim(),
    Country:      document.getElementById('s-country').value.trim(),
    Phone:        document.getElementById('s-phone').value.trim(),
    Email:        document.getElementById('s-email').value.trim(),
  };
  if (!data.SupplierName) {
    toast('Supplier Name is required!', 'error');
    return;
  }
  try {
    if (id) {
      await api.put(`/api/suppliers/${id}`, data);
      toast(`Supplier #${id} updated successfully!`);
    } else {
      await api.post('/api/suppliers', data);
      toast('Supplier added successfully!');
    }
    closeModal('modal-supplier');
    await Promise.all([loadSuppliers(), loadStats()]);
  } catch (e) {
    toast('Operation failed: ' + e.message, 'error');
  }
}

// ── Transactions ──
async function loadTransactions() {
  const rows = await api.get('/api/transactions');
  rows.forEach(r => transactionsCache[r.TransactionID] = r);
  
  const sel = document.getElementById('t-product');
  const cur = sel.value;
  sel.innerHTML = '<option value="">— Select Product —</option>' +
    Object.values(productsCache).map(p => `<option value="${p.ProductID}">${escapeHtml(p.ProductName)}</option>`).join('');
  sel.value = cur;

  document.getElementById('cnt-transactions').textContent = rows.length + ' records';
  const typeCls = {Purchase:'b-purchase', Sale:'b-sale', Return:'b-return'};
  document.getElementById('body-transactions').innerHTML = rows.map(r => `
    <tr>
      <td class="td-id">#${r.TransactionID}</td>
      <td class="td-main">${escapeHtml(r.ProductName)}</td>
      <td>${badge(r.TransactionType, typeCls[r.TransactionType]||'b-sup')}</td>
      <td style="font-weight:700;">${r.Quantity}</td>
      <td style="color:var(--muted);font-size:12px;">${r.TransactionDate}</td>
      <td style="color:var(--muted);max-width:220px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(r.Notes||'—')}</td>
      <td>
        <div class="td-actions">
          <button class="btn btn-outline btn-sm" onclick="editTransaction(${r.TransactionID})">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            Edit
          </button>
          <button class="btn btn-danger btn-sm" onclick="confirmDelete('transaction',${r.TransactionID},'Transaction #${r.TransactionID}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
            Delete
          </button>
        </div>
      </td>
    </tr>`).join('');
}

function openAddTransaction() {
  document.getElementById('modal-txn-title').textContent = 'Add New Transaction';
  document.getElementById('btn-save-txn').textContent = 'Record Transaction';
  document.getElementById('t-id').value = '';
  document.getElementById('t-product').value = '';
  document.getElementById('t-type').value = 'Purchase';
  document.getElementById('t-qty').value = '';
  document.getElementById('t-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('t-notes').value = '';
  openModal('modal-transaction');
}

function editTransaction(id) {
  const r = transactionsCache[id];
  if (!r) return;
  document.getElementById('modal-txn-title').textContent = `Update Transaction #${id}`;
  document.getElementById('btn-save-txn').textContent = 'Update Transaction';
  document.getElementById('t-id').value = r.TransactionID;
  document.getElementById('t-product').value = r.ProductID;
  document.getElementById('t-type').value = r.TransactionType;
  document.getElementById('t-qty').value = r.Quantity;
  document.getElementById('t-date').value = r.TransactionDate;
  document.getElementById('t-notes').value = r.Notes || '';
  openModal('modal-transaction');
}

async function saveTransaction() {
  const id = document.getElementById('t-id').value;
  const data = {
    ProductID:       parseInt(document.getElementById('t-product').value),
    TransactionType: document.getElementById('t-type').value,
    Quantity:        parseInt(document.getElementById('t-qty').value),
    TransactionDate: document.getElementById('t-date').value,
    Notes:           document.getElementById('t-notes').value.trim(),
  };
  if (!data.ProductID || isNaN(data.Quantity) || !data.TransactionDate) {
    toast('Please fill all required fields!', 'error');
    return;
  }
  try {
    if (id) {
      await api.put(`/api/transactions/${id}`, data);
      toast(`Transaction #${id} updated successfully!`);
    } else {
      await api.post('/api/transactions', data);
      toast('Transaction recorded successfully!');
    }
    closeModal('modal-transaction');
    await Promise.all([loadTransactions(), loadStats(), loadChart(), loadProducts()]);
  } catch (e) {
    toast('Operation failed: ' + e.message, 'error');
  }
}

// ── Delete ──
function confirmDelete(type, id, name) {
  document.getElementById('confirm-msg').textContent = `Are you sure you want to delete ${name}? This action directly deletes the record from your Aiven MySQL database.`;
  document.getElementById('confirm-ok-btn').onclick = async () => {
    try {
      const endpoint = type === 'transaction' ? 'transactions' : (type + 's');
      await api.del(`/api/${endpoint}/${id}`);
      toast(`${name} deleted successfully!`);
      closeModal('modal-confirm');
      if (type === 'product')     await Promise.all([loadProducts(), loadStats(), loadChart()]);
      if (type === 'supplier')    await Promise.all([loadSuppliers(), loadStats()]);
      if (type === 'transaction') await Promise.all([loadTransactions(), loadStats(), loadChart()]);
    } catch (e) {
      toast('Delete failed: ' + e.message, 'error');
    }
  };
  openModal('modal-confirm');
}

// ── Chart ──
async function loadChart() {
  const rows = await api.get('/api/stock_movement');
  const maxVal = Math.max(...rows.map(r => r.Purchased), 1);
  document.getElementById('chart-rows').innerHTML = rows.map(r => `
    <div class="chart-row">
      <div class="cname-row">
        <span class="cname">${escapeHtml(r.ProductName)}</span>
        <span class="cval">Stock: ${r.Stock} · ${fmt(r.TotalValue)}</span>
      </div>
      <div class="bar-track"><div class="bar-fill bar-p" data-w="${(r.Purchased/maxVal*100).toFixed(1)}%"></div></div>
      <div class="bar-track"><div class="bar-fill bar-s" data-w="${(r.Sold/maxVal*100).toFixed(1)}%"></div></div>
      ${r.Returned > 0 ? `<div class="bar-track"><div class="bar-fill bar-r" data-w="${(r.Returned/maxVal*100).toFixed(1)}%"></div></div>` : ''}
      <div class="bar-nums">
        <span style="color:var(--green);">↓ ${r.Purchased} purchased</span>
        <span style="color:var(--blue);">↑ ${r.Sold} sold</span>
        ${r.Returned > 0 ? `<span style="color:var(--red);">↩ ${r.Returned} returned</span>` : ''}
      </div>
    </div>`).join('');
  requestAnimationFrame(() => {
    document.querySelectorAll('.bar-fill[data-w]').forEach(el => { el.style.width = el.dataset.w; });
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function escapeAttr(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

const addButtons = {
  products:     `<button class="btn btn-primary" onclick="openAddProduct()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Add Product</button>`,
  suppliers:    `<button class="btn btn-primary" onclick="openAddSupplier()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Add Supplier</button>`,
  transactions: `<button class="btn btn-primary" onclick="openAddTransaction()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Add Transaction</button>`,
  chart: '',
};

function switchTab(name, btn) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('pane-' + name).classList.add('active');
  btn.classList.add('active');
  document.getElementById('tab-action').innerHTML = addButtons[name] || '';
}

async function refreshAll() {
  const btn = document.getElementById('refresh-btn');
  btn.classList.add('spinning');
  await Promise.all([loadStats(), loadSuppliers(), loadProducts()]);
  await Promise.all([loadTransactions(), loadChart()]);
  btn.classList.remove('spinning');
}

document.getElementById('tab-action').innerHTML = addButtons['products'];
refreshAll();
setInterval(refreshAll, 30000);
</script>
</body>
</html>"""

@app.route('/')
def dashboard():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
