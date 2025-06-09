export default class ModeManager {
  constructor(wsManager) {
    this.wsManager = wsManager;
    this.currentMode = "off"; // This will be updated by initial state
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Handle mode updates from WebSocket
    this.wsManager.callbacks.mode = (message) => {
      this.updateMode(message.mode);
    };

    // Handle initial state updates
    this.wsManager.callbacks.initial_state = (message) => {
      if (message.mode) {
        this.updateMode(message.mode);
      }
    };
  }

  updateMode(mode) {
    console.log(`Updating mode from "${this.currentMode}" to "${mode}"`);
    this.currentMode = mode;
    const display = document.getElementById("currentMode");
    if (display) {
      display.textContent = `Current Mode: ${mode}`;
      console.log(`Updated display to: Current Mode: ${mode}`);
    } else {
      console.error("currentMode element not found!");
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
