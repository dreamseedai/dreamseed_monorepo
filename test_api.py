#!/usr/bin/env python3
"""
Test script to verify the personalized API endpoints are working
"""

import requests
import json

# Test the personalized API endpoints
BASE_URL = "http://127.0.0.1:8012/api"

def test_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        print(f"{method} {endpoint}: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error: {response.text}")
        else:
            print(f"  Success: {response.json()}")
        return response
    except Exception as e:
        print(f"{method} {endpoint}: Error - {e}")
        return None

def main():
    print("Testing DreamSeedAI Personalized API")
    print("=" * 50)
    
    # Test basic endpoints
    test_endpoint("/__ok")
    test_endpoint("/auth/me", headers={"Authorization": "Bearer test_token"})
    
    # Test personalized endpoints
    test_endpoint("/personalized/profile", headers={"Authorization": "Bearer test_token"})
    test_endpoint("/personalized/questions", headers={"Authorization": "Bearer test_token"})
    test_endpoint("/personalized/analytics", headers={"Authorization": "Bearer test_token"})
    
    # Test with a valid token (we'll need to create one)
    print("\nTesting with valid authentication...")
    # First, let's try to get a valid token by checking if there are any users
    # This is just for testing purposes
    
    print("\nAPI test completed!")

if __name__ == "__main__":
    main()
