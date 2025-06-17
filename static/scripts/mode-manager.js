export default class ModeManager {
  constructor(wsManager) {
    this.wsManager = wsManager;
    this.currentMode = "off"; // This will be updated by initial state
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Note: callbacks are set up in audio-dashboard.js during wsManager initialization
    // This method is kept for potential future direct event handling
  }

  updateMode(mode) {
    // console.log(`Updating mode from "${this.currentMode}" to "${mode}"`);
    this.currentMode = mode;
    const display = document.getElementById("currentMode");
    if (display) {
      display.textContent = `Current Mode: ${mode}`;
      // console.log(`Updated display to: Current Mode: ${mode}`);
    } else {
      console.error("currentMode element not found!");
    }

    this.onModeChangeCallback?.(mode);
  }

  toggleMode() {
    this.wsManager.send({
      action: "toggle_voice_mode",
    });
  }

  toggleDucking() {
    this.wsManager.send({
      action: "toggle_ducking",
    });
  }

  toggleFeedback() {
    this.wsManager.send({
      action: "toggle_feedback",
    });
  }

  setOnModeChangeCallback(callback) {
    this.onModeChangeCallback = callback;
  }
}
