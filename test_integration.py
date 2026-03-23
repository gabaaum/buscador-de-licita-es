import requests
import json

BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/login"
SEARCH_PAGAS_URL = f"{BASE_URL}/api/search_pagas"

# Login to get session
session = requests.Session()
login_data = {
    "email": "admin",
    "senha": "admin"
}
login_response = session.post(LOGIN_URL, data=login_data)
print(f"Login status: {login_response.status_code}")
if login_response.status_code != 200 and login_response.status_code != 302:
    print("Login failed")
    print(login_response.text)
    exit(1)

# Test each state
states = ["federal", "sp", "rj", "mg"]
for state in states:
    print(f"\n--- Testing state: {state} ---")
    search_data = {
        "estado": state,
        "dataInicial": "2024-01-01",
        "dataFinal": "2024-12-31"
    }
    response = session.post(SEARCH_PAGAS_URL, json=search_data)
    print(f"Search status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"Number of results: {len(results)}")
        if results:
            print("First result:")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
        else:
            print("No results")
    else:
        print(f"Error: {response.text}")

print("\n--- Integration test completed ---")