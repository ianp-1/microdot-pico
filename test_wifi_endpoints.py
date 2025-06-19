#!/usr/bin/env python3
"""
Test script to verify WiFi config endpoints work correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"  # Adjust if needed

def test_config_endpoint():
    """Test the /wifi/config endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/wifi/config")
        print(f"Config endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Config data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing config endpoint: {e}")

def test_status_endpoint():
    """Test the /wifi/status endpoints"""
    try:
        # Test basic status
        response = requests.get(f"{BASE_URL}/wifi/status")
        print(f"Status endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Status data:")
            print(json.dumps(data, indent=2))
        
        # Test detailed status
        response = requests.get(f"{BASE_URL}/wifi/status-detailed")
        print(f"Detailed status endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Detailed status data:")
            print(json.dumps(data, indent=2))
            
    except Exception as e:
        print(f"Error testing status endpoints: {e}")

if __name__ == "__main__":
    print("Testing WiFi configuration endpoints...")
    test_config_endpoint()
    print()
    test_status_endpoint()
