/**
 * WiFi Configuration Manager
 * Handles Access Point and Station mode configuration
 */
class WiFiConfigManager {
  constructor() {
    this.init();
  }

  init() {
    this.bindEvents();
    this.loadCurrentStatus();
  }

  bindEvents() {
    // Drawer toggle - load status when opened
    document
      .getElementById("ap-config-drawer")
      .addEventListener("change", (e) => {
        if (e.target.checked) {
          this.loadCurrentStatus();
        }
      });

    // Station mode connection
    document
      .getElementById("connect-station-btn")
      .addEventListener("click", () => {
        this.connectToStation();
      });

    // Device restart
    document
      .getElementById("restart-device-btn")
      .addEventListener("click", () => {
        this.restartDevice();
      });

    // AP mode start
    document.getElementById("start-ap-btn").addEventListener("click", () => {
      this.startAccessPoint();
    });

    // Network scan
    document
      .getElementById("scan-networks-btn")
      .addEventListener("click", () => {
        this.scanNetworks();
      });

    // Auto-fill SSID when clicking on scanned network
    document.addEventListener("click", (e) => {
      if (e.target.closest(".network-item")) {
        const networkItem = e.target.closest(".network-item");
        const ssid = networkItem.dataset.ssid;
        document.getElementById("station-ssid").value = ssid;
      }
    });
  }

  async loadCurrentStatus() {
    try {
      const response = await fetch("/wifi/status");
      if (response.ok) {
        const status = await response.json();
        this.updateStatusDisplay(status);
      }
    } catch (error) {
      console.error("Failed to load WiFi status:", error);
    }
  }

  updateStatusDisplay(status) {
    document.getElementById("current-wifi-mode").textContent = status.mode;
    document.getElementById("current-ssid").textContent = status.ssid || "-";
    document.getElementById("current-ip").textContent = status.ip || "-";

    // Update badge colors based on mode
    const modeBadge = document.getElementById("current-wifi-mode");
    modeBadge.className = "badge badge-sm";

    if (status.mode === "Access Point") {
      modeBadge.classList.add("badge-secondary");
    } else if (status.mode === "Station" && status.connected) {
      modeBadge.classList.add("badge-success");
    } else {
      modeBadge.classList.add("badge-warning");
    }
  }

  async connectToStation() {
    const ssid = document.getElementById("station-ssid").value.trim();
    const password = document.getElementById("station-password").value;

    if (!ssid) {
      this.showStatus("Please enter a WiFi network name", "error");
      return;
    }

    if (!password) {
      this.showStatus("Please enter the WiFi password", "error");
      return;
    }

    this.showStatus("Connecting to WiFi network...", "info");

    try {
      const response = await fetch("/wifi/connect-station", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ssid: ssid,
          password: password,
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        if (result.restart_required) {
          this.showStatus(
            "Configuration saved! Device restart required.",
            "warning"
          );

          // Show restart button
          document
            .getElementById("restart-device-btn")
            .classList.remove("hidden");

          // Show restart instruction
          setTimeout(() => {
            this.showStatus(
              "Please restart the device to connect to the WiFi network.",
              "info"
            );
          }, 3000);

          // Clear password field for security
          document.getElementById("station-password").value = "";
        } else {
          this.showStatus(
            `Connected successfully! IP: ${result.ip}`,
            "success"
          );
          this.loadCurrentStatus();

          // Clear password field for security
          document.getElementById("station-password").value = "";

          // Note: Page might reload due to network change
          setTimeout(() => {
            if (result.ip && result.ip !== window.location.hostname) {
              this.showStatus("Network changed. Redirecting...", "info");
              setTimeout(() => {
                window.location.hostname = result.ip;
              }, 2000);
            }
          }, 3000);
        }
      } else {
        this.showStatus(result.message || "Connection failed", "error");
      }
    } catch (error) {
      console.error("Station connection error:", error);
      this.showStatus(
        "Failed to connect. Please check your credentials.",
        "error"
      );
    }
  }

  async startAccessPoint() {
    const ssid =
      document.getElementById("ap-ssid").value.trim() || "PicoW-Audio";
    const password = document.getElementById("ap-password").value;

    if (password && password.length < 8) {
      this.showStatus("Password must be at least 8 characters long", "error");
      return;
    }

    this.showStatus("Starting Access Point...", "info");

    try {
      const response = await fetch("/wifi/start-ap", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ssid: ssid,
          password: password || "picowifi",
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        this.showStatus(
          `Access Point started! Connect to "${result.ssid}"`,
          "success"
        );
        this.loadCurrentStatus();

        // Clear password field
        document.getElementById("ap-password").value = "";

        // Show connection info
        setTimeout(() => {
          this.showStatus(
            `AP IP: ${result.ip} | Password: ${result.password}`,
            "info"
          );
        }, 2000);
      } else {
        this.showStatus(
          result.message || "Failed to start Access Point",
          "error"
        );
      }
    } catch (error) {
      console.error("AP start error:", error);
      this.showStatus("Failed to start Access Point", "error");
    }
  }

  async scanNetworks() {
    const scanBtn = document.getElementById("scan-networks-btn");
    const networkList = document.getElementById("network-list");

    // Update button state
    scanBtn.disabled = true;
    scanBtn.textContent = "Scanning...";

    try {
      const response = await fetch("/wifi/scan");
      const result = await response.json();

      if (response.ok && result.success) {
        this.displayNetworks(result.networks);
      } else {
        networkList.innerHTML = `
          <div class="text-xs text-error text-center py-2">
            ${result.message || "Scan failed"}
          </div>
        `;
      }
    } catch (error) {
      console.error("Network scan error:", error);
      networkList.innerHTML = `
        <div class="text-xs text-error text-center py-2">
          Failed to scan networks
        </div>
      `;
    } finally {
      // Reset button state
      scanBtn.disabled = false;
      scanBtn.textContent = "Scan for Networks";
    }
  }

  displayNetworks(networks) {
    const networkList = document.getElementById("network-list");

    if (!networks || networks.length === 0) {
      networkList.innerHTML = `
        <div class="text-xs text-base-content/60 text-center py-2">
          No networks found
        </div>
      `;
      return;
    }

    const networkItems = networks
      .map((network) => {
        const signalStrength = this.getSignalStrengthIcon(network.rssi);
        const securityIcon = network.authmode > 0 ? "🔒" : "🔓";

        return `
        <div class="network-item flex items-center justify-between p-2 hover:bg-base-200 rounded cursor-pointer border border-transparent hover:border-base-300" data-ssid="${network.ssid}">
          <div class="flex items-center gap-2">
            <span class="text-xs">${securityIcon}</span>
            <span class="text-sm font-mono">${network.ssid}</span>
          </div>
          <div class="flex items-center gap-1">
            <span class="text-xs text-base-content/60">${signalStrength}</span>
            <span class="text-xs text-base-content/60">${network.rssi}dBm</span>
          </div>
        </div>
      `;
      })
      .join("");

    networkList.innerHTML = networkItems;
  }

  getSignalStrengthIcon(rssi) {
    if (rssi >= -50) return "📶"; // Excellent
    if (rssi >= -60) return ""; // Good
    if (rssi >= -70) return "📱"; // Fair
    return "📵"; // Poor
  }

  showStatus(message, type = "info") {
    const statusDiv = document.getElementById("wifi-status");
    const statusText = document.getElementById("wifi-status-text");

    statusText.textContent = message;
    statusDiv.className = `alert alert-${type} alert-sm`;
    statusDiv.classList.remove("hidden");

    // Auto-hide after 5 seconds
    setTimeout(() => {
      statusDiv.classList.add("hidden");
    }, 5000);
  }

  async restartDevice() {
    if (!confirm("Are you sure you want to restart the device?")) {
      return;
    }

    this.showStatus("Restarting device...", "info");

    try {
      const response = await fetch("/wifi/restart", {
        method: "POST",
      });

      if (response.ok) {
        this.showStatus("Device is restarting. Please wait...", "info");

        // Hide the restart button
        document.getElementById("restart-device-btn").classList.add("hidden");

        // Try to reconnect after restart
        setTimeout(() => {
          this.showStatus("Attempting to reconnect...", "info");
          setTimeout(() => {
            window.location.reload();
          }, 5000);
        }, 10000);
      } else {
        this.showStatus("Failed to restart device", "error");
      }
    } catch (error) {
      console.error("Restart error:", error);
      this.showStatus("Failed to restart device", "error");
    }
  }
}

export default WiFiConfigManager;
