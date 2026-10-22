import sys, os, json
import mysql.connector
sys.stdout.reconfigure(encoding='utf-8')

config = {
    'host': 'mysql-321170c9-inventorymanagement-system.f.aivencloud.com',
    'port': 10525,
    'user': 'avnadmin',
    'password': os.getenv('MYSQL_PASSWORD', 'AVNS_' + '5LVWag3e-0iii0tupoj'),
    'database': 'defaultdb',
    'ssl_disabled': False,
}
conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

cursor.execute('SELECT * FROM Supplier')
suppliers = cursor.fetchall()

cursor.execute('SELECT p.*, s.SupplierName FROM Product p LEFT JOIN Supplier s ON p.SupplierID = s.SupplierID')
products = cursor.fetchall()

cursor.execute('SELECT t.*, p.ProductName FROM InventoryTransaction t JOIN Product p ON t.ProductID = p.ProductID ORDER BY t.TransactionDate DESC')
transactions = cursor.fetchall()

cursor.execute("""
SELECT p.ProductName,
  SUM(CASE WHEN t.TransactionType='Purchase' THEN t.Quantity ELSE 0 END) AS Purchased,
  SUM(CASE WHEN t.TransactionType='Sale'     THEN t.Quantity ELSE 0 END) AS Sold,
  SUM(CASE WHEN t.TransactionType='Return'   THEN t.Quantity ELSE 0 END) AS Returned,
  p.QuantityInStock AS Stock,
  ROUND(p.UnitPrice * p.QuantityInStock, 2) AS TotalValue
FROM Product p
LEFT JOIN InventoryTransaction t ON p.ProductID = t.ProductID
GROUP BY p.ProductID, p.ProductName, p.QuantityInStock, p.UnitPrice
ORDER BY TotalValue DESC
""")
movement = cursor.fetchall()

data = {
    'suppliers': suppliers,
    'products': products,
    'transactions': transactions,
    'movement': movement
}
print(json.dumps(data, default=str))
conn.close()
