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

    // Send regular EQ update to server via WebSocket
    this.wsManager.send({
      action: "eq_update",
      band: band,
      value: value,
    });

    // Send UART command for gain control (only for low and high bands)
    if (band === "low" || band === "high") {
      // Map EQ band to UART gain parameter
      let uartParam = band === "low" ? "g1" : "g2";

      // Convert EQ dB value (-12 to +12) to gain value (0.0 to 2.0)
      // -12dB = 0.0, 0dB = 1.0, +12dB = 2.0
      let gainValue = Math.max(0.0, Math.min(2.0, 1.0 + value / 12.0));

      this.wsManager.send({
        action: "uart_command",
        param: uartParam,
        value: gainValue,
      });
      console.log(
        `EQ->UART: ${band} = ${value}dB -> ${uartParam} = ${gainValue.toFixed(
          2
        )}`
      );
    }

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
    this.controlStatus[band] = source;
    const statusElement = document.getElementById(`${band}ControlStatus`);
    if (statusElement) {
      statusElement.textContent = source === "digital" ? "Digital" : "Physical";
      // Use Tailwind classes for styling
      statusElement.className =
        source === "digital"
          ? "text-xs text-emerald-400 font-semibold"
          : "text-xs text-gray-400";
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
