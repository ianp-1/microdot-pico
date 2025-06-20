"""
WiFi route handlers
"""
import machine
import uasyncio as asyncio
from .utils import (
    ValidationError, 
    validate_wifi_mode, 
    validate_wifi_credentials,
    create_success_response, 
    create_error_response,
    safe_json_parse
)
from .config import DEFAULT_AP_SSID, DEFAULT_AP_PASSWORD
from .logger import wifi_logger

class WiFiRoutes:
    def __init__(self, wifi_manager):
        self.wifi_manager = wifi_manager
        self.logger = wifi_logger
    
    def get_status(self, request):
        """Return current WiFi status"""
        try:
            return self.wifi_manager.get_status()
        except Exception as e:
            self.logger.exception("Status error", e)
            return create_error_response("Failed to get WiFi status")
    
    def get_status_detailed(self, request):
        """Return detailed WiFi status"""
        try:
            return self.wifi_manager.get_current_status_detailed()
        except Exception as e:
            self.logger.exception("Detailed status error", e)
            return create_error_response("Failed to get detailed WiFi status")
    
    def get_config(self, request):
        """Return saved WiFi configuration for autofill"""
        try:
            config = self.wifi_manager.config
            return create_success_response("Configuration retrieved", {
                'config': {
                    'mode': config.get_mode(),
                    'station': config.get_station_config(),
                    'ap': config.get_ap_config()
                }
            })
        except Exception as e:
            self.logger.exception("Config fetch error", e)
            return create_error_response("Failed to fetch configuration")
    
    async def set_mode(self, request):
        """Set network mode (station, ap, dual)"""
        try:
            data = safe_json_parse(request.body)
            mode = validate_wifi_mode(data.get('mode', '').strip().lower())
            restart_required = data.get('restart_required', True)
            
            result = await self.wifi_manager.set_network_mode(mode, restart_required)
            return result
            
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("Set mode error", e)
            return create_error_response("Failed to set network mode")
    
    async def connect_station(self, request):
        """Connect to a WiFi network in station mode"""
        try:
            data = safe_json_parse(request.body)
            ssid, password = validate_wifi_credentials(
                data.get('ssid', ''), 
                data.get('password', '')
            )
            
            result = await self.wifi_manager.connect_to_station(ssid, password)
            return result
            
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("Station connect error", e)
            return create_error_response("Connection failed")
    
    async def connect_station_dual(self, request):
        """Connect to a WiFi network while keeping AP active (dual mode)"""
        try:
            data = safe_json_parse(request.body)
            ssid, password = validate_wifi_credentials(
                data.get('ssid', ''), 
                data.get('password', '')
            )
            
            result = await self.wifi_manager.connect_to_station_dual_mode(ssid, password)
            return result
            
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("Dual station connect error", e)
            return create_error_response("Connection failed")
    
    async def start_ap(self, request):
        """Start the device as an access point"""
        try:
            data = safe_json_parse(request.body)
            ssid = data.get('ssid', DEFAULT_AP_SSID).strip()
            password = data.get('password', DEFAULT_AP_PASSWORD)
            
            # Validate credentials
            ssid, password = validate_wifi_credentials(ssid, password)
            
            result = await self.wifi_manager.start_access_point(ssid, password)
            return result
            
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("AP start error", e)
            return create_error_response("Failed to start Access Point")
    
    def scan_networks(self, request):
        """Scan for available WiFi networks"""
        try:
            return self.wifi_manager.scan_networks()
        except Exception as e:
            self.logger.exception("Scan error", e)
            return create_error_response("Failed to scan networks")
    
    def restart_device(self, request):
        """Restart the device to apply WiFi configuration changes"""
        try:
            self.logger.info("Device restart requested")
            
            async def delayed_restart():
                await asyncio.sleep(1)
                machine.reset()
            
            asyncio.create_task(delayed_restart())
            return create_success_response("Device restarting...")
            
        except Exception as e:
            self.logger.exception("Restart error", e)
            return create_error_response("Failed to restart device")
    
    def save_station_config(self, request):
        """Save station configuration to file"""
        try:
            data = safe_json_parse(request.body)
            ssid, password = validate_wifi_credentials(
                data.get('ssid', ''), 
                data.get('password', '')
            )
            
            success = self.wifi_manager.config.set_station_config(ssid, password)
            
            if success:
                return create_success_response(f'WiFi configuration saved for network: {ssid}')
            else:
                return create_error_response('Failed to save configuration')
                
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("Save station config error", e)
            return create_error_response("Failed to save configuration")
    
    def save_ap_config(self, request):
        """Save access point configuration to file"""
        try:
            data = safe_json_parse(request.body)
            ssid, password = validate_wifi_credentials(
                data.get('ssid', ''), 
                data.get('password', '')
            )
            
            success = self.wifi_manager.config.set_ap_config(ssid, password)
            
            if success:
                return create_success_response(f'Access Point configuration saved: {ssid}')
            else:
                return create_error_response('Failed to save configuration')
                
        except ValidationError as e:
            return create_error_response(str(e))
        except Exception as e:
            self.logger.exception("Save AP config error", e)
            return create_error_response("Failed to save configuration")
