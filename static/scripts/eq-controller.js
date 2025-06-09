export default class EQController {
  constructor(chart, wsManager) {
    this.chart = chart;
    this.wsManager = wsManager;
    this.bands = ["low", "mid", "high"];

    this.setupSliders();
    // Remove the broken fetchCurrentEQ call
    this.requestInitialValues();
  }

  setupSliders() {
    this.bands.forEach((band) => {
      const slider = document.getElementById(`${band}Slider`);
      if (slider) {
        slider.addEventListener("input", (e) => {
          this.handleSliderChange(band, parseFloat(e.target.value));
        });
        console.log(`${band} slider connected`);
      } else {
        console.warn(`${band} slider not found`);
      }
    });
  }

  handleSliderChange(band, value) {
    console.log(`EQ ${band} changed to ${value}dB`);

    // Update chart - use the correct method name
    const index = this.bands.indexOf(band);
    this.chart.updateBand(index, value);

    // Update display
    this.updateValueDisplay(band, value);

    // Send to server via WebSocket with correct format
    this.wsManager.send({
      action: "eq_update",
      band: band,
      value: value,
    });
  }

  updateValueDisplay(band, value) {
    const valueLabel = document.getElementById(`${band}Value`);
    if (valueLabel) {
      valueLabel.textContent = `${value.toFixed(1)}dB`;
    }
  }

  updateFromServer(eqData) {
    console.log("Updating from server:", eqData);

    this.bands.forEach((band) => {
      if (eqData[band] !== undefined) {
        const value = parseFloat(eqData[band]);
        const slider = document.getElementById(`${band}Slider`);

        if (slider) {
          slider.value = value;
        }

        this.updateValueDisplay(band, value);

        // Update chart
        const index = this.bands.indexOf(band);
        this.chart.updateBand(index, value);
      }
    });
  }

  requestInitialValues() {
    // Request initial EQ values
    this.wsManager.send({
      action: "get_current_eq",
    });
  }

  // Remove the broken HTTP fetch methods
  startSync() {
    // No longer needed - using WebSocket
  }

  stopSync() {
    // No longer needed
  }
}
