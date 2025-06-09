const ctx = document.getElementById("eqChart").getContext("2d");

const eqChart = new Chart(ctx, {
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
    animation: {
      animation: false,
    },
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
    onClick: (e) => {
      const points = eqChart.getElementsAtEventForMode(
        e,
        "nearest",
        { intersect: true },
        false
      );

      if (points.length > 0) {
        const index = points[0].index;
        const band = ["low", "mid", "high"][index];
        const current = eqChart.data.datasets[0].data[index];

        const input = prompt(`Set ${band.toUpperCase()} value (dB):`, current);
        const newValue = parseFloat(input);

        if (!isNaN(newValue) && newValue >= -12 && newValue <= 12) {
          eqChart.data.datasets[0].data[index] = newValue;
          eqChart.update();

          // Update corresponding slider and label
          document.getElementById(`${band}Slider`).value = newValue;
          document.getElementById(`${band}Value`).textContent = `${newValue}dB`;
        } else {
          alert("Please enter a number between -12 and 12.");
        }
      }
    },
  },
});

// Sync chart when slider changes
function updateEQFromSlider(band, value) {
  const index = { low: 0, mid: 1, high: 2 }[band];
  const val = parseFloat(value);
  eqChart.data.datasets[0].data[index] = val;
  eqChart.update();

  document.getElementById(`${band}Value`).textContent = `${val}dB`;
}
