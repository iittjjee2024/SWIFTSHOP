"""
Test the /admin/query endpoint directly
Run: python test_query.py
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Step 1: Login as admin
print("1️⃣ Logging in as admin...")
login_resp = requests.post(f"{BASE_URL}/users/login", json={
    "email": "admin@swiftshop.com",
    "password": "Admin@1234"
})

if login_resp.status_code != 200:
    print(f" Login failed: {login_resp.status_code}")
    print(login_resp.text)
    exit(1)

token = login_resp.json()["access_token"]
print(f" Login successful! Token: {token[:20]}...")

# Step 2: Test query endpoint
print("\n2️⃣ Testing SELECT * FROM users...")
query_resp = requests.post(
    f"{BASE_URL}/admin/query",
    headers={"Authorization": f"Bearer {token}"},
    json={"query": "SELECT * FROM users"}
)

print(f"Status: {query_resp.status_code}")
print(f"Response: {json.dumps(query_resp.json(), indent=2)}")

if query_resp.status_code == 200:
    data = query_resp.json()
    if data.get("status") == "success":
        print(f"\n Query successful! {data['rows_affected']} rows returned")
        if data.get("columns"):
            print(f"Columns: {', '.join(data['columns'])}")
    else:
        print(f"\n Query failed: {data.get('error')}")
else:
    print(f"\n Request failed!")
