import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            try:
                body = json.loads(body)
            except:
                pass
            return e.code, body
        except:
            return e.code, str(e)
    except Exception as e:
        return 0, str(e)

def test_auth_flow():
    print("Testing Auth and Refresh flow on backend using urllib...")
    
    email = "test_user_ref_flow@marketbeacon.ai"
    password = "password123"
    
    # 1. Register test user
    reg_data = {
        "full_name": "Test User Ref Flow",
        "email": email,
        "password": password,
        "confirm_password": password
    }
    
    print(f"Registering test user: {email}")
    status, res = make_request(f"{BASE_URL}/api/auth/register", method="POST", data=reg_data)
    
    if status == 201:
        print("Registration successful!")
        auth_data = res
    elif status == 400 and "already registered" in str(res):
        print("User already registered, performing login...")
        login_data = {
            "email": email,
            "password": password
        }
        status, res = make_request(f"{BASE_URL}/api/auth/login", method="POST", data=login_data)
        if status == 200:
            print("Login successful!")
            auth_data = res
        else:
            print(f"Login failed: {status} - {res}")
            sys.exit(1)
    else:
        print(f"Registration failed: {status} - {res}")
        sys.exit(1)
        
    access_token = auth_data["access_token"]
    refresh_token = auth_data["refresh_token"]
    
    # 2. Get current user profile (/me)
    print("Calling /api/auth/me...")
    headers = {"Authorization": f"Bearer {access_token}"}
    status, user_info = make_request(f"{BASE_URL}/api/auth/me", headers=headers)
    if status == 200:
        print("Successfully fetched user profile! User data:")
        print(json.dumps(user_info, indent=2))
        assert "preferences" in user_info, "preferences missing from user profile response"
        print("Preferences block is present in /me response.")
    else:
        print(f"Failed to fetch profile: {status} - {user_info}")
        sys.exit(1)
        
    # 3. Perform token refresh
    print("Calling /api/auth/refresh...")
    refresh_payload = {
        "refresh_token": refresh_token
    }
    status, ref_data = make_request(f"{BASE_URL}/api/auth/refresh", method="POST", data=refresh_payload)
    if status == 200:
        print("Successfully refreshed token! Response data:")
        print(json.dumps(ref_data, indent=2))
        assert "access_token" in ref_data, "access_token missing from refresh response"
        assert "refresh_token" in ref_data, "refresh_token missing from refresh response"
        assert "user" in ref_data, "user data missing from refresh response"
        print("Backend refresh endpoint verified successfully - HTTP 200 with complete serialization!")
    else:
        print(f"Refresh failed: {status} - {ref_data}")
        sys.exit(1)

if __name__ == "__main__":
    test_auth_flow()
