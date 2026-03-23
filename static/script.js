const buscarBtn = document.getElementById("buscarBtn");
const downloadBtn = document.getElementById("downloadBtn");
const keywordInput = document.getElementById("keyword");
const ufSelect = document.getElementById("uf");
const dataInicioInput = document.getElementById("dataInicio");
const spinner = document.getElementById("spinner");
const statusBox = document.getElementById("statusBox");
const logs = document.getElementById("logs");
const tBody = document.getElementById("tBody");

const API_BASE = ""; // mesmo host

function setStatus(msg, type = "info") {
  const colors = {
    info: "text-gray-300",
    success: "text-emerald-400",
    error: "text-red-400",
  };
  statusBox.className = `${colors[type] || colors.info}`;
  statusBox.textContent = msg;
}

function addLog(line) {
  const div = document.createElement("div");
  const ts = new Date().toLocaleTimeString("pt-BR", { hour12: false });
  div.textContent = `[${ts}] ${line}`;
  logs.appendChild(div);
  logs.scrollTop = logs.scrollHeight;
}

function renderTable(data) {
  tBody.innerHTML = "";
  data.forEach((row) => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-gray-800";

    const orgao = document.createElement("td");
    orgao.className = "px-3 py-2";
    orgao.textContent = row.orgao || "-";

    const objeto = document.createElement("td");
    objeto.className = "px-3 py-2";
    objeto.textContent = row.objeto || "-";

    const valor = document.createElement("td");
    valor.className = "px-3 py-2";
    valor.textContent = row.valorEstimado ? `R$ ${Number(row.valorEstimado).toLocaleString("pt-BR")}` : "-";

    const link = document.createElement("td");
    link.className = "px-3 py-2";
    if (row.link) {
      const a = document.createElement("a");
      a.href = row.link;
      a.target = "_blank";
      a.rel = "noreferrer";
      a.className = "text-emerald-400 hover:underline";
      a.textContent = "Abrir";
      link.appendChild(a);
    } else {
      link.textContent = "-";
    }

    tr.appendChild(orgao);
    tr.appendChild(objeto);
    tr.appendChild(valor);
    tr.appendChild(link);

    tBody.appendChild(tr);
  });
}

async function buscar() {
  const keyword = keywordInput.value.trim();
  const uf = ufSelect.value;
  const dataInicio = dataInicioInput.value || null;

  if (!keyword) {
    setStatus("Informe a palavra-chave.", "error");
    return;
  }

  spinner.classList.remove("hidden");
  buscarBtn.disabled = true;
  downloadBtn.classList.add("hidden");
  setStatus("Consultando PNCP...", "info");
  addLog(`Iniciando busca: "${keyword}" UF=${uf || 'todas'} data>=${dataInicio || '-'}`);

  try {
    const resp = await fetch(`${API_BASE}/buscar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keyword, uf, dataInicio }),
    });
    const data = await resp.json();

    (data.logs || []).forEach(addLog);

    if (!resp.ok || data.status !== "success") {
      throw new Error(data.message || "Falha na busca");
    }

    setStatus(`Encontrados ${data.total} resultados.`, "success");
    renderTable(data.data || []);
    downloadBtn.classList.remove("hidden");
  } catch (err) {
    setStatus(err.message || "Erro inesperado", "error");
    addLog(`Erro: ${err.message}`);
  } finally {
    spinner.classList.add("hidden");
    buscarBtn.disabled = false;
  }
}

buscarBtn.addEventListener("click", buscar);
keywordInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") buscar();
});

downloadBtn.addEventListener("click", () => {
  window.location.href = `${API_BASE}/download`;
});
