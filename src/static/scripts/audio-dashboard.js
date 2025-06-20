import WebSocketManager from "./web-socket-manager.js";
import EQChart from "./eq-chart.js";
import EQController from "./eq-controller.js";
import ModeManager from "./mode-manager.js";

export default class AudioDashboardApp {
  constructor() {
    this.wsManager = null;
    this.eqChart = null;
    this.eqController = null;
    this.modeManager = null;

    this.init();
  }

  init() {
    // console.log("Initializing Audio Dashboard...");

    // Initialize WebSocket with callbacks
    this.wsManager = new WebSocketManager(`ws://${location.host}/ws`, {
      dial: (message) => this.handleDialUpdate(message),
      mode: (message) => this.handleModeUpdate(message),
      ducking: (message) => this.handleDuckingUpdate(message),
      feedback: (message) => this.handleFeedbackUpdate(message),
      initial_state: (message) => this.handleInitialState(message),
      onOpen: () => {
        // console.log("Dashboard WebSocket connected");
        // Don't request initial data - server sends it automatically
      },
      onClose: () => {}, // console.log("Dashboard WebSocket disconnected"),
      onError: (error) => console.error("Dashboard WebSocket error:", error),
    });

    // Initialize EQ Chart
    this.eqChart = new EQChart("eqChart");

    // Initialize EQ Controller
    this.eqController = new EQController(this.eqChart, this.wsManager);

    // Initialize Mode Manager
    this.modeManager = new ModeManager(this.wsManager);

    // Connect toggle button to mode manager
    this.setupModeToggleButton();
    this.setupDuckingFeedbackButtons();

    // console.log("Audio Dashboard initialized");
  }

  // Add this new method to handle initial state
  handleInitialState(message) {
    // console.log("Handling initial state:", message);

    // Update mode first
    if (this.modeManager && message.mode) {
      // console.log("Setting mode to:", message.mode);
      this.modeManager.updateMode(message.mode);
    }

    // Update EQ values
    if (this.eqController && message.eq) {
      // console.log("Setting EQ to:", message.eq);
      this.eqController.updateFromServer(message.eq);
    }

    // Update ducking state
    if (message.ducking !== undefined) {
      // console.log("Setting ducking to:", message.ducking);
      this.updateDuckingDisplay(message.ducking);
    }

    // Update feedback state
    if (message.feedback !== undefined) {
      // console.log("Setting feedback to:", message.feedback);
      this.updateFeedbackDisplay(message.feedback);
    }
  }

  handleDialUpdate(message) {
    // console.log("Handling dial update:", message);
    if (this.eqController) {
      this.eqController.updateFromServer({
        low: message.low,
        mid: message.mid,
        high: message.high,
      });

      // Update control sources if provided
      if (message.control_sources) {
        // console.log("Updating control sources:", message.control_sources);
        Object.keys(message.control_sources).forEach((band) => {
          const source = message.control_sources[band];
          // console.log(`Setting ${band} control to: ${source}`);
          this.eqController.updateControlStatus(band, source);
        });
      }
    }
  }

  handleModeUpdate(message) {
    // console.log("Handling mode update:", message);
    if (this.modeManager) {
      this.modeManager.updateMode(message.mode);
    }
  }

  handleDuckingUpdate(message) {
    // console.log("Handling ducking update:", message);
    this.updateDuckingDisplay(message.enabled);
  }

  handleFeedbackUpdate(message) {
    // console.log("Handling feedback update:", message);
    this.updateFeedbackDisplay(message.enabled);
  }

  updateDuckingDisplay(enabled) {
    const duckingDisplay = document.getElementById("musicDucking");
    if (duckingDisplay) {
      duckingDisplay.textContent = `Ducking: ${enabled ? "on" : "off"}`;
      duckingDisplay.className = `mt-2 capitalize ${
        enabled ? "text-emerald-400" : "text-gray-400"
      }`;
    }
  }

  updateFeedbackDisplay(enabled) {
    const feedbackDisplay = document.getElementById("feedback");
    if (feedbackDisplay) {
      feedbackDisplay.textContent = `Feedback: ${enabled ? "on" : "off"}`;
      feedbackDisplay.className = `mt-2 capitalize ${
        enabled ? "text-emerald-400" : "text-gray-400"
      }`;
    }
  }

  setupModeToggleButton() {
    const toggleButton = document.getElementById("toggleVoiceModeBtn");
    if (toggleButton) {
      toggleButton.addEventListener("click", () => {
        // console.log("Toggle voice mode button clicked");
        this.modeManager.toggleMode();
      });
    } else {
      console.error("Toggle voice mode button not found!");
    }
  }

  setupDuckingFeedbackButtons() {
    // Setup ducking button
    const duckingButtons = document.querySelectorAll(
      'button[hx-post="/trigger-ducking"]'
    );
    duckingButtons.forEach((button) => {
      // Remove HTMX attributes and add WebSocket click handler
      button.removeAttribute("hx-post");
      button.removeAttribute("hx-target");
      button.removeAttribute("hx-swap");

      button.addEventListener("click", () => {
        // console.log("Toggle ducking button clicked");
        this.modeManager.toggleDucking();
      });
    });

    // Setup feedback button
    const feedbackButtons = document.querySelectorAll(
      'button[hx-post="/trigger-feedback"]'
    );
    feedbackButtons.forEach((button) => {
      // Remove HTMX attributes and add WebSocket click handler
      button.removeAttribute("hx-post");
      button.removeAttribute("hx-target");
      button.removeAttribute("hx-swap");

      button.addEventListener("click", () => {
        // console.log("Toggle feedback button clicked");
        this.modeManager.toggleFeedback();
      });
    });
  }

  destroy() {
    // console.log("Destroying Audio Dashboard...");

    // Destroy EQ Chart to clean up resize observers
    if (this.eqChart) {
      this.eqChart.destroy();
      this.eqChart = null;
    }

    // Close WebSocket connection
    this.wsManager?.socket?.close();
  }
}
