import AudioDashboardApp from "./audio-dashboard.js";
import WiFiConfigManager from "./wifi-config.js";
import UARTController from "./uart-controller.js";

document.addEventListener("DOMContentLoaded", () => {
  try {
    const app = new AudioDashboardApp();
    const wifiConfig = new WiFiConfigManager();
    const uartController = new UARTController(app.wsManager);

    // Store app instances globally for debugging
    window.audioApp = app;
    window.wifiConfig = wifiConfig;
    window.uartController = uartController;

    // Cleanup on page unload
    window.addEventListener("beforeunload", () => {
      app.destroy();
    });
  } catch (error) {
    console.error("Failed to initialize app:", error);
  }
});
