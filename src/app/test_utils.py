"""
Simple test utilities for validation and basic functionality
"""
from utils import (
    validate_wifi_mode, 
    validate_wifi_credentials, 
    validate_eq_update,
    ValidationError,
    create_success_response,
    create_error_response
)
from logger import Logger

def test_validation_functions():
    """Test validation functions"""
    test_logger = Logger("TEST")
    
    # Test WiFi mode validation
    try:
        assert validate_wifi_mode('station') == 'station'
        assert validate_wifi_mode('ap') == 'ap'
        assert validate_wifi_mode('dual') == 'dual'
        test_logger.info("✓ WiFi mode validation passed")
    except Exception as e:
        test_logger.error(f"✗ WiFi mode validation failed: {e}")
    
    # Test invalid WiFi mode
    try:
        validate_wifi_mode('invalid')
        test_logger.error("✗ WiFi mode validation should have failed")
    except ValidationError:
        test_logger.info("✓ Invalid WiFi mode properly rejected")
    
    # Test WiFi credentials validation
    try:
        ssid, password = validate_wifi_credentials('MyNetwork', 'mypassword123')
        assert ssid == 'MyNetwork'
        assert password == 'mypassword123'
        test_logger.info("✓ WiFi credentials validation passed")
    except Exception as e:
        test_logger.error(f"✗ WiFi credentials validation failed: {e}")
    
    # Test short password
    try:
        validate_wifi_credentials('MyNetwork', '123')
        test_logger.error("✗ Short password should have been rejected")
    except ValidationError:
        test_logger.info("✓ Short password properly rejected")
    
    # Test EQ validation
    try:
        band, value = validate_eq_update('low', -6.0)
        assert band == 'low'
        assert value == -6.0
        test_logger.info("✓ EQ validation passed")
    except Exception as e:
        test_logger.error(f"✗ EQ validation failed: {e}")
    
    # Test invalid EQ band
    try:
        validate_eq_update('invalid', 0)
        test_logger.error("✗ Invalid EQ band should have been rejected")
    except ValidationError:
        test_logger.info("✓ Invalid EQ band properly rejected")
    
    # Test response helpers
    success_resp = create_success_response("Test success", {'key': 'value'})
    assert success_resp['success'] == True
    assert success_resp['message'] == "Test success"
    assert success_resp['key'] == 'value'
    
    error_resp = create_error_response("Test error")
    assert error_resp['success'] == False
    assert error_resp['message'] == "Test error"
    
    test_logger.info("✓ Response helpers working correctly")
    test_logger.info("All validation tests completed")

def run_basic_tests():
    """Run basic functionality tests"""
    print("Running basic validation tests...")
    test_validation_functions()
    print("Tests completed.")

if __name__ == '__main__':
    run_basic_tests()
