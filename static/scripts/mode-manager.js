export default class ModeManager {
  constructor(wsManager) {
    this.wsManager = wsManager;
    this.currentMode = "off";
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Handle mode updates from WebSocket
    this.wsManager.callbacks.mode = (message) => {
      this.updateMode(message.mode);
    };
  }

  updateMode(mode) {
    this.currentMode = mode;
    const display = document.getElementById("currentMode");
    if (display) {
      display.textContent = `Current Mode: ${mode}`;
    }

    this.onModeChange?.(mode);
  }

  toggleMode() {
    this.wsManager.send({
      action: "toggle_voice_mode",
    });
  }

  onModeChange(callback) {
    this.onModeChange = callback;
  }
}
