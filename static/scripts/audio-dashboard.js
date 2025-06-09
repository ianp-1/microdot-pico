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
    console.log("Initializing Audio Dashboard...");

    // Initialize WebSocket with callbacks
    this.wsManager = new WebSocketManager(`ws://${location.host}/ws`, {
      dial: (message) => this.handleDialUpdate(message),
      mode: (message) => this.handleModeUpdate(message),
      onOpen: () => {
        console.log("Dashboard WebSocket connected");
        // Request initial EQ values when connected
        this.requestInitialData();
      },
      onClose: () => console.log("Dashboard WebSocket disconnected"),
      onError: (error) => console.error("Dashboard WebSocket error:", error),
    });

    // Initialize EQ Chart
    this.eqChart = new EQChart("eqChart");

    // Initialize EQ Controller
    this.eqController = new EQController(this.eqChart, this.wsManager);

    // Initialize Mode Manager
    this.modeManager = new ModeManager(this.wsManager);

    // Make global functions available for HTML onclick handlers
    this.exposeGlobalFunctions();

    console.log("Audio Dashboard initialized");
  }

  requestInitialData() {
    // Request current EQ and mode values
    this.wsManager.send({ action: "get_current_eq" });
  }

  handleDialUpdate(message) {
    console.log("Handling dial update:", message);
    if (this.eqController) {
      this.eqController.updateFromServer({
        low: message.low,
        mid: message.mid,
        high: message.high,
      });
    }
  }

  handleModeUpdate(message) {
    console.log("Handling mode update:", message);
    if (this.modeManager) {
      this.modeManager.updateMode(message.mode);
    }
  }

  exposeGlobalFunctions() {
    // For backward compatibility with HTML onclick handlers
    window.updateEQFromSlider = (band, value) => {
      if (this.eqController) {
        this.eqController.handleSliderChange(band, parseFloat(value));
      }
    };

    window.updateEQChart = (values) => {
      if (this.eqChart) {
        this.eqChart.updateValues(values);
      }
    };
  }

  destroy() {
    console.log("Destroying Audio Dashboard...");
    this.wsManager?.socket?.close();
  }
}
