import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api.index import app

if __name__ == '__main__':
    print("=" * 60)
    print("  🚀  Inventory Dashboard — Full CRUD + Live Aiven MySQL")
    print("  📌  Local URL : http://localhost:5000")
    print("  🔐  SSL       : CA Certificate Verified")
    print("=" * 60)
    app.run(debug=False, port=5000)
