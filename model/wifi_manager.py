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
        """Setup network - check for station mode, otherwise default to AP"""
        mode = self.config.get_mode()
        print(f"[WiFi] Setting up network in {mode} mode")
        
        if mode == 'station':
            # Try to connect to saved station network
            result = await self.connect_to_saved_station()
            return result
        else:
            # Default to AP mode
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
    
    async def start_access_point(self, ssid, password, save_config=True):
        """Start the device as an access point"""
        print(f"[WiFi] Starting Access Point: {ssid}")
        
        # Deactivate station mode if active (using mm_wlan interface)
        if mm_wlan_interface.active():
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
        """Get current WiFi status"""
        if self.current_mode == 'station' and mm_wlan.is_connected():
            return {
                'mode': 'Station',
                'ssid': self.current_ssid,
                'ip': mm_wlan.get_ip(),
                'connected': True
            }
        elif self.current_mode == 'ap' and self.ap_if.active():
            return {
                'mode': 'Access Point',
                'ssid': self.current_ssid,
                'ip': self.current_ip,
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
            # Use mm_wlan for station connection
            mm_wlan.connect_to_network(station_config['ssid'], station_config['password'], retries=15, verbose=True)
            
            # Connection successful - get IP info
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
            else:
                raise Exception("Connection failed - no IP address obtained")
                
        except Exception as e:
            print(f"[WiFi] Station connection failed: {e}")
            # Fall back to AP mode
            print("[WiFi] Falling back to AP mode")
            self.config.set_mode('ap')
            ap_config = self.config.get_ap_config()
            return await self.start_access_point(ap_config['ssid'], ap_config['password'])
