export default class EQChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.options = this.mergeOptions(options);
    this.chart = null;

    this.init();
  }

  mergeOptions(userOptions) {
    const defaultOptions = {
      type: "line",
      data: {
        labels: ["Low", "Mid", "High"],
        datasets: [
          {
            label: "EQ dB",
            data: [0, 0, 0],
            borderColor: "#04aa6d",
            backgroundColor: "#04aa6d44",
            fill: true,
            tension: 0.3,
            pointBackgroundColor: "#fff",
            pointRadius: 6,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        animation: { animation: false },
        scales: {
          y: {
            min: -12,
            max: 12,
            ticks: { stepSize: 6 },
          },
        },
        interaction: {
          mode: "nearest",
          intersect: true,
        },
        plugins: {
          legend: { display: false },
          title: { display: false },
          tooltip: { enabled: false },
        },
      },
    };

    return this.deepMerge(defaultOptions, userOptions);
  }

  deepMerge(target, source) {
    for (const key in source) {
      if (
        source[key] &&
        typeof source[key] === "object" &&
        !Array.isArray(source[key])
      ) {
        target[key] = target[key] || {};
        this.deepMerge(target[key], source[key]);
      } else {
        target[key] = source[key];
      }
    }
    return target;
  }

  init() {
    this.options.options.onClick = (e) => this.handleChartClick(e);
    this.chart = new Chart(this.ctx, this.options);
  }

  handleChartClick(event) {
    const points = this.chart.getElementsAtEventForMode(
      event,
      "nearest",
      { intersect: true },
      false
    );

    if (points.length > 0) {
      const index = points[0].index;
      const band = ["low", "mid", "high"][index];
      const current = this.chart.data.datasets[0].data[index];

      this.promptForValue(band, current, index);
    }
  }

  promptForValue(band, currentValue, index) {
    const input = prompt(`Set ${band.toUpperCase()} value (dB):`, currentValue);
    const newValue = parseFloat(input);

    if (!isNaN(newValue) && newValue >= -12 && newValue <= 12) {
      this.updateBand(index, newValue);
      this.syncWithSlider(band, newValue);
    } else {
      alert("Please enter a number between -12 and 12.");
    }
  }

  updateBand(index, value) {
    this.chart.data.datasets[0].data[index] = value;
    this.chart.update();
  }

  updateValues(values) {
    this.chart.data.datasets[0].data = values;
    this.chart.update("none");
  }

  syncWithSlider(band, value) {
    const slider = document.getElementById(`${band}Slider`);
    const valueLabel = document.getElementById(`${band}Value`);

    if (slider) slider.value = value;
    if (valueLabel) valueLabel.textContent = `${value}dB`;
  }

  getValue(band) {
    const index = { low: 0, mid: 1, high: 2 }[band];
    return this.chart.data.datasets[0].data[index];
  }
}
