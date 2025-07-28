export default class UARTController {
  constructor(wsManager) {
    this.wsManager = wsManager;
    this.controls = [
      {
        id: "masterGainSlider",
        param: "master",
        labelId: "masterGainLabel",
        valueId: "masterGainValue",
      },
      {
        id: "gainCh1Slider",
        param: "g1",
        labelId: "gainCh1Label",
        valueId: "gainCh1Value",
      },
      {
        id: "gainCh2Slider",
        param: "g2",
        labelId: "gainCh2Label",
        valueId: "gainCh2Value",
      },
      {
        id: "panSlider",
        param: "pan",
        labelId: "panLabel",
        valueId: "panValue",
      },
    ];

    this.setupControls();
  }

  setupControls() {
    this.controls.forEach((control) => {
      const slider = document.getElementById(control.id);
      if (slider) {
        slider.addEventListener("input", (e) => {
          this.handleSliderInput(
            control.param,
            parseFloat(e.target.value),
            control.labelId,
            control.valueId
          );
        });

        slider.addEventListener("change", (e) => {
          this.handleSliderChange(control.param, parseFloat(e.target.value));
        });
      }
    });
  }

  handleSliderInput(param, value, labelId, valueId) {
    this.updateValueDisplay({ [param]: value });
  }

  handleSliderChange(param, value) {
    this.wsManager.send({
      action: "uart_command",
      param: param,
      value: value,
    });
  }

  updateValueDisplay(mixerData) {
    this.controls.forEach((control) => {
      if (mixerData[control.param] !== undefined) {
        const value = parseFloat(mixerData[control.param]);
        const slider = document.getElementById(control.id);
        const label = document.getElementById(control.labelId);
        const valueDisplay = document.getElementById(control.valueId);

        if (slider) slider.value = value;
        if (label) label.textContent = value.toFixed(2);
        if (valueDisplay) valueDisplay.textContent = value.toFixed(2);
      }
    });
  }

  updateFromServer(mixerData) {
    this.updateValueDisplay(mixerData);
  }

  handleStateUpdate(state) {
    this.updateValueDisplay(state);
  }
}
