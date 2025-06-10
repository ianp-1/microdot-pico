export default class EQController {
  constructor(chart, wsManager) {
    this.chart = chart;
    this.wsManager = wsManager;
    this.bands = ["low", "mid", "high"];
    this.controlStatus = { low: "physical", mid: "physical", high: "physical" };

    this.setupSliders();
    this.setupControlStatusDisplay();
  }

  setupSliders() {
    this.bands.forEach((band) => {
      const slider = document.getElementById(`${band}Slider`);
      if (slider) {
        // Handle real-time visual updates while dragging
        slider.addEventListener("input", (e) => {
          this.handleSliderInput(band, parseFloat(e.target.value));
        });

        // Handle final value submission when user releases slider
        slider.addEventListener("change", (e) => {
          this.handleSliderChange(band, parseFloat(e.target.value));
        });

        // Add visual feedback for drag start/end
        slider.addEventListener("mousedown", () => {
          this.setSliderDragging(band, true);
        });

        slider.addEventListener("mouseup", () => {
          this.setSliderDragging(band, false);
        });

        console.log(`${band} slider connected`);
      } else {
        console.warn(`${band} slider not found`);
      }
    });
  }

  setupControlStatusDisplay() {
    // Control status elements are now pre-existing in the HTML template
    // Just initialize the status for each band
    this.bands.forEach((band) => {
      this.updateControlStatus(band, "physical");
    });
  }

  handleSliderInput(band, value) {
    // Real-time visual updates while dragging (no server communication)
    console.log(`EQ ${band} preview: ${value}dB`);

    // Update chart immediately for visual feedback
    const index = this.bands.indexOf(band);
    this.chart.updateBand(index, value);

    // Update display immediately
    this.updateValueDisplay(band, value);
  }

  handleSliderChange(band, value) {
    // Final value submission when user releases slider
    console.log(
      `EQ ${band} changed to ${value}dB (digital control - persists until physical movement)`
    );

    // Update control status
    this.updateControlStatus(band, "digital");

    // Send to server via WebSocket (only when slider is released)
    this.wsManager.send({
      action: "eq_update",
      band: band,
      value: value,
    });

    // Brief visual confirmation that value was sent
    this.showValueSentConfirmation(band);
  }

  showValueSentConfirmation(band) {
    const valueLabel = document.getElementById(`${band}Value`);
    if (valueLabel) {
      // Flash green to indicate value was sent
      valueLabel.style.color = "#22c55e"; // green-500
      valueLabel.style.fontWeight = "bold";

      setTimeout(() => {
        valueLabel.style.color = "";
        valueLabel.style.fontWeight = "";
      }, 200);
    }
  }

  setSliderDragging(band, isDragging) {
    const valueLabel = document.getElementById(`${band}Value`);
    if (valueLabel) {
      if (isDragging) {
        valueLabel.style.color = "#10b981"; // emerald-500 for dragging
        valueLabel.style.fontWeight = "bold";
      } else {
        valueLabel.style.color = ""; // reset to default
        valueLabel.style.fontWeight = "";
      }
    }
  }

  updateControlStatus(band, source) {
    console.log(
      `[EQ Controller] Updating ${band} control status to: ${source}`
    );
    this.controlStatus[band] = source;
    const statusElement = document.getElementById(`${band}ControlStatus`);
    if (statusElement) {
      statusElement.textContent = source === "digital" ? "Digital" : "Physical";
      // Use Tailwind classes for styling
      statusElement.className =
        source === "digital"
          ? "text-xs text-emerald-400 font-semibold"
          : "text-xs text-gray-400";
      console.log(
        `[EQ Controller] Updated ${band} status element text to: ${statusElement.textContent}`
      );
    } else {
      console.warn(
        `[EQ Controller] Status element not found for band: ${band}`
      );
    }
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
    this.wsManager.send({
      action: "get_current_eq",
    });
  }
}
