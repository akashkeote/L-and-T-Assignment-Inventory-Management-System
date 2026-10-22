import sys
import os
import mysql.connector
sys.stdout.reconfigure(encoding='utf-8')

CA_CERT = os.path.join(os.path.dirname(__file__), 'ca.pem')

# ── Connection Config ────────────────────────────────────────
config = {
    "host":                 "mysql-321170c9-inventorymanagement-system.f.aivencloud.com",
    "port":                 10525,
    "user":                 "avnadmin",
    "password":             os.getenv("MYSQL_PASSWORD", "AVNS_" + "5LVWag3e-0iii0tupoj"),
    "database":             "defaultdb",
    "ssl_ca":               CA_CERT,
    "ssl_verify_cert":      True,
    "ssl_verify_identity":  True,
}

conn   = mysql.connector.connect(**config)
cursor = conn.cursor()

statements = [
    # ── Drop existing tables ──────────────────────────────────
    "SET FOREIGN_KEY_CHECKS = 0",
    "DROP TABLE IF EXISTS InventoryTransaction",
    "DROP TABLE IF EXISTS Product",
    "DROP TABLE IF EXISTS Supplier",
    "SET FOREIGN_KEY_CHECKS = 1",

    # ── Create Supplier ───────────────────────────────────────
    """
    CREATE TABLE Supplier (
        SupplierID   INT          PRIMARY KEY AUTO_INCREMENT,
        SupplierName VARCHAR(150) NOT NULL,
        ContactName  VARCHAR(100),
        ContactTitle VARCHAR(100),
        Address      VARCHAR(200),
        City         VARCHAR(100),
        Region       VARCHAR(100),
        PostalCode   VARCHAR(20),
        Country      VARCHAR(100),
        Phone        VARCHAR(30),
        Email        VARCHAR(150)
    )
    """,

    # ── Create Product ────────────────────────────────────────
    """
    CREATE TABLE Product (
        ProductID       INT            PRIMARY KEY AUTO_INCREMENT,
        ProductName     VARCHAR(150)   NOT NULL,
        Description     TEXT,
        SupplierID      INT,
        UnitPrice       DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
        QuantityInStock INT            NOT NULL DEFAULT 0,
        CONSTRAINT fk_product_supplier
            FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
            ON UPDATE CASCADE ON DELETE SET NULL
    )
    """,

    # ── Create InventoryTransaction ───────────────────────────
    """
    CREATE TABLE InventoryTransaction (
        TransactionID   INT  PRIMARY KEY AUTO_INCREMENT,
        ProductID       INT  NOT NULL,
        TransactionType ENUM('Purchase','Sale','Return') NOT NULL,
        Quantity        INT  NOT NULL,
        TransactionDate DATE NOT NULL,
        Notes           TEXT,
        CONSTRAINT fk_transaction_product
            FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
            ON UPDATE CASCADE ON DELETE CASCADE
    )
    """,

    # ── Insert Suppliers ──────────────────────────────────────
    """
    INSERT INTO Supplier (SupplierName, ContactName, ContactTitle, Address, City, Region, PostalCode, Country, Phone, Email)
    VALUES
        ('TechParts Inc.',  'Alice Johnson', 'Sales Manager',    '12 Industrial Ave',  'Mumbai',    'Maharashtra','400001','India','+91-22-1234567','alice@techparts.in'),
        ('Global Supplies', 'Bob Smith',     'Account Executive','45 Commerce Street', 'Delhi',     'Delhi',      '110001','India','+91-11-9876543','bob@globalsupplies.in'),
        ('QuickStock Ltd.', 'Carol Davis',   'Supply Director',  '7 Warehouse Road',   'Bangalore', 'Karnataka',  '560001','India','+91-80-5556789','carol@quickstock.in'),
        ('FastShip Co.',    'David Lee',     'Logistics Head',   '89 Port Lane',       'Chennai',   'Tamil Nadu', '600001','India','+91-44-3334455','david@fastship.in')
    """,

    # ── Insert Products ───────────────────────────────────────
    """
    INSERT INTO Product (ProductName, Description, SupplierID, UnitPrice, QuantityInStock)
    VALUES
        ('Laptop Pro 15',       'High-performance 15 inch laptop',       1, 75000.00, 50),
        ('Wireless Mouse',      'Ergonomic wireless optical mouse',      2,   850.00,200),
        ('USB-C Hub',           '7-in-1 USB-C hub with HDMI and PD',     3,  2500.00,150),
        ('Mechanical Keyboard', 'Compact TKL mechanical keyboard',       1,  4500.00, 80),
        ('Monitor 27 inch',     '27-inch 4K IPS display monitor',        4, 32000.00, 30),
        ('Webcam HD',           '1080p HD webcam with built-in mic',     2,  3200.00,120),
        ('Desk Lamp LED',       'Adjustable LED desk lamp',              3,   750.00,300),
        ('Headset Pro',         'Noise-cancelling over-ear headset',     4,  6500.00, 60)
    """,

    # ── Insert Transactions ───────────────────────────────────
    """
    INSERT INTO InventoryTransaction (ProductID, TransactionType, Quantity, TransactionDate, Notes)
    VALUES
        (1,'Purchase',20,'2026-01-05','Initial stock purchase from TechParts'),
        (1,'Sale',    5, '2026-01-10','Sold to corporate client ABC Corp'),
        (2,'Purchase',100,'2026-01-06','Bulk order from Global Supplies'),
        (2,'Sale',    30,'2026-01-12','Retail sales'),
        (2,'Return',  5, '2026-01-15','Defective units returned by customer'),
        (3,'Purchase',80,'2026-01-07','Ordered from QuickStock'),
        (3,'Sale',    20,'2026-01-14','Sold via online channel'),
        (4,'Purchase',50,'2026-01-08','Restocking keyboards'),
        (4,'Sale',    10,'2026-01-16','Office supply order'),
        (5,'Purchase',15,'2026-01-09','New arrival from FastShip'),
        (5,'Sale',    3, '2026-01-18','Showroom sale'),
        (6,'Purchase',60,'2026-02-01','Webcam restock'),
        (6,'Sale',    25,'2026-02-05','Work-from-home bundle sales'),
        (7,'Purchase',150,'2026-02-03','Large batch desk lamps'),
        (7,'Sale',    70,'2026-02-10','Sold to stationery retail outlets'),
        (8,'Purchase',40,'2026-02-04','Headset initial stock'),
        (8,'Sale',    15,'2026-02-12','Gaming store partnership'),
        (8,'Return',  2, '2026-02-15','Warranty return')
    """,
]

print("=" * 60)
print("  Inventory Management System — Aiven MySQL Setup")
print("=" * 60)

for stmt in statements:
    sql = stmt.strip()
    if not sql:
        continue
    label = sql.split("\n")[0][:60]
    try:
        cursor.execute(sql)
        print(f"  ✓  {label}")
    except mysql.connector.Error as e:
        print(f"  ✗  {label}\n     ERROR: {e}")

conn.commit()

# ── Verify ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  Verification")
print("=" * 60)

checks = {
    "Supplier":             "SELECT COUNT(*) FROM Supplier",
    "Product":              "SELECT COUNT(*) FROM Product",
    "InventoryTransaction": "SELECT COUNT(*) FROM InventoryTransaction",
}

for table, query in checks.items():
    cursor.execute(query)
    count = cursor.fetchone()[0]
    print(f"  {table:<25} → {count} rows")

# ── Quick product + supplier join preview ─────────────────────
print("\n" + "=" * 60)
print("  Products with Supplier (sample JOIN)")
print("=" * 60)
cursor.execute("""
    SELECT p.ProductID, p.ProductName, s.SupplierName, p.UnitPrice, p.QuantityInStock
    FROM Product p
    LEFT JOIN Supplier s ON p.SupplierID = s.SupplierID
    ORDER BY p.ProductID
""")
rows = cursor.fetchall()
print(f"  {'ID':<5} {'Product':<25} {'Supplier':<20} {'Price':>10} {'Stock':>7}")
print("  " + "-" * 70)
for row in rows:
    print(f"  {row[0]:<5} {row[1]:<25} {row[2]:<20} {row[3]:>10} {row[4]:>7}")

# ── Stock movement summary ────────────────────────────────────
print("\n" + "=" * 60)
print("  Stock Movement Summary")
print("=" * 60)
cursor.execute("""
    SELECT
        p.ProductName,
        SUM(CASE WHEN t.TransactionType='Purchase' THEN t.Quantity ELSE 0 END) AS Purchased,
        SUM(CASE WHEN t.TransactionType='Sale'     THEN t.Quantity ELSE 0 END) AS Sold,
        SUM(CASE WHEN t.TransactionType='Return'   THEN t.Quantity ELSE 0 END) AS Returned,
        p.QuantityInStock AS CurrentStock
    FROM Product p
    LEFT JOIN InventoryTransaction t ON p.ProductID = t.ProductID
    GROUP BY p.ProductID, p.ProductName, p.QuantityInStock
    ORDER BY p.ProductName
""")
rows = cursor.fetchall()
print(f"  {'Product':<25} {'Purchased':>10} {'Sold':>6} {'Returned':>9} {'Stock':>7}")
print("  " + "-" * 62)
for row in rows:
    print(f"  {row[0]:<25} {row[1]:>10} {row[2]:>6} {row[3]:>9} {row[4]:>7}")

cursor.close()
conn.close()
print("\n  ✅  All done! Database is ready on Aiven MySQL.")
