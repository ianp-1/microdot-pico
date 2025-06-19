import AudioDashboardApp from "./audio-dashboard.js";
import WiFiConfigManager from "./wifi-config.js";

// console.log("Script.js loading...");

document.addEventListener("DOMContentLoaded", () => {
  // console.log("DOM loaded, initializing app...");

  try {
    const app = new AudioDashboardApp();
    const wifiConfig = new WiFiConfigManager();

    // Store app instances globally for debugging
    window.audioApp = app;
    window.wifiConfig = wifiConfig;

    // console.log("Apps initialized successfully");

    // Cleanup on page unload
    window.addEventListener("beforeunload", () => {
      // console.log("Page unloading, destroying app...");
      app.destroy();
    });
  } catch (error) {
    console.error("Failed to initialize app:", error);
  }
});
