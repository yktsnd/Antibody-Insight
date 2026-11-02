"use strict";

// UI state and display only; identity/provenance rules live in the Python domain.
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pretty = (value) => esc(JSON.stringify(value, null, 2));
const screenNames = {E:"Candidate Explorer", W:"Molecule Workspace", D:"Design & Compare", R:"Evidence & Decision"};
let csrf = "", projects = [], bundle = null, pendingImport = null, pendingShortlist = null;
let state = {screen:"E", selected:[], focus:null, chains:{}, position:null, filter:""};
let loading = false;
let indexedBundle = null, indexedEntities = null;

async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method:"POST", headers:{"Content-Type":"application/json", "X-CSRF-Token":csrf}, body:JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error([result.error, ...(result.details || [])].join("\n"));
  return result;
}
function notify(message, error = false) {
  const box = $("#notification"); box.hidden = false; box.className = error ? "error" : ""; box.textContent = message;
}
function safeStorage(key, value) {
  try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch { /* DB persistence still works. */ }
}
function remember() {
  if (bundle) safeStorage("awx-state-" + bundle.project.id, JSON.stringify(state));
}
function entities(type) { return bundle ? bundle.entities.filter((e) => e.type === type) : []; }
function selectedMolecules() { return entities("molecule").filter((m) => state.selected.includes(m.id)); }
function index() {
  if (indexedBundle !== bundle || indexedEntities === null) {
    indexedBundle = bundle; indexedEntities = new Map((bundle?.entities || []).map((e) => [e.id, e]));
  }
  return indexedEntities;
}
function subjectPath(evidence) {
  const records = index(); let subject = records.get(evidence.subject_id); const path = [];
  while (subject) {
    path.push(subject);
    if (subject.type === "material") subject = records.get(subject.construct_id);
    else if (subject.type === "construct") subject = records.get(subject.molecule_id);
    else break;
  }
  return path;
}
function selectedEvidence() {
  return entities("evidence").filter((e) => subjectPath(e).some((s) => s.type === "molecule" && state.selected.includes(s.id)));
}
function heading(label, title, description) {
  return `<div class="page-heading"><div><p class="eyebrow">${label}</p><h1>${title}</h1><p class="muted">${description}</p></div><span class="project-chip">${esc(bundle?.project.title || "No active project")}</span></div>`;
}
function fixtureBanner() { return bundle?.project.title.includes("[SYNTHETIC FIXTURE]") ? '<div class="fixture-notice">Synthetic engineering fixture. Values are invented test data, not real experiments or model predictions.</div>' : ""; }
function emptySelection() { return '<div class="panel empty"><h2>Choose candidates to continue</h2><p class="muted">Select candidates in the Explorer. Their IDs remain selected as you move through the workspace.</p><button data-screen="E">Open Candidate Explorer</button></div>'; }
function render() {
  remember();
  document.querySelectorAll("nav [data-screen]").forEach((b) => { b.classList.toggle("active", b.dataset.screen === state.screen); b.setAttribute("aria-current", b.dataset.screen === state.screen ? "page" : "false"); });
  $("#selection-count").textContent = `${state.selected.length} selected`;
  $("#breadcrumb").textContent = `${bundle?.project.title || "Project"} / ${screenNames[state.screen]}`;
  if (state.screen === "W") {
    const active = entities("molecule").find((m) => m.id === state.focus) || selectedMolecules()[0];
    if (active) {
      const chain = active.chains.find((c) => c.id === state.chains[active.id]) || active.chains[0];
      $("#breadcrumb").textContent += ` / ${active.external_id} / ${chain.id}${state.position ? " / index " + state.position : ""}`;
    }
  }
  $("#export-button").disabled = !bundle;
  $("#content").innerHTML = fixtureBanner() + ({E:renderExplorer, W:renderWorkspace, D:renderDesign, R:renderEvidence}[state.screen])();
}

function renderExplorer() {
  const molecules = entities("molecule");
  const repeated = new Map();
  for (const m of molecules) {
    const signature = JSON.stringify(m.chains.map((c) => c.sequence));
    repeated.set(signature, (repeated.get(signature) || 0) + 1);
  }
  const duplicateCount = molecules.filter((m) => repeated.get(JSON.stringify(m.chains.map((c) => c.sequence))) > 1).length;
  const shown = molecules.filter((m) => (m.name + " " + m.external_id + " " + m.format).toLowerCase().includes(state.filter.toLowerCase()));
  const evidence = entities("evidence");
  let html = heading("OBSERVE · COMPARE · SELECT", "Candidate Explorer", "Keep candidate identity and the evidence behind your next question in view.");
  if (!bundle) return html + `<div class="panel empty"><p class="eyebrow">START WITH YOUR RESEARCH QUESTION</p><h2>A connected place to inspect candidates</h2><p class="muted">Import sequences or a workspace bundle, inspect their identity and provenance, then save the reason behind a shortlist.</p><button data-action="import">Import local data</button><p class="subtle">FASTA · Sequence CSV · Workspace JSON</p></div>`;
  html += `<div class="stats"><div class="stat"><span>CANDIDATES</span><div class="number" id="candidate-count">${molecules.length}</div><div class="foot">Distinct persistent IDs</div></div><div class="stat"><span>SELECTED</span><div class="number">${state.selected.length}</div><div class="foot">Context across all four screens</div></div><div class="stat"><span>EVIDENCE RECORDS</span><div class="number">${evidence.length}</div><div class="foot">${evidence.filter((e) => e.kind === "measured").length} measured · ${evidence.filter((e) => e.kind === "computed").length} computed</div></div><div class="stat"><span>SEQUENCE REPEATS</span><div class="number">${duplicateCount}</div><div class="foot">Flagged, never merged</div></div></div>`;
  html += `<div class="panel"><div class="panel-head"><h2>Research candidates <span class="subtle">${shown.length} shown</span></h2><input class="search" id="candidate-search" type="search" placeholder="Search name, external ID or format" aria-label="Search candidates" value="${esc(state.filter)}"></div>`;
  if (state.selected.length) html += `<div class="selected-strip"><span>${state.selected.length} candidate IDs held in context</span><div><button class="text-button" data-screen="W">Inspect sequences →</button> <button class="text-button" data-screen="R">Record selection →</button></div></div>`;
  html += `<div class="table-wrap"><table><thead><tr><th>Select</th><th>Candidate</th><th>Format / chains</th><th>Sequence QC</th><th>Evidence</th></tr></thead><tbody>`;
  for (const m of shown) {
    const ev = evidence.filter((e) => subjectPath(e).some((s) => s.id === m.id));
    const repeat = repeated.get(JSON.stringify(m.chains.map((c) => c.sequence))) > 1;
    html += `<tr class="${state.selected.includes(m.id) ? "selected" : ""}"><td><input type="checkbox" data-select="${m.id}" aria-label="Select ${esc(m.external_id)}" ${state.selected.includes(m.id) ? "checked" : ""}></td><td><button class="name-button" data-open="${m.id}">${esc(m.name)}</button><small>${esc(m.external_id)}</small></td><td>${esc(m.format)}<small>${m.chains.length} chain${m.chains.length === 1 ? "" : "s"} · ${m.chains.reduce((n, c) => n + c.sequence.length, 0)} aa</small></td><td><span class="tag ${repeat ? "warning" : ""}">${repeat ? "Sequence repeat" : "Imported sequence"}</span><small>Numbering not registered</small></td><td>${ev.length ? `${ev.length} record${ev.length === 1 ? "" : "s"}<small>Traceable to subject IDs</small>` : '<span class="muted">Not measured / not predicted</span>'}</td></tr>`;
  }
  return html + '</tbody></table></div><div class="panel-body subtle">Sequence repeats do not establish molecular identity. CDR grouping and assay-aware sorting are scheduled for later milestones.</div></div>';
}

function renderWorkspace() {
  let html = heading("FOLLOW THE MOLECULE", "Molecule Workspace", "Inspect chain identity and sequence positions without inventing biological correspondence.");
  const selected = selectedMolecules();
  const focus = entities("molecule").find((m) => m.id === state.focus);
  const molecules = focus ? [focus, ...selected.filter((m) => m.id !== focus.id)] : selected;
  if (!molecules.length) return html + emptySelection();
  html += '<p class="muted">Sequence indexes are 1-based. This is an unaligned position comparison; equal indexes do not establish homologous residues. IMGT numbering: mapping unavailable. Structure: not registered.</p>';
  if (molecules.length > 2) html += `<p class="muted">Showing the first 2 of ${molecules.length} candidates in context. The full selection is retained.</p>`;
  const displayed = molecules.slice(0, 2);
  const chains = displayed.map((m) => m.chains.find((c) => c.id === state.chains[m.id]) || m.chains[0]);
  html += '<div class="two-columns">';
  for (let n = 0; n < displayed.length; n++) {
    const m = displayed[n], chain = chains[n], other = chains[1 - n];
    html += `<div class="panel"><div class="panel-head"><div><h2>${esc(m.name)}</h2><p class="subtle">${esc(m.external_id)}</p></div><span class="tag">${esc(m.format)}</span></div><div class="panel-body"><p class="mono">Molecule: ${m.id}</p><label class="field">Chain<select data-chain="${m.id}" aria-label="Chain for ${esc(m.external_id)}">${m.chains.map((c) => `<option value="${esc(c.id)}" ${c.id === chain.id ? "selected" : ""}>${esc(c.id)} / ${esc(c.role)} / ${c.sequence.length} aa</option>`).join("")}</select></label><div class="sequence">`;
    // Long chains stay inspectable without rendering hundreds of thousands of buttons.
    const start = state.position && state.position > 200 ? Math.floor((state.position - 1) / 200) * 200 : 0;
    for (let i = start; i < Math.min(start + 200, chain.sequence.length); i++) {
      const difference = other && (other.sequence[i] ?? "absent") !== chain.sequence[i];
      html += `<button class="residue ${difference ? "diff" : ""} ${state.position === i + 1 ? "active" : ""}" data-position="${i + 1}" aria-label="${esc(m.external_id)} ${esc(chain.id)} sequence index ${i + 1} ${chain.sequence[i]}"><small>${i + 1}</small>${chain.sequence[i]}</button>`;
    }
    html += `</div><label class="field">Jump to sequence index<input type="number" data-jump="${m.id}" min="1" max="${chain.sequence.length}" value="${state.position || 1}"></label><p class="sequence-details">${state.position ? `Selected index ${state.position}: ${esc(chain.sequence[state.position - 1] || "absent in this chain")} · numbering mapping unavailable` : "Choose a sequence index to compare. Gold marks raw position differences."}</p><details><summary>Sequence source and raw record</summary><p>${esc(m.source.name)} / ${esc(m.source.version || "version unknown")}</p><pre>${pretty(m)}</pre></details>`;
    html += renderComposition(m);
    const constructs = entities("construct").filter((c) => c.molecule_id === m.id);
    html += '<p class="section-label">CONSTRUCTS & MATERIALS</p>';
    html += constructs.length ? constructs.map((c) => `<details><summary>${esc(c.name)} (${c.id})</summary><pre>${pretty(c)}</pre><p class="muted">CDS translation and signal-peptide processing are not validated.</p>${entities("material").filter((s) => s.construct_id === c.id).map((s) => `<p class="muted">${esc(s.name)} / lot ${esc(s.lot)}<br><span class="mono">${s.id}</span></p>`).join("")}</details>`).join("") : '<p class="muted">No construct or material registered.</p>';
    html += '</div></div>';
  }
  return html + '</div><button data-screen="R">Follow evidence and record a question →</button>';
}

function renderComposition(molecule) {
  let html = '<p class="section-label">DECLARED MOLECULAR COMPOSITION</p>';
  const graph = molecule.component_graph;
  if (!graph) html += '<p class="muted">Composition undefined. Chain pairing, domain order and copy counts were not supplied; nothing is inferred.</p>';
  else {
    html += '<p class="muted">Declared metadata; folding, pairing and assembly are not validated. Connections refer to component definitions, not individual chain-copy contacts.</p>';
    for (const chain of graph.chains) {
      html += `<div class="composition-chain"><h3>${esc(chain.chain_id)} · ${chain.copies} declared ${chain.copies === 1 ? "copy" : "copies"}</h3><div class="component-order">`;
      for (const component of chain.components) {
        html += `<details class="component-item"><summary>${esc(component.id)} / ${esc(component.role)} / ${component.sequence.length} aa</summary>`;
        if (component.origin) {
          const origin = component.origin, unit = index().get(origin.binding_unit_id);
          html += `<p class="muted">Binding unit: ${esc(unit?.name)}<br><span class="mono">${esc(origin.binding_unit_id)}</span><br>Chain ${esc(origin.chain_id)}, raw indexes ${origin.start}–${origin.end}</p>`;
          if (unit) {
            html += `<p class="muted">Topology: ${esc(unit.topology)}<br>Source: ${esc(unit.source.name)} / ${esc(unit.source.version || "version unknown")}</p><pre>${pretty(unit)}</pre>`;
            html += unit.chains.filter((c) => c.origin).map((c) => `<button class="text-button" data-open="${c.origin.molecule_id}">Inspect unit origin: ${esc(index().get(c.origin.molecule_id)?.name)} / ${esc(c.origin.chain_id)} / indexes ${c.origin.start}–${c.origin.end}</button>`).join("");
          }
        } else html += '<p class="muted">Explicit sequence declaration. No binding-unit origin supplied.</p>';
        html += `<p class="mono">${esc(component.sequence)}</p></details>`;
      }
      html += '</div></div>';
    }
    html += '<details><summary>Declared connections and complete component graph</summary><pre>' + pretty(graph) + '</pre></details>';
  }
  const lineage = entities("lineage").filter((edge) => edge.parent_id === molecule.id || edge.child_id === molecule.id);
  html += '<p class="section-label">PARENT / CHILD COMPOSITION HISTORY</p>';
  html += lineage.length ? lineage.map((edge) => {
    const parent = index().get(edge.parent_id), child = index().get(edge.child_id);
    return `<details><summary>${esc(parent?.name)} → ${esc(child?.name)}</summary><p class="mono">${edge.id}</p><p class="muted">${esc(edge.change_set.reason)}</p><button class="text-button" data-open="${edge.parent_id}">Inspect parent</button> <button class="text-button" data-open="${edge.child_id}">Inspect child</button><p class="muted">Parent measurements stay on the original material. This history creates no child measurements.</p><pre>${pretty(edge.change_set)}</pre></details>`;
  }).join("") : '<p class="muted">No lineage record registered.</p>';
  return html;
}

function renderDesign() {
  return heading("PRESERVE THE DESIGN HISTORY", "Design & Compare", "A shared design context for mutations, molecular composition and expression constructs.") +
    `<div class="panel"><div class="panel-body"><h2>Design operations are not implemented in this build</h2><p class="muted">${state.selected.length} selected candidate IDs remain in context. No design result or scientific score is generated. Imported declared component graphs and composition lineage can be inspected in W.</p><ul class="scope-list"><li>M2: verified numbering and structure correspondence</li><li>M3: create numbered mutations, lineage and molecular assemblies interactively</li><li>M4: construct comparisons and experimental questions</li></ul><button data-screen="W" class="secondary">Inspect source sequences</button></div></div>`;
}

function renderEvidence() {
  let html = heading("RETAIN THE REASONING", "Evidence & Decision", "Separate observations from calculations, and keep the subject and source attached.");
  if (!state.selected.length) return html + emptySelection();
  const evidence = selectedEvidence();
  html += `<div class="two-columns"><div><div class="panel"><div class="panel-head"><h2>Evidence for ${state.selected.length} selected candidates</h2><span class="subtle">${evidence.length} records</span></div>`;
  if (!evidence.length) html += '<div class="panel-body"><p class="muted">Not measured / not predicted. No evidence records were registered for this selection.</p></div>';
  for (const e of evidence) {
    const path = subjectPath(e);
    html += `<article class="evidence-row"><div class="metric"><div><span class="tag ${esc(e.kind)}">${esc(e.kind)}</span><p>${esc(e.metric)}</p></div><div class="value">${e.value === null ? '<span class="muted">Value missing</span>' : esc(e.value) + ' <span class="muted">' + esc(e.unit) + '</span>'}</div></div><p class="muted">${path.map((p) => `${esc(p.type)}: ${esc(p.name)}`).join(" → ")}</p><p>Source: ${esc(e.source.name)} / ${esc(e.source.version || "version unknown")}<br>Event time: ${esc(e.timestamp)}</p><p>${e.conditions === null ? '<span class="tag warning">Conditions unknown — do not pool</span>' : 'Conditions: ' + esc(JSON.stringify(e.conditions))}</p>${e.kind === "computed" ? '<p class="muted">Computed result. Interpretation and uncertainty depend on the source; this is not an experimental measurement.</p>' : ""}<details><summary>Original record, subject IDs & provenance</summary><pre>${pretty(e)}</pre>${path.map((p) => `<p class="mono">${esc(p.type)}: ${p.id}</p>`).join("")}</details><label class="evidence-check"><input type="checkbox" data-evidence="${e.id}" checked> Include in draft snapshot</label></article>`;
  }
  html += '</div></div><div><div class="panel"><div class="panel-head"><h2>Save a shortlist draft</h2><span class="tag">Draft only</span></div><div class="panel-body"><p class="muted">Record why these candidates deserve further investigation. Final decisions with criteria, weights and missing-data gates are scheduled for M4.</p><p class="section-label">CANDIDATES IN CONTEXT</p>';
  html += selectedMolecules().map((m) => `<p class="wrap">${esc(m.external_id)} — ${esc(m.name)}<br><span class="mono">${m.id}</span></p>`).join("");
  html += '<label class="field">Reason and next research question<textarea id="shortlist-reason" rows="5" placeholder="What did you observe? Why keep this selection? What remains unverified?"></textarea></label><button id="review-shortlist">Review before saving</button></div></div>';
  const decisions = entities("decision").filter((d) => d.candidate_ids.some((id) => state.selected.includes(id)));
  html += `<div class="panel"><div class="panel-head"><h2>Saved shortlist drafts</h2><span class="subtle">${decisions.length} records</span></div>`;
  if (!decisions.length) html += '<p class="panel-body muted">No saved draft for this selection.</p>';
  for (const d of decisions.toReversed()) html += `<article class="saved-draft"><span class="tag">Draft · immutable record</span><p>${esc(d.reason)}</p><p class="muted">${d.candidate_ids.length} candidate IDs · ${d.evidence_snapshot.length} evidence snapshots<br>${esc(d.timestamp)}</p><button class="text-button" data-restore="${d.id}">Restore this selection</button><details><summary>Saved IDs and frozen evidence</summary><pre>${pretty(d)}</pre></details></article>`;
  return html + '</div></div></div><p class="muted">Measurements are not averaged or ranked across different units or conditions. Missing values remain unknown.</p>';
}

async function loadProject(id) {
  bundle = await api("/api/bundle?project_id=" + encodeURIComponent(id));
  let saved;
  try { saved = JSON.parse(safeStorage("awx-state-" + id) || "null"); } catch { saved = null; }
  state = {screen:"E", selected:[], focus:null, chains:{}, position:null, filter:""};
  if (saved && Array.isArray(saved.selected)) {
    const ids = new Set(entities("molecule").map((m) => m.id));
    state = {...state, ...saved, screen:screenNames[saved.screen] ? saved.screen : "E", selected:saved.selected.filter((x) => ids.has(x))};
    if (state.selected.length !== saved.selected.length) notify("Some saved candidate IDs are unavailable; selection was not replaced with another candidate.", true);
  }
  safeStorage("awx-project", id); $("#project-select").value = id; render();
}
async function refreshProjects(preferred) {
  const boot = await api("/api/bootstrap"); csrf = boot.csrf; projects = boot.projects;
  $("#project-select").innerHTML = projects.length ? projects.map((p) => `<option value="${p.id}">${esc(p.title)}</option>`).join("") : '<option value="">No project yet</option>';
  $("#import-target").innerHTML = '<option value="">New project</option>' + projects.map((p) => `<option value="${p.id}">${esc(p.title)}</option>`).join("");
  const id = projects.find((p) => p.id === preferred)?.id || projects.find((p) => p.id === safeStorage("awx-project"))?.id || projects[0]?.id;
  if (id) await loadProject(id); else render();
}
function showImport() {
  pendingImport = null; $("#import-preview").hidden = true; $("#import-form").hidden = false;
  $("#import-target").value = bundle?.project.id || ""; $("#new-project-fields").hidden = !!bundle;
  $("#import-dialog").showModal();
}
function renderPreview(result, synthetic = false) {
  pendingImport = result.bundle;
  const r = result.report;
  $("#import-form").hidden = true; const target = $("#import-preview"); target.hidden = false;
  const samples = pendingImport.entities.filter((e) => e.type === "molecule").slice(0, 5);
  target.innerHTML = `<h2>Review before saving</h2>${synthetic ? '<p class="fixture-notice">Synthetic fixture. These are invented engineering values, not real scientific results.</p>' : ""}<p class="muted">Project: ${esc(pendingImport.project.title)}</p><div class="preview-summary">${r.total_rows} input rows · ${r.valid_rows} valid · ${r.excluded.length} excluded · ${r.duplicates.length} sequence-repeat warnings</div><p class="muted">${pendingImport.entities.length} entities will be added. Existing records are never overwritten. IDs and references are revalidated at save time.</p>${r.excluded.length ? `<h3>Excluded records (not saved)</h3><pre class="preview-list">${pretty(r.excluded)}</pre>` : ""}${r.duplicates.length || r.warnings.length ? `<details><summary>QC warnings</summary><pre class="preview-list">${pretty([...r.duplicates, ...r.warnings])}</pre></details>` : ""}<h3>Sample of incoming candidates</h3><ul class="muted">${samples.map((m) => `<li>${esc(m.external_id)} / ${esc(m.name)} / ${esc(m.format)}</li>`).join("")}</ul><details><summary>Incoming records and source metadata</summary><pre class="preview-list">${pretty(pendingImport.entities.slice(0, 8))}</pre></details><div class="dialog-actions"><button class="secondary" id="back-import">Back</button><button id="commit-import" ${pendingImport.entities.length ? "" : "disabled"}>Save ${r.valid_rows} valid rows${r.excluded.length ? " (excluded rows omitted)" : ""}</button></div>`;
}

const guides = {
  en:`<h3>Observe, then retain the reasoning</h3><ol class="scope-list"><li>Import a local FASTA, sequence CSV or awx/1 JSON. Inspect the preview and excluded rows before saving.</li><li>Select candidates in E. Open W to inspect chains and compare raw sequence indexes. These are not IMGT positions or an alignment.</li><li>In R, follow each evidence record to its source and subject. Measured values belong to a particular material and construct.</li><li>Write a reason, review the candidate IDs and evidence snapshot, and save a shortlist draft.</li><li>Export JSON for an explicit local backup or import into a fresh database. An existing ID collision rejects the entire import.</li></ol><p>Missing values stay unknown; zero remains zero. Measured, computed, literature and annotation are distinct. Drafts are not finalized decisions. Structures, verified numbering, mutations, molecular assembly and final decisions are not implemented yet.</p><h3>Terminology</h3><p>Humanization means engineering a non-human antibody toward a human antibody framework while evaluating effects experimentally. A humanness score has a model-specific definition; no such score is implemented or inferred here.</p>`,
  ja:`<h3>観察した内容と判断の理由を残す</h3><ol class="scope-list"><li>ローカルのFASTA、配列CSV、awx/1形式のJSONを読み込みます。保存前に取込内容と除外行を確認します。</li><li>Eで候補を選び、Wで鎖と配列を確認します。表示位置は配列先頭からの通し番号で、IMGT番号やアラインメントによる対応位置ではありません。</li><li>Rでは根拠の出典と対象を確認します。実測値は特定の試料とコンストラクトに紐づきます。</li><li>選定理由を書き、候補IDと根拠の保存内容を確認して、ショートリストの下書きを保存します。</li><li>明示的にJSONを書き出し、バックアップや空のデータベースへの再取込に利用できます。同じIDがあれば取込全体を拒否します。</li></ol><p>欠測値と0は区別します。実測、計算結果、文献、注釈も区別します。下書きは確定した意思決定ではありません。構造表示、検証済み番号付け、変異体設計、分子構成の設計、判断の確定は未実装です。</p><h3>用語について</h3><p>humanizationは「ヒト化」です。非ヒト抗体の配列をヒト抗体に近づける改変を指し、機能への影響は別途評価します。humannessは指標ごとに定義が異なるため、必要に応じて英語を併記し、ヒト抗体配列との類似性をどう評価した値かを説明します。この製品では現時点でその指標を計算していません。</p>`
};
function renderHelp() { $("#help-content").innerHTML = guides[$("#help-language").value]; }

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button || button.disabled || loading) return;
  try {
    if (button.dataset.screen) { state.screen = button.dataset.screen; render(); }
    else if (button.dataset.close) $("#" + button.dataset.close).close();
    else if (button.dataset.action === "import" || button.id === "import-button") showImport();
    else if (button.dataset.open) { state.focus = button.dataset.open; state.screen = "W"; render(); }
    else if (button.dataset.position) { state.position = Number(button.dataset.position); render(); }
    else if (button.dataset.restore) { const d = entities("decision").find((e) => e.id === button.dataset.restore); state.selected = [...d.candidate_ids]; state.focus = null; render(); }
    else if (button.id === "back-import") { pendingImport = null; $("#import-preview").hidden = true; $("#import-form").hidden = false; }
    else if (button.id === "commit-import") {
      loading = true; button.disabled = true;
      const saved = await api("/api/import", pendingImport); $("#import-dialog").close(); pendingImport = null;
      await refreshProjects(saved.project_id); notify(`Saved ${saved.imported} entities. IDs and source metadata were retained.`);
    } else if (button.id === "fixture-button" || button.id === "composition-fixture-button") {
      const example = await api(button.id === "fixture-button" ? "/api/example" : "/api/example-composition"); renderPreview({bundle:example, report:{total_rows:example.entities.length, valid_rows:example.entities.length, excluded:[], duplicates:[], warnings:[]}}, true);
    } else if (button.id === "export-button") {
      // Fetch fresh DB state, rather than exporting a stale tab snapshot.
      const fresh = await api("/api/bundle?project_id=" + encodeURIComponent(bundle.project.id));
      const url = URL.createObjectURL(new Blob([JSON.stringify(fresh, null, 2)], {type:"application/json"}));
      const a = document.createElement("a"); a.href = url; a.download = "antibody-workspace-" + bundle.project.id + ".json"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } else if (button.id === "review-shortlist") {
      const reason = $("#shortlist-reason").value.trim(); if (!reason) throw new Error("Enter a reason before reviewing the draft.");
      const ids = [...document.querySelectorAll("[data-evidence]:checked")].map((e) => e.dataset.evidence);
      pendingShortlist = {project_id:bundle.project.id, candidate_ids:[...state.selected], evidence_ids:ids, reason};
      $("#shortlist-preview").innerHTML = `<p class="muted">This saves a draft, not a finalized scientific decision.</p><p>${esc(reason)}</p><p>${state.selected.length} candidate IDs · ${ids.length} evidence records will be frozen</p><pre>${pretty(pendingShortlist)}</pre>`;
      $("#shortlist-dialog").showModal();
    } else if (button.id === "confirm-shortlist") {
      loading = true; button.disabled = true;
      const saved = await api("/api/shortlist", pendingShortlist); $("#shortlist-dialog").close();
      bundle = await api("/api/bundle?project_id=" + encodeURIComponent(bundle.project.id)); render(); notify(`Saved shortlist draft ${saved.id}. This record and its evidence snapshot are immutable.`);
    } else if (button.id === "help-button") { renderHelp(); $("#help-dialog").showModal(); }
  } catch (error) { notify(error.message, true); }
  finally { loading = false; if (button.isConnected) button.disabled = false; }
});
document.addEventListener("change", async (event) => {
  const el = event.target;
  try {
    if (el.dataset.select) { if (el.checked) state.selected.push(el.dataset.select); else state.selected = state.selected.filter((x) => x !== el.dataset.select); render(); }
    else if (el.dataset.chain) { state.chains[el.dataset.chain] = el.value; render(); }
    else if (el.dataset.jump) { const pos = Number(el.value), m = entities("molecule").find((x) => x.id === el.dataset.jump); const c = m.chains.find((x) => x.id === state.chains[m.id]) || m.chains[0]; if (!Number.isInteger(pos) || pos < 1 || pos > c.sequence.length) throw new Error("Sequence index is outside this chain."); state.position = pos; render(); }
    else if (el.id === "project-select") { await loadProject(el.value); }
    else if (el.id === "import-target") $("#new-project-fields").hidden = !!el.value;
    else if (el.id === "import-file" && el.files[0]) { const file = el.files[0]; if (file.size > 24 * 1024 * 1024) throw new Error("Maximum input file size is 24 MiB."); $("#import-text").value = await file.text(); const ext = file.name.split(".").pop().toLowerCase(); if (["json","csv"].includes(ext)) $("#import-format").value = ext; else if (["fa","fasta","faa"].includes(ext)) $("#import-format").value = "fasta"; else throw new Error("Unsupported file format; no data saved."); }
    else if (el.id === "help-language") renderHelp();
  } catch (error) { notify(error.message, true); }
});
document.addEventListener("input", (event) => {
  if (event.target.id === "candidate-search") {
    state.filter = event.target.value; const pos = event.target.selectionStart; render(); const input = $("#candidate-search"); input.focus(); if (input.type !== "search") input.setSelectionRange(pos, pos);
  }
});
$("#import-form").addEventListener("submit", async (event) => {
  event.preventDefault(); if (loading) return;
  loading = true;
  try {
    const result = await api("/api/preview", {text:$("#import-text").value, format:$("#import-format").value,
      filename:$("#import-file").files[0]?.name || "pasted-local-input", project_id:$("#import-target").value || null,
      title:$("#project-title").value, goal:$("#project-goal").value});
    renderPreview(result);
  } catch (error) { notify(error.message, true); }
  finally { loading = false; }
});
refreshProjects().catch((error) => notify(error.message, true));
