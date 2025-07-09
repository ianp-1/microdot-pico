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
    this.currentMode = mode;
    const modeDisplay = document.getElementById("currentMode");
    if (modeDisplay) {
      modeDisplay.textContent = `Current Mode: ${mode}`;
    }
  }

  toggleMode() {
    this.wsManager.send({ action: "toggle_voice_mode" });
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

  toggleMute() {
    this.wsManager.send({
      action: "toggle_mute",
    });
  }

  setOnModeChangeCallback(callback) {
    this.onModeChangeCallback = callback;
  }
}
