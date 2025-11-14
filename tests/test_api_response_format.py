#!/usr/bin/env python3
"""
Test script for API response format validation

This script tests the standardized API response format across all endpoints.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.web_app import app, create_api_response, create_error_response


def test_helper_functions():
    """Test the helper functions for creating API responses"""
    print("=" * 60)
    print("Testing Helper Functions")
    print("=" * 60)

    # Test create_api_response - success case
    print("\n1. Testing create_api_response() - Success")
    with app.test_request_context():
        response = create_api_response(
            success=True,
            message="テスト成功",
            data={"test_key": "test_value"},
            status_code=200
        )
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response: {json.dumps(response.get_json(), indent=2, ensure_ascii=False)}")
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        print("✅ PASSED")

    # Test create_error_response
    print("\n2. Testing create_error_response()")
    with app.test_request_context():
        response = create_error_response(
            message="テストエラー",
            details="詳細なエラー情報",
            code="TEST_ERROR",
            status_code=400
        )
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response: {json.dumps(response.get_json(), indent=2, ensure_ascii=False)}")
        assert response.status_code == 400
        assert response.get_json()['success'] is False
        assert response.get_json()['error']['code'] == "TEST_ERROR"
        print("✅ PASSED")


def test_response_structure():
    """Test that all responses have the correct structure"""
    print("\n" + "=" * 60)
    print("Testing Response Structure")
    print("=" * 60)

    required_fields = ['success', 'message', 'data', 'error']

    print("\n1. Testing success response structure")
    with app.test_request_context():
        response = create_api_response(
            success=True,
            message="Success",
            data={"key": "value"}
        )
        data = response.get_json()

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  ✓ Field '{field}' present")

        assert data['success'] is True
        assert data['data'] is not None
        assert data['error'] is None
        print("✅ PASSED")

    print("\n2. Testing error response structure")
    with app.test_request_context():
        response = create_error_response(
            message="Error",
            details="Details",
            code="ERROR_CODE"
        )
        data = response.get_json()

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  ✓ Field '{field}' present")

        assert data['success'] is False
        assert data['data'] is None
        assert data['error'] is not None
        assert 'message' in data['error']
        assert 'details' in data['error']
        assert 'code' in data['error']
        print("✅ PASSED")


def test_refresh_data_endpoint():
    """Test the /api/refresh-data endpoint"""
    print("\n" + "=" * 60)
    print("Testing /api/refresh-data Endpoint")
    print("=" * 60)

    client = app.test_client()

    print("\n1. Testing GET request to /api/refresh-data")
    response = client.get('/api/refresh-data')
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")

    # Check CORS headers
    print("\nCORS Headers:")
    print(f"  Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
    print(f"  Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods')}")
    print(f"  Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers')}")

    # Parse JSON response
    try:
        data = response.get_json()
        print("\nResponse Structure:")
        print(f"  success: {data.get('success')}")
        print(f"  message: {data.get('message')}")
        print(f"  data: {type(data.get('data'))}")
        print(f"  error: {type(data.get('error'))}")

        # Verify structure
        assert 'success' in data
        assert 'message' in data
        assert 'data' in data
        assert 'error' in data

        if data['success']:
            print("\n✅ Request successful")
            if data['data'] and 'stats' in data['data']:
                print(f"  Stats: {data['data']['stats']}")
        else:
            print(f"\n❌ Request failed: {data.get('message')}")
            if data['error']:
                print(f"  Error Code: {data['error'].get('code')}")
                print(f"  Details: {data['error'].get('details')}")

        print("\n✅ Response structure validation PASSED")

    except Exception as e:
        print(f"\n❌ Failed to parse JSON response: {e}")
        print(f"Response body: {response.data}")


def test_content_type():
    """Test that Content-Type is properly set"""
    print("\n" + "=" * 60)
    print("Testing Content-Type Headers")
    print("=" * 60)

    with app.test_request_context('/api/refresh-data'):
        response = create_api_response(
            success=True,
            message="Test"
        )
        content_type = response.headers.get('Content-Type')
        print(f"Content-Type: {content_type}")

        assert 'application/json' in content_type
        assert 'charset=utf-8' in content_type
        print("✅ PASSED")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("API Response Format Test Suite")
    print("=" * 60)

    try:
        test_helper_functions()
        test_response_structure()
        test_content_type()
        test_refresh_data_endpoint()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
