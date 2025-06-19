# WiFi Configuration Feature

This document describes the new WiFi configuration feature added to the audio dashboard.

## Overview

The WiFi configuration feature allows users to:

- Switch between Station mode (connect to existing WiFi) and Access Point mode (create WiFi hotspot)
- Scan for available WiFi networks
- Configure network credentials through a user-friendly interface
- Automatically save and restore network settings

## User Interface

### Accessing WiFi Configuration

- Click the WiFi icon (📶) in the top-right corner of the dashboard
- This opens a slide-out drawer with WiFi configuration options

### WiFi Configuration Drawer

The drawer contains several sections:

#### Current Status

Shows the current WiFi mode, connected SSID, and IP address.

#### Station Mode Configuration

- **WiFi Network SSID**: Enter the name of the WiFi network to connect to
- **Password**: Enter the WiFi network password
- **Connect to Network**: Button to initiate connection

#### Access Point Mode Configuration

- **AP Name (SSID)**: Set the name for the access point (default: "PicoW-Audio")
- **AP Password**: Set the password for the access point (minimum 8 characters)
- **Start Access Point**: Button to start the access point

#### Network Scanner

- **Scan for Networks**: Button to scan for available WiFi networks
- **Network List**: Shows discovered networks with signal strength and security status
- Click on any network to auto-fill the SSID field

## Backend Components

### Files Added/Modified

1. **`model/wifi_config.py`**: Configuration management

   - Loads/saves WiFi settings to `wifi_config.json`
   - Manages station and AP mode configurations

2. **`model/wifi_manager.py`**: Network operations

   - Uses existing `mm_wlan` module for station mode connections
   - Handles access point setup with native network module
   - Provides network scanning functionality
   - Manages network mode switching

3. **`static/scripts/wifi-config.js`**: Frontend functionality

   - Handles user interactions in the WiFi drawer
   - Makes API calls to backend endpoints
   - Updates UI based on WiFi status

4. **`main.py`**: Updated with new endpoints

   - `/wifi/status`: Get current WiFi status
   - `/wifi/connect-station`: Connect to WiFi network
   - `/wifi/start-ap`: Start access point mode
   - `/wifi/scan`: Scan for available networks

5. **`templates/dashboard.html`**: Updated with drawer UI
   - Added WiFi configuration drawer
   - Integrated with existing theme system

## API Endpoints

### GET `/wifi/status`

Returns current WiFi status:

```json
{
  "mode": "Station|Access Point|Disconnected",
  "ssid": "network_name",
  "ip": "192.168.1.100",
  "connected": true
}
```

### POST `/wifi/connect-station`

Connect to WiFi network:

```json
{
  "ssid": "network_name",
  "password": "network_password"
}
```

### POST `/wifi/start-ap`

Start access point:

```json
{
  "ssid": "ap_name",
  "password": "ap_password"
}
```

### GET `/wifi/scan`

Scan for networks:

```json
{
  "success": true,
  "networks": [
    {
      "ssid": "network_name",
      "rssi": -45,
      "authmode": 3,
      "channel": 6
    }
  ]
}
```

## Implementation Details

### mm_wlan Integration

The WiFi manager uses the existing `mm_wlan` module for all station mode operations:

- **Station connections**: Uses `mm_wlan.connect_to_network()` for reliable connections
- **Status checking**: Uses `mm_wlan.is_connected()` and `mm_wlan.get_ip()`
- **Network scanning**: Uses the `mm_wlan.wlan` interface for scanning networks
- **Access Point mode**: Uses native `network.WLAN(network.AP_IF)` for AP operations

This ensures consistency with the existing codebase and leverages the proven reliability of the mm_wlan module.

## Configuration Storage

WiFi settings are stored in `wifi_config.json`:

```json
{
  "mode": "station",
  "station": {
    "ssid": "MyWiFi",
    "password": "password123"
  },
  "ap": {
    "ssid": "PicoW-Audio",
    "password": "picowifi"
  }
}
```

## Usage Flow

1. **Initial Setup**: Device attempts to connect using saved station credentials
2. **Fallback**: If no station config or connection fails, starts in AP mode
3. **User Configuration**: Users can switch modes and update credentials via the drawer
4. **Persistence**: All settings are automatically saved and restored on restart

## Design Integration

The WiFi configuration drawer follows the existing design system:

- Uses DaisyUI components and themes
- Matches the gradient styling and color scheme
- Responsive design works on mobile and desktop
- Integrated with the existing theme selector

## Security Considerations

- Passwords are not displayed in plain text in the UI
- Configuration file contains sensitive data and should be protected
- AP mode requires minimum 8-character passwords
- Network scanning is performed securely without exposing credentials
