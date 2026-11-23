(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const form = $("#search-form");
  const queryInput = $("#query");
  const modeSelect = $("#mode");
  const rankingSelect = $("#ranking");
  const facultySelect = $("#faculty");
  const weightInput = $("#weight");
  const weightValue = $("#weight-value");
  const weightRow = $("#weight-row");
  const searchButton = $("#search-button");
  const resultsSection = $("#results-section");
  const resultsList = $("#results-list");
  const resultsMessage = $("#results-message");
  const resultCount = $("#result-count");
  const pagination = $("#pagination");
  const previousPage = $("#previous-page");
  const nextPage = $("#next-page");
  const pageIndicator = $("#page-indicator");
  const apiStatus = $("#api-status");

  const state = {
    query: "",
    mode: "OR",
    ranking: "tfidf",
    faculty: "all",
    weight: 0.7,
    page: 1,
    perPage: 10,
    lastResponse: null,
  };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
  }

  function updateWeightLabel() {
    const percentage = Math.round(Number(weightInput.value) * 100);
    weightValue.textContent = `${percentage} % TF-IDF · ${100 - percentage} % PageRank`;
    state.weight = Number(weightInput.value);
  }

  function updateRankingControls() {
    weightRow.hidden = rankingSelect.value !== "hibrido";
  }

  async function loadFaculties() {
    try {
      const response = await fetch("/api/facultades", { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("No se pudo cargar el catálogo de facultades.");
      const data = await response.json();
      for (const faculty of data.facultades || []) {
        const option = document.createElement("option");
        option.value = faculty.id;
        option.textContent = faculty.nombre;
        facultySelect.appendChild(option);
      }
    } catch (error) {
      apiStatus.textContent = `${error.message} Comprueba que Flask y Apache estén iniciados.`;
      apiStatus.classList.add("status-error");
    }
  }

  async function loadHealth() {
    try {
      const response = await fetch("/api/health", { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("La API no respondió correctamente.");
      const data = await response.json();
      $("#stat-documents").textContent = data.corpus.documentos;
      $("#stat-faculties").textContent = data.corpus.facultades;
      $("#stat-terms").textContent = Number(data.corpus.terminos_unicos).toLocaleString("es-MX");
      $("#stat-links").textContent = Number(data.corpus.aristas).toLocaleString("es-MX");
      apiStatus.textContent = "Motor de búsqueda conectado · API disponible";
      apiStatus.classList.remove("status-error");
      apiStatus.classList.add("status-ok");
    } catch (error) {
      apiStatus.textContent = "API no disponible. Inicia Flask y verifica el proxy /api/ de Apache.";
      apiStatus.classList.remove("status-ok");
      apiStatus.classList.add("status-error");
    }
  }

  function scoreMarkup(document) {
    const values = [];
    if (Number.isFinite(document.score_tfidf)) {
      values.push(`<span class="score-chip">TF-IDF <strong>${document.score_tfidf.toFixed(4)}</strong></span>`);
    }
    if (Number.isFinite(document.score_pagerank)) {
      values.push(`<span class="score-chip">PageRank <strong>${document.score_pagerank.toFixed(6)}</strong></span>`);
    }
    if (Number.isFinite(document.score_hibrido)) {
      values.push(`<span class="score-chip score-primary">Híbrido <strong>${document.score_hibrido.toFixed(4)}</strong></span>`);
    }
    if (values.length === 0) values.push('<span class="score-chip">Orden por identificador</span>');
    return values.join("");
  }

  function renderResults(data) {
    state.lastResponse = data;
    resultsList.innerHTML = "";
    const results = data.resultados || [];
    const page = data.paginacion || { pagina: 1, total_paginas: 0, total_resultados: 0 };

    resultCount.textContent = `${page.total_resultados} documento${page.total_resultados === 1 ? "" : "s"} encontrado${page.total_resultados === 1 ? "" : "s"}`;
    if (page.total_resultados === 0) {
      resultsMessage.hidden = false;
      resultsMessage.innerHTML = '<div class="empty-icon" aria-hidden="true">?</div><h3>No encontramos documentos</h3><p>Prueba con otros términos, cambia OR/AND o selecciona otra facultad.</p>';
      pagination.hidden = true;
      return;
    }

    resultsMessage.hidden = true;
    const methodLabel = {
      tfidf: "Ordenado por relevancia textual · TF-IDF",
      pagerank: "Ordenado por importancia de enlaces · PageRank",
      hibrido: "Ordenado por combinación de TF-IDF y PageRank",
      ninguno: "Ordenado por identificador de documento",
    }[state.ranking];

    for (const document of results) {
      const matched = (document.terminos_coincidentes || [])
        .map((term) => `<span class="term-chip">${escapeHtml(term)}</span>`).join("");
      const article = `
        <article class="result-card">
          <div class="result-topline"><span class="document-id">${escapeHtml(document.id)}</span><span class="faculty-name">${escapeHtml(document.facultad)}</span></div>
          <h3><a href="${escapeHtml(document.url)}">${escapeHtml(document.titulo)}</a></h3>
          <p class="result-snippet">${escapeHtml(document.fragmento)}</p>
          <div class="result-bottom"><div class="score-list">${scoreMarkup(document)}</div><a class="open-document" href="${escapeHtml(document.url)}">Abrir artículo <span aria-hidden="true">↗</span></a></div>
          ${matched ? `<div class="matched-terms"><span>Coincidencias:</span>${matched}</div>` : ""}
        </article>`;
      resultsList.insertAdjacentHTML("beforeend", article);
    }

    pagination.hidden = page.total_paginas <= 1;
    previousPage.disabled = !page.hay_anterior;
    nextPage.disabled = !page.hay_siguiente;
    pageIndicator.textContent = `Página ${page.pagina} de ${page.total_paginas}`;

    const summary = document.createElement("p");
    summary.className = "ranking-summary";
    summary.textContent = `${methodLabel}${data.facultad_filtro ? ` · ${data.facultad_filtro}` : ""}`;
    resultsList.prepend(summary);
  }

  async function executeSearch(page = 1) {
    const query = queryInput.value.trim();
    if (!query) {
      queryInput.focus();
      return;
    }

    state.query = query;
    state.mode = modeSelect.value;
    state.ranking = rankingSelect.value;
    state.faculty = facultySelect.value;
    state.page = page;
    state.weight = Number(weightInput.value);
    state.perPage = 10;

    searchButton.disabled = true;
    searchButton.textContent = "Buscando…";
    resultsSection.setAttribute("aria-busy", "true");
    resultsMessage.hidden = false;
    resultsMessage.innerHTML = '<div class="loading-spinner" aria-hidden="true"></div><h3>Buscando documentos</h3><p>Consultando el índice invertido y calculando el orden seleccionado…</p>';
    resultsList.innerHTML = "";
    pagination.hidden = true;

    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          q: state.query,
          modo: state.mode,
          ranking: state.ranking,
          facultad: state.faculty,
          peso_tfidf: state.weight,
          pagina: state.page,
          por_pagina: state.perPage,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "No se pudo completar la búsqueda.");
      renderResults(data);
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
      resultsMessage.hidden = false;
      resultsMessage.innerHTML = `<div class="empty-icon" aria-hidden="true">!</div><h3>No fue posible realizar la búsqueda</h3><p>${escapeHtml(error.message)}</p>`;
      resultCount.textContent = "Error en la búsqueda";
    } finally {
      searchButton.disabled = false;
      searchButton.innerHTML = 'Buscar <span aria-hidden="true">→</span>';
      resultsSection.setAttribute("aria-busy", "false");
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    executeSearch(1);
  });

  rankingSelect.addEventListener("change", updateRankingControls);
  weightInput.addEventListener("input", updateWeightLabel);
  previousPage.addEventListener("click", () => executeSearch(Math.max(1, state.page - 1)));
  nextPage.addEventListener("click", () => executeSearch(state.page + 1));

  document.querySelectorAll(".quick-query").forEach((button) => {
    button.addEventListener("click", () => {
      queryInput.value = button.dataset.query || "";
      executeSearch(1);
    });
  });

  updateWeightLabel();
  updateRankingControls();
  loadFaculties();
  loadHealth();
})();
