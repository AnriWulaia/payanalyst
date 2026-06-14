let selectedFile = null;
let pdfBlob = null;
let charts = {};

const fileInput = document.getElementById("fileInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const statusEl = document.getElementById("status");
const chartsSection = document.getElementById("charts");
const downloadBtn = document.getElementById("downloadBtn");

fileInput.addEventListener("change", () => {
  selectedFile = fileInput.files[0];
  if (selectedFile) {
    analyzeBtn.disabled = false;
    statusEl.textContent = `Selected: ${selectedFile.name}`;
    statusEl.className = "status";
  }
});

const uploadBox = document.getElementById("uploadBox");
uploadBox.addEventListener("dragover", e => { e.preventDefault(); uploadBox.style.borderColor = "#4f6ef7"; });
uploadBox.addEventListener("dragleave", () => { uploadBox.style.borderColor = "#c0c8e0"; });
uploadBox.addEventListener("drop", e => {
  e.preventDefault();
  uploadBox.style.borderColor = "#c0c8e0";
  const file = e.dataTransfer.files[0];
  if (file && file.name.endsWith(".csv")) {
    selectedFile = file;
    analyzeBtn.disabled = false;
    statusEl.textContent = `Selected: ${file.name}`;
  }
});

analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span class="spinner"></span>Analyzing...';
  statusEl.textContent = "Running analysis and generating AI report...";
  statusEl.className = "status";
  chartsSection.style.display = "none";

  try {
    const [statsRes, pdfRes] = await Promise.all([
      fetchStats(),
      fetchPDF()
    ]);

    pdfBlob = pdfRes;
    renderMetrics(statsRes);
    renderCharts(statsRes);

    chartsSection.style.display = "block";
    statusEl.textContent = "Done!";
    analyzeBtn.innerHTML = "Generate Report";
    analyzeBtn.disabled = false;

  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = "status error";
    analyzeBtn.innerHTML = "Generate Report";
    analyzeBtn.disabled = false;
  }
});

async function fetchStats() {
  const formData = new FormData();
  formData.append("file", selectedFile);
  const res = await fetch("/stats", { method: "POST", body: formData });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
  return res.json();
}

async function fetchPDF() {
  const formData = new FormData();
  formData.append("file", selectedFile);
  const res = await fetch("/analyze", { method: "POST", body: formData });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
  return res.blob();
}

function renderMetrics(stats) {
  document.getElementById("metrics").innerHTML = `
    <div class="metric-card"><div class="value">${stats.total_transactions}</div><div class="label">Total Transactions</div></div>
    <div class="metric-card"><div class="value">${stats.success_rate}%</div><div class="label">Success Rate</div></div>
    <div class="metric-card"><div class="value">$${stats.total_volume.toLocaleString()}</div><div class="label">Total Volume</div></div>
  `;
}

function renderCharts(stats) {
  Object.values(charts).forEach(c => c.destroy());
  charts = {};

  charts.merchant = new Chart(document.getElementById("merchantChart"), {
    type: "bar",
    data: {
      labels: Object.keys(stats.top_merchants_by_volume),
      datasets: [{ label: "Volume ($)", data: Object.values(stats.top_merchants_by_volume), backgroundColor: "#4f6ef7", borderRadius: 6 }]
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
  });

  charts.status = new Chart(document.getElementById("statusChart"), {
    type: "doughnut",
    data: {
      labels: ["Success", "Failed"],
      datasets: [{ data: [stats.successful, stats.failed], backgroundColor: ["#2e7d32", "#e53935"], borderWidth: 0 }]
    },
    options: { plugins: { legend: { position: "bottom" } }, cutout: "65%" }
  });

  if (stats.failure_reasons && Object.keys(stats.failure_reasons).length > 0) {
    charts.reason = new Chart(document.getElementById("reasonChart"), {
      type: "bar",
      data: {
        labels: Object.keys(stats.failure_reasons),
        datasets: [{ label: "Count", data: Object.values(stats.failure_reasons), backgroundColor: "#e53935", borderRadius: 6 }]
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } }, indexAxis: "y" }
    });
  }
}

downloadBtn.addEventListener("click", () => {
  if (!pdfBlob) return;
  const url = URL.createObjectURL(pdfBlob);
  const a = document.createElement("a");
  a.href = url; a.download = "payment_report.pdf"; a.click();
  URL.revokeObjectURL(url);
});
