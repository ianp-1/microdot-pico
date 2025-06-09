import AudioDashboardApp from "./audio-dashboard.js";

console.log("Script.js loading...");

document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing app...");

  try {
    const app = new AudioDashboardApp();

    // Store app instance globally for debugging
    window.audioApp = app;

    console.log("App initialized successfully");

    // Cleanup on page unload
    window.addEventListener("beforeunload", () => {
      console.log("Page unloading, destroying app...");
      app.destroy();
    });
  } catch (error) {
    console.error("Failed to initialize app:", error);
  }
});
