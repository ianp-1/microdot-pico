import AudioDashboardApp from "./audio-dashboard.js";
import WiFiConfigManager from "./wifi-config.js";

document.addEventListener("DOMContentLoaded", () => {
  try {
    const app = new AudioDashboardApp();
    const wifiConfig = new WiFiConfigManager();

    // Store app instances globally for debugging
    window.audioApp = app;
    window.wifiConfig = wifiConfig;

    // Cleanup on page unload
    window.addEventListener("beforeunload", () => {
      app.destroy();
    });
  } catch (error) {
    console.error("Failed to initialize app:", error);
  }
});
