"""
Example usage of OpenRoute Navigator API

This script demonstrates how to use the routing API with different scenarios.
"""

import requests
import json


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/route/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_route_with_coordinates():
    """Test routing with coordinates (Natal, RN area)"""
    print("=" * 60)
    print("Test 1: Routing with Coordinates (Natal, RN)")
    print("=" * 60)
    
    # UFRN area to Ponta Negra
    request_data = {
        "origin": {
            "lat": -5.7945,
            "lon": -35.2110
        },
        "destination": {
            "lat": -5.8822,
            "lon": -35.1767
        },
        "vehicle": {
            "vehicle_type": "car"
        }
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/route/calculate",
            json=request_data,
            timeout=120
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {len(data['routes'])} routes:")
            
            for route in data['routes']:
                print(f"\n  Type: {route['type']}")
                print(f"  Distance: {route['distance_km']} km")
                print(f"  Geometry points: {len(route['geometry'])}")
                print(f"  Alerts: {len(route['alerts'])}")
                print(f"  Summary: {route['summary']}")
                
                if route['alerts']:
                    print("  Alert details:")
                    for alert in route['alerts'][:3]:  # Show first 3
                        print(f"    - [{alert['level']}] {alert['message']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print()


def test_route_with_truck():
    """Test routing with truck restrictions"""
    print("=" * 60)
    print("Test 2: Routing with Truck (Height/Weight Restrictions)")
    print("=" * 60)
    
    request_data = {
        "origin": {
            "lat": -5.7945,
            "lon": -35.2110
        },
        "destination": {
            "lat": -5.8822,
            "lon": -35.1767
        },
        "vehicle": {
            "vehicle_type": "truck",
            "height": 4.2,
            "weight": 28
        }
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/route/calculate",
            json=request_data,
            timeout=120
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {len(data['routes'])} routes:")
            
            # Should include truck_compatible route
            for route in data['routes']:
                print(f"\n  Type: {route['type']}")
                print(f"  Distance: {route['distance_km']} km")
                print(f"  Summary: {route['summary']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print()


def test_route_with_address():
    """Test routing with address geocoding"""
    print("=" * 60)
    print("Test 3: Routing with Addresses (Geocoding)")
    print("=" * 60)
    
    request_data = {
        "origin": "UFRN, Natal, RN, Brazil",
        "destination": "Ponta Negra, Natal, RN, Brazil",
        "vehicle": {
            "vehicle_type": "car"
        }
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    print("\nSending request (this may take longer due to geocoding)...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/route/calculate",
            json=request_data,
            timeout=120
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nGeocoded coordinates:")
            print(f"  Origin: {data['origin_coords']}")
            print(f"  Destination: {data['destination_coords']}")
            print(f"\nFound {len(data['routes'])} routes")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "OpenRoute Navigator - API Tests" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\nMake sure the server is running: uvicorn app.main:app --reload\n")
    
    # Run tests
    test_health()
    test_route_with_coordinates()
    test_route_with_truck()
    
    # Uncomment to test with addresses (requires internet for geocoding)
    # test_route_with_address()
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)
