"""
WiFi Configuration Manager
Handles storing and loading WiFi settings from a configuration file
"""

import json

CONFIG_FILE = 'wifi_config.json'

class WiFiConfig:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            'mode': 'ap',  # Default to AP mode: 'station', 'ap', or 'dual'
            'station': {
                'ssid': '',
                'password': ''
            },
            'ap': {
                'ssid': 'PicoW-Audio',
                'password': 'picowifi'
            }
        }
        
        try:
            # Try to open the file
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                    elif isinstance(default_config[key], dict):
                        for subkey in default_config[key]:
                            if subkey not in config[key]:
                                config[key][subkey] = default_config[key][subkey]
                print(f"[WiFi Config] Loaded configuration from {CONFIG_FILE}")
                return config
        except OSError as e:
            if e.args[0] == 2:  # ENOENT - File not found
                print(f"[WiFi Config] Configuration file not found, creating default config")
                # Create default config file
                try:
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(default_config, f)
                    print(f"[WiFi Config] Created default configuration file: {CONFIG_FILE}")
                except Exception as create_error:
                    print(f"[WiFi Config] Failed to create default config file: {create_error}")
            else:
                print(f"[WiFi Config] OS error loading config: {e}")
        except ValueError as e:
            print(f"[WiFi Config] Invalid JSON in config file: {e}")
        
        return default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f)
            return True
        except Exception as e:
            print(f"Error saving WiFi config: {e}")
            return False
    
    def get_mode(self):
        """Get current WiFi mode"""
        return self.config.get('mode', 'ap')  # Default to AP mode
    
    def set_mode(self, mode):
        """Set WiFi mode ('station', 'ap', or 'dual')"""
        if mode in ['station', 'ap', 'dual']:
            self.config['mode'] = mode
            return self.save_config()
        return False
    
    def get_station_config(self):
        """Get station mode configuration"""
        return self.config.get('station', {'ssid': '', 'password': ''})
    
    def set_station_config(self, ssid, password):
        """Set station mode configuration"""
        self.config['station']['ssid'] = ssid
        self.config['station']['password'] = password
        return self.save_config()
    
    def get_ap_config(self):
        """Get access point configuration"""
        return self.config.get('ap', {'ssid': 'PicoW-Audio', 'password': 'picowifi'})
    
    def set_ap_config(self, ssid, password):
        """Set access point configuration"""
        self.config['ap']['ssid'] = ssid
        self.config['ap']['password'] = password
        return self.save_config()
