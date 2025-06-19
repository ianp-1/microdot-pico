# WiFi Configuration Test Server

This test server allows you to test all the WiFi configuration features locally without needing actual WiFi hardware.

## Running the Test Server

1. **Install Dependencies** (if not already installed):

   ```bash
   pip install microdot
   ```

2. **Start the Test Server**:

   ```bash
   python test_server.py
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:8000`

## Testing Features

### WiFi Configuration Testing

The test server simulates all WiFi functionality:

#### **Access Point Mode** (Default)

- Server starts in AP mode
- Default AP name: `PicoW-Audio-Test`
- Default IP: `192.168.4.1`
- You can change AP settings through the UI

#### **Station Mode Testing**

- Enter any SSID and password to test station mode
- The system will save the configuration and show "restart required"
- Click the restart button to simulate the restart process
- After "restart," the server simulates connecting to the station network

#### **Network Scanning**

The test server provides mock networks for testing:

- `TestNetwork_5G` (Strong signal, -45dBm, Secured)
- `MyWiFi` (Good signal, -55dBm, Secured)
- `OpenNetwork` (Fair signal, -65dBm, Open)
- `WeakSignal` (Poor signal, -80dBm, Secured)
- `Office_Guest` (Good signal, -50dBm, Secured)

Click on any network in the scan results to auto-fill the SSID field.

#### **Error Testing**

Test error scenarios:

- **Network not found**: Use SSID `failtest`
- **Wrong password**: Use password `wrong`
- **Short password**: Try AP password with less than 8 characters

### UI Testing

#### **Drawer Functionality**

- Click the WiFi icon (📶) in the top-right to open the configuration drawer
- Test theme switching with the theme dropdown
- All UI components should be responsive

#### **Status Updates**

- Status badge colors change based on connection state
- Real-time status updates when switching modes
- Toast notifications for all operations

#### **Form Validation**

- Required field validation (SSID, password)
- Password length validation for AP mode
- Proper error messages for all scenarios

### Audio Dashboard Testing

The test server also provides mock audio functionality:

- EQ controls with random values
- Voice mode toggling
- Ducking and feedback controls
- All buttons return random states for testing

## Console Output

The server provides detailed console output for debugging:

```
[TEST] WiFi status requested - Mode: ap
[TEST] Station connection requested: MyWiFi
[TEST] Station config saved: MyWiFi
[TEST] Network scan requested
[TEST] Found 5 networks
[TEST] Device restart requested
```

## Development Notes

### Mock State Management

The server maintains WiFi state in memory:

- Current mode (AP/Station)
- Configuration settings
- Connection status
- IP addresses

### Realistic Behavior

- Station mode always requires restart (as in real implementation)
- AP mode switches immediately
- Network scan includes realistic signal strengths
- Proper error handling and responses

### File Structure

The test server uses the same file structure as the main application:

- Serves files from `static/` directory
- Uses `templates/dashboard.html`
- Same API endpoints as main application

## Troubleshooting

**Port already in use:**

```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Missing files:**
Make sure you're running from the project root directory where `static/` and `templates/` folders exist.

**Module not found:**
Install microdot if not already installed:

```bash
pip install microdot
```

## Testing Checklist

Use this checklist to test all features:

- [ ] **Basic UI**

  - [ ] Dashboard loads correctly
  - [ ] WiFi drawer opens/closes
  - [ ] Theme switching works
  - [ ] All buttons are clickable

- [ ] **WiFi Status**

  - [ ] Current status displays correctly
  - [ ] Status updates when mode changes
  - [ ] Badge colors change appropriately

- [ ] **Network Scanning**

  - [ ] Scan button works
  - [ ] Networks display with signal strength
  - [ ] Clicking networks auto-fills SSID
  - [ ] Security icons show correctly

- [ ] **Station Mode**

  - [ ] Can enter SSID and password
  - [ ] Validation works (required fields)
  - [ ] Success shows restart required message
  - [ ] Restart button appears and works
  - [ ] Error scenarios work (failtest, wrong password)

- [ ] **Access Point Mode**

  - [ ] Can configure AP name and password
  - [ ] Password validation (8+ characters)
  - [ ] AP starts immediately
  - [ ] Status updates correctly

- [ ] **Audio Controls** (Basic functionality)
  - [ ] EQ sliders work
  - [ ] Voice mode button responds
  - [ ] Ducking/feedback toggles work

This test environment provides a complete testing platform for all WiFi configuration features!
