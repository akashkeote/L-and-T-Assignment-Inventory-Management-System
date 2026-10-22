-- =============================================================
--  PROJECT STATEMENT 2: Inventory Management System
--  Tables: Supplier, Product, InventoryTransaction
-- =============================================================

-- -------------------------------------------------------------
-- 1. CREATE TABLES
-- -------------------------------------------------------------

-- Drop tables in reverse dependency order (if re-running)
DROP TABLE IF EXISTS InventoryTransaction;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Supplier;

-- ── Supplier Table ──────────────────────────────────────────
CREATE TABLE Supplier (
    SupplierID   INT           PRIMARY KEY AUTO_INCREMENT,
    SupplierName VARCHAR(150)  NOT NULL,
    ContactName  VARCHAR(100),
    ContactTitle VARCHAR(100),
    Address      VARCHAR(200),
    City         VARCHAR(100),
    Region       VARCHAR(100),
    PostalCode   VARCHAR(20),
    Country      VARCHAR(100),
    Phone        VARCHAR(30),
    Email        VARCHAR(150)
);

-- ── Product Table ────────────────────────────────────────────
CREATE TABLE Product (
    ProductID       INT            PRIMARY KEY AUTO_INCREMENT,
    ProductName     VARCHAR(150)   NOT NULL,
    Description     TEXT,
    SupplierID      INT,
    UnitPrice       DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    QuantityInStock INT            NOT NULL DEFAULT 0,
    CONSTRAINT fk_product_supplier
        FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ── Inventory Transaction Table ──────────────────────────────
CREATE TABLE InventoryTransaction (
    TransactionID   INT           PRIMARY KEY AUTO_INCREMENT,
    ProductID       INT           NOT NULL,
    TransactionType ENUM('Purchase','Sale','Return') NOT NULL,
    Quantity        INT           NOT NULL,
    TransactionDate DATE          NOT NULL,
    Notes           TEXT,
    CONSTRAINT fk_transaction_product
        FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- 2. INSERT SAMPLE DATA
-- -------------------------------------------------------------

-- Suppliers
INSERT INTO Supplier (SupplierName, ContactName, ContactTitle, Address, City, Region, PostalCode, Country, Phone, Email)
VALUES
    ('TechParts Inc.',    'Alice Johnson',  'Sales Manager',    '12 Industrial Ave',  'Mumbai',    'Maharashtra', '400001', 'India', '+91-22-1234567', 'alice@techparts.in'),
    ('Global Supplies',   'Bob Smith',      'Account Executive','45 Commerce Street', 'Delhi',     'Delhi',       '110001', 'India', '+91-11-9876543', 'bob@globalsupplies.in'),
    ('QuickStock Ltd.',   'Carol Davis',    'Supply Director',  '7 Warehouse Road',   'Bangalore', 'Karnataka',   '560001', 'India', '+91-80-5556789', 'carol@quickstock.in'),
    ('FastShip Co.',      'David Lee',      'Logistics Head',   '89 Port Lane',       'Chennai',   'Tamil Nadu',  '600001', 'India', '+91-44-3334455', 'david@fastship.in');

-- Products
INSERT INTO Product (ProductName, Description, SupplierID, UnitPrice, QuantityInStock)
VALUES
    ('Laptop Pro 15',      'High-performance 15" laptop',          1, 75000.00, 50),
    ('Wireless Mouse',     'Ergonomic wireless optical mouse',     2,   850.00, 200),
    ('USB-C Hub',          '7-in-1 USB-C hub with HDMI & PD',      3,  2500.00, 150),
    ('Mechanical Keyboard','Compact TKL mechanical keyboard',      1,  4500.00, 80),
    ('Monitor 27"',        '27-inch 4K IPS display monitor',       4, 32000.00, 30),
    ('Webcam HD',          '1080p HD webcam with built-in mic',    2,  3200.00, 120),
    ('Desk Lamp LED',      'Adjustable LED desk lamp',             3,   750.00, 300),
    ('Headset Pro',        'Noise-cancelling over-ear headset',    4,  6500.00, 60);

-- Inventory Transactions
INSERT INTO InventoryTransaction (ProductID, TransactionType, Quantity, TransactionDate, Notes)
VALUES
    (1, 'Purchase', 20, '2026-01-05', 'Initial stock purchase from TechParts'),
    (1, 'Sale',     5,  '2026-01-10', 'Sold to corporate client ABC Corp'),
    (2, 'Purchase', 100,'2026-01-06', 'Bulk order from Global Supplies'),
    (2, 'Sale',     30, '2026-01-12', 'Retail sales'),
    (2, 'Return',   5,  '2026-01-15', 'Defective units returned by customer'),
    (3, 'Purchase', 80, '2026-01-07', 'Ordered from QuickStock'),
    (3, 'Sale',     20, '2026-01-14', 'Sold via online channel'),
    (4, 'Purchase', 50, '2026-01-08', 'Restocking keyboards'),
    (4, 'Sale',     10, '2026-01-16', 'Office supply order'),
    (5, 'Purchase', 15, '2026-01-09', 'New arrival from FastShip'),
    (5, 'Sale',     3,  '2026-01-18', 'Showroom sale'),
    (6, 'Purchase', 60, '2026-02-01', 'Webcam restock'),
    (6, 'Sale',     25, '2026-02-05', 'Work-from-home bundle sales'),
    (7, 'Purchase', 150,'2026-02-03', 'Large batch desk lamps'),
    (7, 'Sale',     70, '2026-02-10', 'Sold to stationery retail outlets'),
    (8, 'Purchase', 40, '2026-02-04', 'Headset initial stock'),
    (8, 'Sale',     15, '2026-02-12', 'Gaming store partnership'),
    (8, 'Return',   2,  '2026-02-15', 'Warranty return');

-- -------------------------------------------------------------
-- 3. SQL QUERIES FOR INVENTORY MANAGEMENT
-- -------------------------------------------------------------

-- ── Q1: View all products with their supplier names ──────────
SELECT
    p.ProductID,
    p.ProductName,
    p.Description,
    s.SupplierName,
    p.UnitPrice,
    p.QuantityInStock
FROM Product p
LEFT JOIN Supplier s ON p.SupplierID = s.SupplierID
ORDER BY p.ProductName;

-- ── Q2: Add a new product ────────────────────────────────────
INSERT INTO Product (ProductName, Description, SupplierID, UnitPrice, QuantityInStock)
VALUES ('Portable SSD 1TB', '1TB USB-C portable solid-state drive', 1, 8500.00, 75);

-- ── Q3: Update quantity in stock for a product ───────────────
UPDATE Product
SET QuantityInStock = QuantityInStock + 50
WHERE ProductID = 1;

-- ── Q4: Record a new inventory transaction (Purchase) ────────
INSERT INTO InventoryTransaction (ProductID, TransactionType, Quantity, TransactionDate, Notes)
VALUES (1, 'Purchase', 30, CURDATE(), 'Q2 restock order');

-- ── Q5: Record a Sale transaction ────────────────────────────
INSERT INTO InventoryTransaction (ProductID, TransactionType, Quantity, TransactionDate, Notes)
VALUES (2, 'Sale', 10, CURDATE(), 'Sold to Retail Partner XYZ');

-- ── Q6: Track all transactions for a specific product ────────
SELECT
    t.TransactionID,
    p.ProductName,
    t.TransactionType,
    t.Quantity,
    t.TransactionDate,
    t.Notes
FROM InventoryTransaction t
JOIN Product p ON t.ProductID = p.ProductID
WHERE p.ProductID = 1
ORDER BY t.TransactionDate DESC;

-- ── Q7: Total stock movement summary per product ─────────────
SELECT
    p.ProductName,
    SUM(CASE WHEN t.TransactionType = 'Purchase' THEN t.Quantity ELSE 0 END) AS TotalPurchased,
    SUM(CASE WHEN t.TransactionType = 'Sale'     THEN t.Quantity ELSE 0 END) AS TotalSold,
    SUM(CASE WHEN t.TransactionType = 'Return'   THEN t.Quantity ELSE 0 END) AS TotalReturned,
    p.QuantityInStock AS CurrentStock
FROM Product p
LEFT JOIN InventoryTransaction t ON p.ProductID = t.ProductID
GROUP BY p.ProductID, p.ProductName, p.QuantityInStock
ORDER BY p.ProductName;

-- ── Q8: Low-stock alert (stock below threshold of 50) ────────
SELECT
    ProductID,
    ProductName,
    QuantityInStock,
    'LOW STOCK - Reorder Required' AS StockStatus
FROM Product
WHERE QuantityInStock < 50
ORDER BY QuantityInStock ASC;

-- ── Q9: Supplier contact report ──────────────────────────────
SELECT
    s.SupplierID,
    s.SupplierName,
    s.ContactName,
    s.ContactTitle,
    CONCAT(s.Address, ', ', s.City, ', ', s.Country) AS FullAddress,
    s.Phone,
    s.Email,
    COUNT(p.ProductID) AS ProductsSupplied
FROM Supplier s
LEFT JOIN Product p ON s.SupplierID = p.SupplierID
GROUP BY s.SupplierID, s.SupplierName, s.ContactName, s.ContactTitle,
         s.Address, s.City, s.Country, s.Phone, s.Email
ORDER BY s.SupplierName;

-- ── Q10: Total inventory value per product ───────────────────
SELECT
    p.ProductName,
    p.UnitPrice,
    p.QuantityInStock,
    ROUND(p.UnitPrice * p.QuantityInStock, 2) AS TotalValue
FROM Product p
ORDER BY TotalValue DESC;

-- ── Q11: Overall inventory value ─────────────────────────────
SELECT
    ROUND(SUM(UnitPrice * QuantityInStock), 2) AS TotalInventoryValue
FROM Product;

-- ── Q12: Monthly transaction summary ────────────────────────
SELECT
    DATE_FORMAT(TransactionDate, '%Y-%m') AS Month,
    TransactionType,
    COUNT(*)            AS TransactionCount,
    SUM(Quantity)       AS TotalQuantity
FROM InventoryTransaction
GROUP BY DATE_FORMAT(TransactionDate, '%Y-%m'), TransactionType
ORDER BY Month, TransactionType;

-- ── Q13: Delete a supplier (only if no products linked) ──────
-- First, reassign or remove linked products, then:
DELETE FROM Supplier WHERE SupplierID = 4;

-- ── Q14: Update supplier contact info ────────────────────────
UPDATE Supplier
SET Email = 'newemail@fastship.in',
    Phone = '+91-44-9998877'
WHERE SupplierID = 4;

-- =============================================================
-- END OF SCRIPT
-- =============================================================
