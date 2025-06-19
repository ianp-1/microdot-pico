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
    this.loadConfigForAutofill();
    this.updateConnectButtonText();
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

    // Network mode selection
    document
      .getElementById("apply-network-mode-btn")
      .addEventListener("click", () => {
        this.applyNetworkMode();
      });

    // Update button text when network mode changes
    document
      .getElementById("network-mode-select")
      .addEventListener("change", () => {
        this.updateConnectButtonText();
        this.hideRestartButtonIfModeUnchanged();
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
  hideRestartButtonIfModeUnchanged() {
    // Hide restart button when user is just browsing modes without applying
    const restartBtn = document.getElementById("restart-device-btn");
    if (restartBtn && !restartBtn.classList.contains("hidden")) {
      // Only hide if user is changing modes but hasn't applied yet
      // The button will show again when they actually apply a mode change
      const currentModeEl = document.getElementById("current-wifi-mode");
      const selectedModeEl = document.getElementById("network-mode-select");

      if (currentModeEl && selectedModeEl) {
        const currentMode = currentModeEl.textContent.toLowerCase();
        const selectedMode = selectedModeEl.value;

        // If they're selecting the same mode that's currently active, hide restart button
        if (
          currentMode.includes(selectedMode) ||
          selectedMode === currentMode
        ) {
          restartBtn.classList.add("hidden");
        }
      }
    }
  }

  updateConnectButtonText() {
    const networkModeSelect = document.getElementById("network-mode-select");
    const connectButton = document.getElementById("connect-station-btn");
    const apButton = document.getElementById("start-ap-btn");

    if (networkModeSelect && connectButton) {
      const selectedMode = networkModeSelect.value;

      // Update station button
      switch (selectedMode) {
        case "dual":
          connectButton.textContent = "Connect to WiFi (Dual Mode)";
          connectButton.disabled = false;
          connectButton.classList.remove("btn-disabled");
          break;
        case "station":
          connectButton.textContent = "Save and Connect to WiFi";
          connectButton.disabled = false;
          connectButton.classList.remove("btn-disabled");
          break;
        default: // AP mode
          connectButton.textContent = "WiFi Unavailable (AP Mode)";
          connectButton.disabled = true;
          connectButton.classList.add("btn-disabled");
      }

      // Update AP button
      if (apButton) {
        switch (selectedMode) {
          case "dual":
          case "ap":
            apButton.disabled = false;
            apButton.classList.remove("btn-disabled");
            break;
          default: // Station mode
            apButton.disabled = true;
            apButton.classList.add("btn-disabled");
        }
      }

      // Update visual indicators for sections
      this.updateSectionAvailability(selectedMode);
    }
  }

  updateSectionAvailability(selectedMode) {
    // Find the collapse sections by traversing from buttons
    const connectButton = document.getElementById("connect-station-btn");
    const apButton = document.getElementById("start-ap-btn");

    if (connectButton) {
      const stationSection = connectButton.closest(".collapse");
      if (stationSection) {
        const stationTitle = stationSection.querySelector(".collapse-title");
        if (selectedMode === "station" || selectedMode === "dual") {
          stationSection.classList.remove("opacity-50");
          if (stationTitle)
            stationTitle.classList.remove("text-base-content/50");
        } else {
          stationSection.classList.add("opacity-50");
          if (stationTitle) stationTitle.classList.add("text-base-content/50");
        }
      }
    }

    if (apButton) {
      const apSection = apButton.closest(".collapse");
      if (apSection) {
        const apTitle = apSection.querySelector(".collapse-title");
        if (selectedMode === "ap" || selectedMode === "dual") {
          apSection.classList.remove("opacity-50");
          if (apTitle) apTitle.classList.remove("text-base-content/50");
        } else {
          apSection.classList.add("opacity-50");
          if (apTitle) apTitle.classList.add("text-base-content/50");
        }
      }
    }
  }

  async applyNetworkMode() {
    const selectedMode = document.getElementById("network-mode-select").value;

    if (!selectedMode) {
      this.showToast("Please select a network mode", "error");
      return;
    }

    this.showToast("Applying network mode...", "info");

    try {
      const response = await fetch("/wifi/set-mode", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mode: selectedMode,
          restart_required: true,
        }),
      });

      const result = await response.json();

      if (result.success) {
        if (result.restart_required) {
          this.showToast(
            `Network mode set to ${selectedMode}. Device will restart to apply changes.`,
            "success"
          );
          // Show restart button
          const restartBtn = document.getElementById("restart-device-btn");
          restartBtn.classList.remove("hidden");
          restartBtn.textContent = `Restart for ${
            selectedMode.charAt(0).toUpperCase() + selectedMode.slice(1)
          } Mode`;
        } else {
          this.showToast(`Network mode applied: ${selectedMode}`, "success");
          this.loadCurrentStatus();
        }
      } else {
        this.showToast(result.message || "Failed to set network mode", "error");
      }
    } catch (error) {
      console.error("Network mode setting failed:", error);
      this.showToast("Network error occurred", "error");
    }
  }

  async loadCurrentStatus() {
    try {
      const response = await fetch("/wifi/status-detailed");
      if (response.ok) {
        const detailedStatus = await response.json();
        this.updateStatusDisplay(detailedStatus);
        this.updateNetworkModeSelector(detailedStatus.mode);
      } else {
        // Fallback to basic status
        const basicResponse = await fetch("/wifi/status");
        if (basicResponse.ok) {
          const status = await basicResponse.json();
          this.updateStatusDisplayBasic(status);
        }
      }
    } catch (error) {
      console.error("Failed to load WiFi status:", error);
    }
  }

  updateNetworkModeSelector(currentMode) {
    const selector = document.getElementById("network-mode-select");
    if (selector && currentMode) {
      // Map current mode to selector values
      const modeMap = {
        station: "station",
        ap: "ap",
        dual: "dual",
        disconnected: "ap", // default
      };

      selector.value = modeMap[currentMode] || "ap";
    }
  }

  updateStatusDisplay(detailedStatus) {
    const mode = detailedStatus.mode;
    const station = detailedStatus.station;
    const ap = detailedStatus.ap;

    let displayMode = "";
    let displaySSID = "";
    let displayIP = "";

    if (mode === "dual") {
      displayMode = "Dual (AP + Station)";
      displaySSID = `AP: ${ap.ssid || "-"}, STA: ${station.ssid || "-"}`;
      displayIP = `AP: ${ap.ip || "-"}, STA: ${station.ip || "-"}`;
    } else if (mode === "station" && station.connected) {
      displayMode = "Station";
      displaySSID = station.ssid || "-";
      displayIP = station.ip || "-";
    } else if (mode === "ap" && ap.active) {
      displayMode = "Access Point";
      displaySSID = ap.ssid || "-";
      displayIP = ap.ip || "-";
    } else {
      displayMode = "Disconnected";
      displaySSID = "-";
      displayIP = "-";
    }

    document.getElementById("current-wifi-mode").textContent = displayMode;
    document.getElementById("current-ssid").textContent = displaySSID;
    document.getElementById("current-ip").textContent = displayIP;

    // Update badge colors based on mode
    const modeBadge = document.getElementById("current-wifi-mode");
    modeBadge.className = "badge badge-sm";

    if (mode === "dual") {
      modeBadge.classList.add("badge-info");
    } else if (mode === "station" && station.connected) {
      modeBadge.classList.add("badge-success");
    } else if (mode === "ap" && ap.active) {
      modeBadge.classList.add("badge-secondary");
    } else {
      modeBadge.classList.add("badge-warning");
    }
  }

  updateStatusDisplayBasic(status) {
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
    // Check if station mode is allowed
    if (!this.canConnectToStation()) {
      this.showToast(
        "WiFi connection is only available in Station or Dual mode. Please change network mode first.",
        "error"
      );
      return;
    }

    const ssid = document.getElementById("station-ssid").value.trim();
    const password = document.getElementById("station-password").value;

    if (!ssid) {
      this.showToast("Please enter a WiFi network name", "error");
      return;
    }

    if (!password) {
      this.showToast("Please enter the WiFi password", "error");
      return;
    }

    this.showToast("Connecting to WiFi network...", "info");

    // Determine which endpoint to use based on current network mode setting
    const networkModeSelect = document.getElementById("network-mode-select");
    const selectedMode = networkModeSelect
      ? networkModeSelect.value
      : "station";

    // Use dual mode endpoint if dual mode is selected and AP is currently active
    const isDualMode = selectedMode === "dual";
    const endpoint = isDualMode
      ? "/wifi/connect-station-dual"
      : "/wifi/connect-station";

    try {
      const response = await fetch(endpoint, {
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
          this.showToast(
            "Configuration saved! Device restart required.",
            "warning"
          );

          // Show restart button
          document
            .getElementById("restart-device-btn")
            .classList.remove("hidden");

          // Show restart instruction
          setTimeout(() => {
            this.showToast(
              "Please restart the device to connect to the WiFi network.",
              "info"
            );
          }, 3000);

          // Clear password field for security
          document.getElementById("station-password").value = "";
        } else {
          this.showToast(
            `Connected successfully! IP: ${result.ip}${
              isDualMode ? " (Dual Mode)" : ""
            }`,
            "success"
          );
          this.loadCurrentStatus();

          // Clear password field for security
          document.getElementById("station-password").value = "";

          // Note: Page might reload due to network change
          setTimeout(() => {
            if (result.ip && result.ip !== window.location.hostname) {
              this.showToast("Network changed. Redirecting...", "info");
              setTimeout(() => {
                window.location.hostname = result.ip;
              }, 2000);
            }
          }, 3000);
        }
      } else {
        this.showToast(result.message || "Connection failed", "error");
      }
    } catch (error) {
      console.error("Station connection error:", error);
      this.showToast(
        "Failed to connect. Please check your credentials.",
        "error"
      );
    }
  }

  async startAccessPoint() {
    // Check if AP mode is allowed
    if (!this.canStartAccessPoint()) {
      this.showToast(
        "Access Point is only available in AP or Dual mode. Please change network mode first.",
        "error"
      );
      return;
    }

    const ssid =
      document.getElementById("ap-ssid").value.trim() || "PicoW-Audio";
    const password = document.getElementById("ap-password").value;

    if (password && password.length < 8) {
      this.showToast("Password must be at least 8 characters long", "error");
      return;
    }

    this.showToast("Starting Access Point...", "info");

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
        this.showToast(
          `Access Point started! Connect to "${result.ssid}"`,
          "success"
        );
        this.loadCurrentStatus();

        // Clear password field
        document.getElementById("ap-password").value = "";

        // Show connection info
        setTimeout(() => {
          this.showToast(
            `AP IP: ${result.ip} | Password: ${result.password}`,
            "info"
          );
        }, 2000);
      } else {
        this.showToast(
          result.message || "Failed to start Access Point",
          "error"
        );
      }
    } catch (error) {
      console.error("AP start error:", error);
      this.showToast("Failed to start Access Point", "error");
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
          <div class="flex items-center gap-2">
            <div class="flex items-center gap-1">
              ${signalStrength}
              <span class="text-xs text-base-content/60">${network.rssi}dBm</span>
            </div>
          </div>
        </div>
      `;
      })
      .join("");

    networkList.innerHTML = networkItems;
  }

  getSignalStrengthIcon(rssi) {
    if (rssi >= -50) {
      // Excellent signal (4 bars)
      return `<svg
        xmlns="http://www.w3.org/2000/svg"
        class="w-5 h-5 text-success"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
      </svg>`;
    }
    if (rssi >= -60) {
      // Good signal (3 bars)
      return `<svg
        xmlns="http://www.w3.org/2000/svg"
        class="w-5 h-5 text-success"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
      </svg>`;
    }
    if (rssi >= -70) {
      // Fair signal (2 bars)
      return `<svg
        xmlns="http://www.w3.org/2000/svg"
        class="w-5 h-5 text-warning"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
      </svg>`;
    }
    // Poor signal (1 bar)
    return `<svg
      xmlns="http://www.w3.org/2000/svg"
      class="w-5 h-5 text-error"
      fill="none"
      viewBox="0 0 24 24"
      stroke-width="1.5"
      stroke="currentColor"
    >
      <path stroke-linecap="round" stroke-linejoin="round" d="M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
    </svg>`;
  }

  showToast(message, type = "info") {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById("toast-container");
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.id = "toast-container";
      toastContainer.className = "toast toast-top toast-center z-50";
      document.body.appendChild(toastContainer);
    }

    // Create toast alert using DaisyUI classes
    const toast = document.createElement("div");
    const alertClass =
      type === "error"
        ? "alert-error"
        : type === "success"
        ? "alert-success"
        : type === "warning"
        ? "alert-warning"
        : "alert-info";

    toast.className = `alert ${alertClass}`;

    // DaisyUI toast icon based on type
    const icons = {
      success: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m9 12 2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>`,
      error: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>`,
      warning: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5Z" />
                </svg>`,
      info: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
             </svg>`,
    };

    toast.innerHTML = `
      ${icons[type] || icons.info}
      <span>${message}</span>
    `;

    // Add toast to container
    toastContainer.appendChild(toast);

    // Auto-remove after 4 seconds with fade animation
    setTimeout(() => {
      if (toast.parentNode) {
        toast.style.transition = "all 0.3s ease-out";
        toast.style.transform = "translateY(-20px)";
        toast.style.opacity = "0";
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }
    }, 4000);
  }

  // Legacy method for backward compatibility - redirects to toast
  showStatus(message, type = "info") {
    this.showToast(message, type);
  }

  getCurrentNetworkMode() {
    const networkModeSelect = document.getElementById("network-mode-select");
    return networkModeSelect ? networkModeSelect.value : "ap";
  }

  canConnectToStation() {
    const mode = this.getCurrentNetworkMode();
    return mode === "station" || mode === "dual";
  }

  canStartAccessPoint() {
    const mode = this.getCurrentNetworkMode();
    return mode === "ap" || mode === "dual";
  }

  async restartDevice() {
    if (!confirm("Are you sure you want to restart the device?")) {
      return;
    }

    this.showToast("Restarting device...", "info");

    try {
      const response = await fetch("/wifi/restart", {
        method: "POST",
      });

      if (response.ok) {
        this.showToast("Device is restarting. Please wait...", "info");

        // Hide the restart button
        document.getElementById("restart-device-btn").classList.add("hidden");

        // Try to reconnect after restart
        setTimeout(() => {
          this.showToast("Attempting to reconnect...", "info");
          setTimeout(() => {
            window.location.reload();
          }, 5000);
        }, 10000);
      } else {
        this.showToast("Failed to restart device", "error");
      }
    } catch (error) {
      console.error("Restart error:", error);
      this.showToast("Failed to restart device", "error");
    }
  }

  async loadConfigForAutofill() {
    try {
      const response = await fetch("/wifi/config");

      if (!response.ok) {
        console.warn("Could not fetch config for autofill");
        return;
      }

      const result = await response.json();

      if (result.success && result.config) {
        const config = result.config;

        // Autofill station mode fields
        if (config.station && config.station.ssid) {
          const stationSSID = document.getElementById("station-ssid");
          const stationPassword = document.getElementById("station-password");

          if (stationSSID) {
            stationSSID.value = config.station.ssid;
            stationSSID.placeholder = `Saved: ${config.station.ssid}`;
          }
          if (stationPassword && config.station.password) {
            stationPassword.value = config.station.password;
            stationPassword.placeholder = "Saved password";
          }
        }

        // Autofill AP mode fields
        if (config.ap) {
          const apSSID = document.getElementById("ap-ssid");
          const apPassword = document.getElementById("ap-password");

          if (apSSID && config.ap.ssid) {
            apSSID.value = config.ap.ssid;
            apSSID.placeholder = `Default: ${config.ap.ssid}`;
          }
          if (apPassword && config.ap.password) {
            apPassword.value = config.ap.password;
            apPassword.placeholder = "Default password";
          }
        }

        // Set current network mode in selector
        const networkModeSelect = document.getElementById(
          "network-mode-select"
        );
        if (networkModeSelect && config.mode) {
          networkModeSelect.value = config.mode;
          // Update UI based on loaded mode
          this.updateConnectButtonText();
        }
      }
    } catch (error) {
      console.warn("Failed to load config for autofill:", error);
      // Don't show error to user - this is a nice-to-have feature
    }
  }
}

export default WiFiConfigManager;
