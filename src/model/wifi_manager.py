"""
WiFi Manager
Handles WiFi network connections and access point operations
"""

import network
import time
import uasyncio as asyncio
import lib.mm_wlan as mm_wlan
from lib.mm_wlan.mm_wlan import wlan as mm_wlan_interface
from model.wifi_config import WiFiConfig

class WiFiManager:
    def __init__(self):
        self.config = WiFiConfig()
        self.ap_if = network.WLAN(network.AP_IF)
        self.current_mode = None
        self.current_ssid = None
        self.current_ip = None
    
    async def setup_network(self):
        """Setup network based on configuration mode"""
        mode = self.config.get_mode()
        print(f"[WiFi] Setting up network in {mode} mode")
        
        if mode == 'station':
            # Station mode only
            result = await self.connect_to_saved_station()
            return result
        elif mode == 'dual':
            # Dual mode: Start AP first, then try to connect to station
            print("[WiFi] Starting dual mode (AP + Station)")
            ap_config = self.config.get_ap_config()
            ap_result = await self.start_access_point(ap_config['ssid'], ap_config['password'], save_config=False, dual_mode=True)
            
            if ap_result.get('success'):
                # Try to connect to station network as well
                station_result = await self.connect_to_saved_station()
                if station_result.get('success'):
                    self.current_mode = 'dual'
                    print("[WiFi] Dual mode active: AP + Station")
                    return {
                        'success': True,
                        'mode': 'dual',
                        'ap': ap_result,
                        'station': station_result
                    }
                else:
                    # Station connection failed, fall back to AP only mode
                    print("[WiFi] Dual mode: AP active, station connection failed - falling back to AP mode")
                    self.current_mode = 'ap'
                    self.config.set_mode('ap')  # Update config to reflect actual state
                    ap_result['mode'] = 'ap'  # Update result mode
            return ap_result
        else:
            # Default to AP mode only
            print("[WiFi] Starting in AP mode")
            ap_config = self.config.get_ap_config()
            return await self.start_access_point(ap_config['ssid'], ap_config['password'], save_config=False)
    
    async def connect_to_station(self, ssid, password, save_config=True):
        """Connect to a WiFi network in station mode using mm_wlan - requires restart"""
        print(f"[WiFi] Preparing station connection to: {ssid}")
        
        try:
            # Save configuration first
            if save_config:
                self.config.set_station_config(ssid, password)
                self.config.set_mode('station')
                print("[WiFi] Station configuration saved")
            
            # Return success but indicate restart is required
            return {
                'success': True,
                'restart_required': True,
                'message': 'Configuration saved. Device restart required to switch to station mode.',
                'ssid': ssid,
                'mode': 'station'
            }
            
        except Exception as e:
            print(f"[WiFi] Station configuration failed: {e}")
            return {
                'success': False,
                'restart_required': False,
                'message': str(e)
            }
    
    async def start_access_point(self, ssid, password, save_config=True, dual_mode=False):
        """Start the device as an access point"""
        print(f"[WiFi] Starting Access Point: {ssid}")
        
        # Only deactivate station mode if not in dual mode
        if not dual_mode and mm_wlan_interface.active():
            print("[WiFi] Deactivating station interface for AP-only mode")
            mm_wlan_interface.active(False)
            await asyncio.sleep(1)
        
        try:
            # Activate AP mode
            self.ap_if.active(True)
            await asyncio.sleep(1)
            
            # Configure the access point
            self.ap_if.config(essid=ssid, password=password)
            
            # Wait for AP to become active
            max_wait = 15
            while max_wait > 0:
                if self.ap_if.active() and self.ap_if.ifconfig()[0] != '0.0.0.0':
                    break
                print(f"[WiFi] Starting AP... {max_wait}")
                await asyncio.sleep(1)
                max_wait -= 1
            
            if not self.ap_if.active() or self.ap_if.ifconfig()[0] == '0.0.0.0':
                raise Exception("Failed to start access point")
            
            # AP started successfully
            ip_info = self.ap_if.ifconfig()
            self.current_mode = 'ap'
            self.current_ssid = ssid
            self.current_ip = ip_info[0]
            
            print(f"[WiFi] Access Point started: {ssid}")
            print(f"[WiFi] AP IP Address: {self.current_ip}")
            print(f"[WiFi] Connect with password: {password}")
            
            # Save configuration if requested
            if save_config:
                self.config.set_ap_config(ssid, password)
                self.config.set_mode('ap')
            
            return {
                'success': True,
                'ip': self.current_ip,
                'ssid': ssid,
                'password': password,
                'mode': 'ap'
            }
            
        except Exception as e:
            print(f"[WiFi] Access Point start failed: {e}")
            self.current_mode = None
            self.current_ssid = None
            self.current_ip = None
            return {
                'success': False,
                'message': str(e)
            }
    
    def scan_networks(self):
        """Scan for available WiFi networks using mm_wlan interface"""
        print("[WiFi] Scanning for networks...")
        
        try:
            # Use mm_wlan's station interface for scanning
            if not mm_wlan_interface.active():
                mm_wlan_interface.active(True)
                time.sleep(1)
            
            # Perform scan
            networks = mm_wlan_interface.scan()
            
            # Process and sort networks
            network_list = []
            seen_ssids = set()  # Avoid duplicates
            
            for network_info in networks:
                ssid = network_info[0].decode('utf-8')
                # Skip hidden networks and duplicates
                if ssid and ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    network_list.append({
                        'ssid': ssid,
                        'bssid': ':'.join(['%02x' % b for b in network_info[1]]),
                        'channel': network_info[2],
                        'rssi': network_info[3],
                        'authmode': network_info[4],
                        'hidden': network_info[5]
                    })
            
            # Sort by signal strength (RSSI)
            network_list.sort(key=lambda x: x['rssi'], reverse=True)
            
            print(f"[WiFi] Found {len(network_list)} networks")
            return {
                'success': True,
                'networks': network_list
            }
            
        except Exception as e:
            print(f"[WiFi] Network scan failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_status(self):
        """Get current WiFi status (simplified version for backward compatibility)"""
        detailed = self.get_current_status_detailed()
        
        if detailed['mode'] == 'dual':
            return {
                'mode': 'Dual (AP + Station)',
                'ssid': f"AP: {detailed['ap']['ssid']}, STA: {detailed['station']['ssid']}",
                'ip': f"AP: {detailed['ap']['ip']}, STA: {detailed['station']['ip']}",
                'connected': True
            }
        elif detailed['mode'] == 'station' and detailed['station']['connected']:
            return {
                'mode': 'Station',
                'ssid': detailed['station']['ssid'],
                'ip': detailed['station']['ip'],
                'connected': True
            }
        elif detailed['mode'] == 'ap' and detailed['ap']['active']:
            return {
                'mode': 'Access Point',
                'ssid': detailed['ap']['ssid'],
                'ip': detailed['ap']['ip'],
                'connected': True
            }
        else:
            return {
                'mode': 'Disconnected',
                'ssid': None,
                'ip': None,
                'connected': False
            }
    
    async def connect_to_saved_station(self):
        """Connect to saved station network - used during startup"""
        station_config = self.config.get_station_config()
        if not station_config['ssid']:
            return {'success': False, 'message': 'No saved station configuration'}
        
        print(f"[WiFi] Connecting to saved station: {station_config['ssid']}")
        
        try:
            # Use mm_wlan for station connection with manual timeout handling
            start_time = time.time()
            timeout = 20  # 20 second timeout
            
            # Start connection attempt
            mm_wlan_interface.active(True)
            await asyncio.sleep(1)
            
            # Connect with shorter retries to allow for timeout handling
            try:
                mm_wlan.connect_to_network(station_config['ssid'], station_config['password'], retries=5, verbose=True)
            except Exception as connect_error:
                print(f"[WiFi] Connection attempt failed: {connect_error}")
            
            # Wait for connection with timeout
            while time.time() - start_time < timeout:
                if mm_wlan.is_connected():
                    ip_address = mm_wlan.get_ip()
                    self.current_mode = 'station'
                    self.current_ssid = station_config['ssid']
                    self.current_ip = ip_address
                    
                    print(f"[WiFi] Connected to {station_config['ssid']}")
                    print(f"[WiFi] IP Address: {self.current_ip}")
                    
                    return {
                        'success': True,
                        'ip': self.current_ip,
                        'ssid': station_config['ssid'],
                        'mode': 'station'
                    }
                
                await asyncio.sleep(1)  # Non-blocking delay
            
            # Timeout reached
            print(f"[WiFi] Station connection timeout after {timeout} seconds")
            raise Exception("Connection timeout")
                
        except Exception as e:
            print(f"[WiFi] Station connection failed: {e}")
            # Fall back to AP mode
            print("[WiFi] Falling back to AP mode")
            self.config.set_mode('ap')
            ap_config = self.config.get_ap_config()
            return await self.start_access_point(ap_config['ssid'], ap_config['password'])
    
    async def set_network_mode(self, mode, restart_required=True):
        """Set network mode and optionally restart"""
        print(f"[WiFi] Setting network mode to: {mode}")
        
        if mode not in ['station', 'ap', 'dual']:
            return {'success': False, 'message': 'Invalid network mode'}
        
        # Save the new mode
        self.config.set_mode(mode)
        
        if restart_required:
            return {
                'success': True,
                'restart_required': True,
                'message': f'Network mode set to {mode}. Device restart required to apply changes.',
                'mode': mode
            }
        else:
            # Try to apply immediately (limited support)
            result = await self.setup_network()
            return result
    
    def get_current_status_detailed(self):
        """Get detailed status including both interfaces"""
        status = {
            'mode': self.current_mode or 'unknown',
            'station': {
                'connected': False,
                'ssid': None,
                'ip': None
            },
            'ap': {
                'active': False,
                'ssid': None,
                'ip': None
            }
        }
        
        # Check station interface
        station_connected = False
        try:
            if mm_wlan.is_connected():
                status['station']['connected'] = True
                status['station']['ssid'] = self.current_ssid if self.current_ssid else 'Connected'
                status['station']['ip'] = mm_wlan.get_ip()
                station_connected = True
        except Exception as e:
            print(f"[WiFi] Station check error: {e}")
        
        # Check AP interface
        ap_active = False
        try:
            if self.ap_if.active() and self.ap_if.ifconfig()[0] != '0.0.0.0':
                status['ap']['active'] = True
                ap_config = self.config.get_ap_config()
                status['ap']['ssid'] = ap_config['ssid']
                status['ap']['ip'] = self.ap_if.ifconfig()[0]
                ap_active = True
        except Exception as e:
            print(f"[WiFi] AP check error: {e}")
        
        # Determine actual mode based on what's actually running
        if station_connected and ap_active:
            status['mode'] = 'dual'
            self.current_mode = 'dual'  # Update our internal state
        elif station_connected:
            status['mode'] = 'station'
            self.current_mode = 'station'
        elif ap_active:
            status['mode'] = 'ap'
            self.current_mode = 'ap'
        else:
            status['mode'] = 'disconnected'
            self.current_mode = None
        
        # If the actual mode doesn't match config, log it (but don't auto-update config 
        # as that could cause issues if user intentionally set a mode that requires restart)
        config_mode = self.config.get_mode()
        if config_mode != status['mode'] and status['mode'] != 'disconnected':
            print(f"[WiFi] Config mode ({config_mode}) doesn't match actual mode ({status['mode']})")
        
        return status
    
    async def connect_to_station_dual_mode(self, ssid, password):
        """Connect to a WiFi network while keeping AP active (dual mode)"""
        print(f"[WiFi] Connecting to station in dual mode: {ssid}")
        
        try:
            # Save station configuration
            self.config.set_station_config(ssid, password)
            
            # Use mm_wlan for station connection without disrupting AP
            mm_wlan.connect_to_network(ssid, password, retries=15, verbose=True)
            
            # Check if connection was successful
            if mm_wlan.is_connected():
                station_ip = mm_wlan.get_ip()
                print(f"[WiFi] Station connected: {ssid} ({station_ip})")
                
                # Update mode to dual if AP is also active
                if self.ap_if.active():
                    self.current_mode = 'dual'
                    print("[WiFi] Dual mode now active")
                else:
                    self.current_mode = 'station'
                
                return {
                    'success': True,
                    'ip': station_ip,
                    'ssid': ssid,
                    'mode': self.current_mode
                }
            else:
                raise Exception("Failed to obtain IP address")
                
        except Exception as e:
            print(f"[WiFi] Dual mode station connection failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }
