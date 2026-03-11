let cy;
let allPapers = [];
let allRelations = [];

async function loadData() {
  const [papersRes, relationsRes] = await Promise.all([
    fetch("data/papers.json"),
    fetch("data/relations.json"),
  ]);

  if (!papersRes.ok || !relationsRes.ok) {
    throw new Error("Failed to load JSON data. Make sure you are using a local server.");
  }

  allPapers = await papersRes.json();
  allRelations = await relationsRes.json();

  populateFilters(allPapers);
  renderGraph(allPapers, allRelations);
}

function populateFilters(papers) {
  const themeFilter = document.getElementById("themeFilter");
  const methodFilter = document.getElementById("methodFilter");

  const themes = new Set();
  const methods = new Set();

  papers.forEach((paper) => {
    (paper.themes || []).forEach((theme) => themes.add(theme));
    (paper.methods || []).forEach((method) => methods.add(method));
  });

  [...themes].sort().forEach((theme) => {
    const option = document.createElement("option");
    option.value = theme;
    option.textContent = theme;
    themeFilter.appendChild(option);
  });

  [...methods].sort().forEach((method) => {
    const option = document.createElement("option");
    option.value = method;
    option.textContent = method;
    methodFilter.appendChild(option);
  });

  themeFilter.addEventListener("change", applyFilters);
  methodFilter.addEventListener("change", applyFilters);
  document.getElementById("resetBtn").addEventListener("click", resetFilters);
}

function applyFilters() {
  const themeValue = document.getElementById("themeFilter").value;
  const methodValue = document.getElementById("methodFilter").value;

  const filteredPapers = allPapers.filter((paper) => {
    const themeMatch = !themeValue || (paper.themes || []).includes(themeValue);
    const methodMatch = !methodValue || (paper.methods || []).includes(methodValue);
    return themeMatch && methodMatch;
  });

  const filteredIds = new Set(filteredPapers.map((p) => p.id));

  const filteredRelations = allRelations.filter(
    (rel) => filteredIds.has(rel.source) && filteredIds.has(rel.target)
  );

  renderGraph(filteredPapers, filteredRelations);

  const detail = document.getElementById("paperDetail");
  detail.innerHTML = `
    <h2>Filtered view</h2>
    <p class="meta">${filteredPapers.length} paper(s) shown</p>
    <p>Click a node to see details.</p>
  `;
}

function resetFilters() {
  document.getElementById("themeFilter").value = "";
  document.getElementById("methodFilter").value = "";
  renderGraph(allPapers, allRelations);

  const detail = document.getElementById("paperDetail");
  detail.innerHTML = `
    <h2>Select a paper</h2>
    <p>Click a node to see details.</p>
  `;
}

function renderGraph(papers, relations) {
  const elements = [];

  papers.forEach((paper) => {
  elements.push({
    data: {
      id: paper.id,
      label: paper.label || paper.title,
      title: paper.title,
      year: paper.year || "n.d.",
      color: paper.color || "#888888"
    }
  });
});

  relations.forEach((rel, index) => {
    elements.push({
      data: {
        id: `edge-${index}-${rel.source}-${rel.target}`,
        source: rel.source,
        target: rel.target,
        label: rel.type || "related",
      },
    });
  });

  if (cy) {
    cy.destroy();
  }

  cy = cytoscape({
    container: document.getElementById("cy"),
    elements,
    style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "background-color": "data(color)",
              color: "#f4f4f4",
              "font-size": "10px",
              "font-weight": "600",
              "text-wrap": "wrap",
              "text-max-width": "90px",
              "text-valign": "center",
              "text-halign": "center",
              width: 58,
              height: 58,
              "overlay-padding": "6px",
              "border-width": 2,
              "border-color": "#1c1c1c"
            },
          },
          {
            selector: "edge",
            style: {
              width: 1.6,
              "line-color": "#555",
              "target-arrow-color": "#555",
              "target-arrow-shape": "none",
              "curve-style": "bezier",
              opacity: 0.7
            },
          },
          {
            selector: "node:selected",
            style: {
              "border-width": 4,
              "border-color": "#ffffff",
              "font-size": "11px"
            },
          },
          {
            selector: ".faded",
            style: {
              opacity: 0.2
            }
          }
        ],
    layout: {
      name: "cose",
        animate: true,
        animationDuration: 500,
        fit: true,
        padding: 50,
        nodeRepulsion: 9000,
        idealEdgeLength: 10,
        edgeElasticity: 120,
        gravity: 0.25
          },
  });

  cy.on("tap", "node", (event) => {
    const paperId = event.target.id();
    const paper = papers.find((p) => p.id === paperId);
    if (paper) {
      renderPaperDetail(paper);
    }
  });
}

function renderPaperDetail(paper) {
  const detail = document.getElementById("paperDetail");

  detail.innerHTML = `
    <h2>${escapeHtml(paper.title || "Untitled")}</h2>
    <p class="meta">
      ${(paper.authors || []).map(escapeHtml).join(", ") || "Unknown author"}<br>
      ${paper.year || "No year"}<br>
      ${escapeHtml(paper.status || "")}
    </p>

    <h3>Summary</h3>
    <p>${paper.summary ? escapeHtml(paper.summary) : '<span class="empty">No summary yet.</span>'}</p>

    <h3>Themes</h3>
    ${renderTagList(paper.themes)}

    <h3>Methods</h3>
    ${renderTagList(paper.methods)}

    <h3>Tensions</h3>
    ${renderTagList(paper.tensions)}

    <h3>Key Concepts</h3>
    ${renderTagList(paper.key_concepts)}

    <h3>Notes</h3>
    <p>${paper.notes ? nl2br(escapeHtml(paper.notes)) : '<span class="empty">No notes yet.</span>'}</p>

    <h3>Related</h3>
    ${renderRelatedList(paper.related)}
  `;
}

function renderTagList(items = []) {
  if (!items.length) {
    return '<p class="empty">None</p>';
  }

  return `
    <ul class="tag-list">
      ${items.map((item) => `<li class="tag">${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderRelatedList(related = []) {
  if (!related.length) {
    return '<p class="empty">No related papers listed.</p>';
  }

  return `
    <ul class="related-list">
      ${related.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function nl2br(text) {
  return text.replace(/\n/g, "<br>");
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

loadData().catch((error) => {
  console.error(error);
  const detail = document.getElementById("paperDetail");
  detail.innerHTML = `
    <h2>Could not load data</h2>
    <p>${escapeHtml(error.message)}</p>
    <p>You probably opened the HTML file directly instead of using a local server.</p>
  `;
});