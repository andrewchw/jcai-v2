#!/usr/bin/env python3
"""
OAuth Flow Test Script

This script tests the OAuth flow endpoints to verify everything is working correctly.
It will make requests to each endpoint and display the responses.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Base URL
BASE_URL = "http://localhost:8000/api"

def test_login():
    """Test the OAuth login endpoint"""
    print("\n=== Testing OAuth Login Endpoint ===")
    
    url = f"{BASE_URL}/auth/oauth/login"
    print(f"Making request to: {url}")
    
    try:
        # Set Accept header to application/json to get JSON response
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Check if we got a redirect URL and follow it
        if "redirect_url" in data:
            print(f"Following redirect to: {data['redirect_url']}")
            full_redirect_url = f"{BASE_URL}{data['redirect_url'].replace('/api', '')}"
            callback_response = requests.get(full_redirect_url)
            if callback_response.status_code == 200:
                print(f"Callback status: {callback_response.status_code} - Success")
        
        return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_token_status():
    """Test the OAuth token status endpoint"""
    print("\n=== Testing OAuth Token Status Endpoint ===")
    
    url = f"{BASE_URL}/auth/oauth/token/status"
    print(f"Making request to: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_logout():
    """Test the OAuth logout endpoint"""
    print("\n=== Testing OAuth Logout Endpoint ===")
    
    url = f"{BASE_URL}/auth/oauth/logout"
    print(f"Making request to: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        return data
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    """Run all tests"""
    print("=== OAuth Flow Test Script ===")
    
    # Test each endpoint
    login_data = test_login()
    token_status = test_token_status()
    logout_data = test_logout()
    
    # Verify token status again after logout
    print("\n=== Verifying token status after logout ===")
    token_status_after = test_token_status()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Login endpoint: {'SUCCESS' if login_data else 'FAILED'}")
    print(f"Token status endpoint: {'SUCCESS' if token_status else 'FAILED'}")
    print(f"Logout endpoint: {'SUCCESS' if logout_data else 'FAILED'}")
    
    # Optional: check if token was actually invalidated
    if token_status and token_status_after:
        token_before = token_status.get('status')
        token_after = token_status_after.get('status')
        
        if token_before != token_after and token_after in ['error', 'unknown']:
            print("Token invalidation test: SUCCESS")
        else:
            print("Token invalidation test: FAILED or Not Applicable")
            print(f"Token status before: {token_before}")
            print(f"Token status after: {token_after}")

if __name__ == "__main__":
    main()
