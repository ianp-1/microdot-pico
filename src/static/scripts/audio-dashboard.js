import WebSocketManager from "./web-socket-manager.js";
import EQChart from "./eq-chart.js";
import EQController from "./eq-controller.js";
import ModeManager from "./mode-manager.js";
import DSPMixerController from "./dsp-mixer-controller.js";

export default class AudioDashboardApp {
  constructor() {
    this.wsManager = null;
    this.eqChart = null;
    this.eqController = null;
    this.modeManager = null;
    this.dspMixerController = null;

    this.init();
  }

  init() {
    // Initialize WebSocket with callbacks
    this.wsManager = new WebSocketManager(`ws://${location.host}/ws`, {
      dial: (message) => this.handleDialUpdate(message),
      mode: (message) => this.handleModeUpdate(message),
      ducking: (message) => this.handleDuckingUpdate(message),
      feedback: (message) => this.handleFeedbackUpdate(message),
      mute: (message) => this.handleMuteUpdate(message),
      dsp_mixer: (message) => this.handleDSPMixerUpdate(message),
      initial_state: (message) => this.handleInitialState(message),
      onOpen: () => {
        // Don't request initial data - server sends it automatically
      },
      onClose: () => {},
      onError: (error) => console.error("Dashboard WebSocket error:", error),
    });

    // Initialize EQ Chart
    this.eqChart = new EQChart("eqChart");

    // Initialize EQ Controller
    this.eqController = new EQController(this.eqChart, this.wsManager);

    // Initialize Mode Manager
    this.modeManager = new ModeManager(this.wsManager);

    // Initialize DSP Mixer Controller
    this.dspMixerController = new DSPMixerController(this.wsManager);

    // Connect toggle button to mode manager
    this.setupModeToggleButton();
    this.setupDuckingFeedbackButtons();
    this.setupMuteButton();
  }

  // Add this new method to handle initial state
  handleInitialState(message) {
    // Update mode first
    if (this.modeManager && message.mode) {
      this.modeManager.updateMode(message.mode);
    }

    // Update EQ values
    if (this.eqController && message.eq) {
      this.eqController.updateFromServer(message.eq);
    }

    // Update ducking state
    if (message.ducking !== undefined) {
      this.updateDuckingDisplay(message.ducking);
    }

    // Update feedback state
    if (message.feedback !== undefined) {
      this.updateFeedbackDisplay(message.feedback);
    }

    // Update mute state
    if (message.mute !== undefined) {
      this.updateMuteDisplay(message.mute);
    }

    // Update DSP mixer state
    if (this.dspMixerController && message.dsp_mixer) {
      this.dspMixerController.updateFromServer(message.dsp_mixer);
    }
  }

  handleDialUpdate(message) {
    if (this.eqController) {
      this.eqController.updateFromServer({
        low: message.low,
        mid: message.mid,
        high: message.high,
      });

      // Update control sources if provided
      if (message.control_sources) {
        Object.keys(message.control_sources).forEach((band) => {
          const source = message.control_sources[band];
          this.eqController.updateControlStatus(band, source);
        });
      }
    }
  }

  handleModeUpdate(message) {
    if (this.modeManager) {
      this.modeManager.updateMode(message.mode);
    }
  }

  handleDuckingUpdate(message) {
    this.updateDuckingDisplay(message.enabled);
  }

  handleFeedbackUpdate(message) {
    this.updateFeedbackDisplay(message.enabled);
  }

  handleMuteUpdate(message) {
    this.updateMuteDisplay(message.enabled);
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

  updateMuteDisplay(enabled) {
    const muteButton = document.getElementById("muteButton");
    const muteStatus = document.getElementById("muteStatus");
    const muteAlert = document.getElementById("muteAlert");

    if (muteStatus) {
      muteStatus.textContent = enabled ? "on" : "off";
    }

    if (muteAlert) {
      if (enabled) {
        muteAlert.classList.remove("hidden");
      } else {
        muteAlert.classList.add("hidden");
      }
    }
  }

  setupModeToggleButton() {
    const toggleButton = document.getElementById("toggleVoiceModeBtn");
    if (toggleButton) {
      toggleButton.addEventListener("click", () => {
        this.modeManager.toggleMode();
      });
    } else {
      console.error("Toggle voice mode button not found!");
    }
  }

  setupDuckingFeedbackButtons() {
    const duckingButton = document.getElementById("toggleDuckingBtn");
    if (duckingButton) {
      duckingButton.addEventListener("click", () => {
        this.modeManager.toggleDucking();
      });
    } else {
      console.error("Ducking button not found!");
    }

    const feedbackButton = document.getElementById("toggleFeedbackBtn");
    if (feedbackButton) {
      feedbackButton.addEventListener("click", () => {
        this.modeManager.toggleFeedback();
      });
    } else {
      console.error("Feedback button not found!");
    }
  }

  setupMuteButton() {
    const muteButton = document.getElementById("muteButton");
    if (muteButton) {
      muteButton.addEventListener("click", () => {
        this.modeManager.toggleMute();
      });
    } else {
      console.error("Mute button not found!");
    }
  }

  handleDSPMixerUpdate(message) {
    if (this.dspMixerController) {
      this.dspMixerController.updateFromServer(message);
    }
  }

  destroy() {
    // Destroy EQ Chart to clean up resize observers
    if (this.eqChart) {
      this.eqChart.destroy();
      this.eqChart = null;
    }

    // Close WebSocket connection
    this.wsManager?.socket?.close();
  }
}
