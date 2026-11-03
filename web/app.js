"use strict";

// UI state and display only; identity/provenance rules live in the Python domain.
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pretty = (value) => esc(JSON.stringify(value, null, 2));
const screenNames = {E:"Candidate Explorer", W:"Molecule Workspace", D:"Design & Compare", R:"Evidence & Decision"};
let csrf = "", projects = [], bundle = null, pendingImport = null, pendingShortlist = null;
const emptyState = () => ({screen:"E", selected:[], focus:null, chains:{}, position:null, filter:"", mapChoices:{}, chainMaps:{}, groupBy:"none", cdr3Group:"",
  structureChoices:{},structureModels:{},structureMapChoices:{},structureViews:{},structureResidues:{},residueSelection:null,linkStructureViews:false,
  observationCohort:null,observationChoices:{},observationDirection:"ascending",
  designParent:null,designMap:null,designReferenceMap:null,designLineage:null,observedStructures:{}});
let state = emptyState();
let numberingView = {maps:[]}, groupView = {candidates:[], groups:[]};
let observationView = {cohorts:[],candidates:[],ineligible:[]}, observationRequest = 0, observationLoading = false;
let loading = false;
let ready = false;
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
  const open = document.querySelector('dialog[open]');
  if (open && error) {let local=open.querySelector(':scope > .dialog-error');if(!local){local=document.createElement('p');local.className='dialog-error';local.setAttribute('role','alert');open.prepend(local);}local.textContent=message;}
}
function safeStorage(key, value) {
  try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch { /* DB persistence still works. */ }
}
function remember() {
  // Only known UI-context fields are persisted; sequence-valued option labels stay in memory.
  if (bundle) safeStorage("awx-state-" + bundle.project.id, JSON.stringify(Object.fromEntries(Object.keys(emptyState()).map((key) => [key, state[key]]))));
}
function readyControls(value) {
  ready = value;
  $("#content").inert = !value;
  $("#content").setAttribute("aria-busy",String(!value));
  document.querySelectorAll("nav [data-screen], #project-select, #import-button").forEach((el) => {el.disabled = !value;});
  $("#export-button").disabled = !value || !bundle;
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
    else if (subject.type === "construct" || subject.type === "structure") subject = records.get(subject.molecule_id);
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
function fixtureBanner() { return bundle?.project.data_class === "synthetic_fixture" ? '<div class="fixture-notice">Synthetic engineering fixture. Values are invented test data, not real experiments or model predictions.</div>' : ""; }
function emptySelection() { return '<div class="panel empty"><h2>Choose candidates to continue</h2><p class="muted">Select candidates in the Explorer. Their IDs remain selected as you move through the workspace.</p><button data-screen="E">Open Candidate Explorer</button></div>'; }
function render() {
  StructureUI.dispose();
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
  readyControls(ready);
  $("#content").innerHTML = fixtureBanner() + ({E:renderExplorer, W:renderWorkspace, D:renderDesign, R:renderEvidence}[state.screen])();
  if (state.screen === "W") StructureUI.mount();
  if (state.screen === "D") DesignUI.mount();
}

function observationControls() {
  const context=observationView.cohorts.find((c)=>c.evidence_ids.includes(state.observationCohort));
  return `<div class="panel-body observation-controls"><label class="field">Observation context<select id="observation-context" ${observationLoading?"disabled":""}><option value="">No numeric ordering</option>${observationView.cohorts.map((c)=>`<option value="${c.id}" ${context?.id===c.id?'selected':''}>${esc(c.kind)} / ${esc(c.metric)} / ${esc(c.unit)} / ${esc(JSON.stringify(c.conditions).slice(0,160))}${JSON.stringify(c.conditions).length>160?"…":""} / ${esc(c.source.name)} / ${esc(c.source.version)} / ${c.evidence_ids.length} records / ${c.id}</option>`).join('')}</select></label><label class="field">Numeric order<select id="observation-direction" ${observationLoading?"disabled":""}><option value="ascending" ${state.observationDirection==='ascending'?'selected':''}>Ascending</option><option value="descending" ${state.observationDirection==='descending'?'selected':''}>Descending</option></select></label><p class="muted">Exact recorded context only; no averaging or unit conversion. Matching metadata does not establish scientific comparability. Missing values follow numeric values in either direction.</p></div>`+
    (context?`<details class="panel-body" id="observation-context-details"><summary>Original ordering context and source</summary><pre>${pretty(context)}</pre><p class="muted">Multiple observations require an explicit choice. Material and evidence identities remain separate.</p></details>`:'')+
    (observationView.ineligible.length?`<p class="panel-body muted">${observationView.ineligible.length} records cannot establish an ordering context (unknown unit, source version, assay or conditions, or a different evidence kind). Original records remain available in R.</p>`:'');
}
function observationCell(molecule,observation) {
  if(observationLoading)return '<td class="ordering-observation" data-observation-status="updating">Updating observations…</td>';
  let html=observation?.value!=null?`${esc(observation.value)} ${esc(observation.unit)}`:esc(observation?.status || 'choose context');
  if(observation?.evidence_id) html+=`<small>Evidence ${esc(observation.evidence_id)}</small>`;
  if(observation?.options.length>1) html+=`<select data-observation-choice="${molecule.id}" aria-label="Observation for ${esc(molecule.external_id)}"><option value="">Choose observation — no average</option>${observation.options.map((o)=>`<option value="${o.id}" ${state.observationChoices[molecule.id]===o.id?'selected':''}>${o.value===null?'Value missing':esc(o.value)+' '+esc(o.unit)} / ${esc(index().get(o.subject_id)?.name)} / ${esc(o.subject_id)} / ${esc(o.timestamp)} / ${esc(o.id)}</option>`).join('')}</select>`;
  return `<td class="ordering-observation" data-observation-status="${esc(observation?.status)}">${html}</td>`;
}
function renderExplorer() {
  const molecules = entities("molecule");
  const repeated = new Map();
  for (const m of molecules) {
    const signature = JSON.stringify(m.chains.map((c) => c.sequence));
    repeated.set(signature, (repeated.get(signature) || 0) + 1);
  }
  const duplicateCount = molecules.filter((m) => repeated.get(JSON.stringify(m.chains.map((c) => c.sequence))) > 1).length;
  const groupIndex = new Map(groupView.candidates.map((row) => [row.molecule_id, row]));
  const filteredGroup = groupView.groups.find((group) => group.group_id === state.cdr3Group);
  const shown = molecules.filter((m) => (m.name + " " + m.external_id + " " + m.format).toLowerCase().includes(state.filter.toLowerCase()) &&
    (!filteredGroup || filteredGroup.candidate_ids.includes(m.id)));
  const observationIndex = new Map(observationView.candidates.map((row) => [row.molecule_id,row]));
  const observationRank = new Map(observationView.candidates.map((row,n) => [row.molecule_id,n]));
  if (state.observationCohort && !observationLoading) shown.sort((a,b) => observationRank.get(a.id)-observationRank.get(b.id));
  // Stable sorting keeps numeric order within an independently chosen CDR-H3 group.
  if (state.groupBy === "cdr3") shown.sort((a, b) => (groupIndex.get(a.id)?.cdr3_sequence || "~").localeCompare(groupIndex.get(b.id)?.cdr3_sequence || "~") || (state.observationCohort ? 0 : a.external_id.localeCompare(b.external_id)));
  const evidence = entities("evidence");
  const evidenceByMolecule = new Map();
  for (const e of evidence) {const id=subjectPath(e).find((s)=>s.type==="molecule")?.id;if(id){if(!evidenceByMolecule.has(id))evidenceByMolecule.set(id,[]);evidenceByMolecule.get(id).push(e);}}
  let html = heading("OBSERVE · COMPARE · SELECT", "Candidate Explorer", "Keep candidate identity and the evidence behind your next question in view.");
  if (!bundle) return html + `<div class="panel empty"><p class="eyebrow">START WITH YOUR RESEARCH QUESTION</p><h2>A connected place to inspect candidates</h2><p class="muted">Import sequences or a workspace bundle, inspect their identity and provenance, then save the reason behind a shortlist.</p><button data-action="import">Import local data</button><p class="subtle">FASTA · Sequence CSV · Workspace JSON</p></div>`;
  html += `<p class="candidate-summary" aria-label="Candidate counts"><strong id="candidate-count">${molecules.length}</strong> candidates · ${state.selected.length} selected · ${evidence.length} evidence records (${evidence.filter((e)=>e.kind==="measured").length} measured, ${evidence.filter((e)=>e.kind==="computed").length} computed) · ${duplicateCount} sequence repeats. IDs remain distinct.</p>`;
  html += `<div class="panel"><div class="panel-head"><h2>Research candidates <span class="subtle">${shown.length} shown</span></h2><input class="search" id="candidate-search" type="search" placeholder="Search name, external ID or format" aria-label="Search candidates" value="${esc(state.filter)}"></div>`;
  html += `<div class="panel-body observation-controls"><label class="field">Group/order<select id="group-by"><option value="none" ${state.groupBy === "none" ? "selected" : ""}>Import order</option><option value="cdr3" ${state.groupBy === "cdr3" ? "selected" : ""}>Imported heavy-chain CDR3</option></select></label><label class="field">CDR-H3 group<select id="cdr3-filter"><option value="">All groups and unavailable maps</option>${groupView.groups.map((g) => `<option value="${g.group_id}" ${state.cdr3Group === g.group_id ? "selected" : ""}>${esc(g.cdr3_sequence)} (${g.candidate_ids.length})</option>`).join("")}</select></label><p class="muted">${groupView.groups.length} complete groups. Truncated, unverified and ambiguous maps remain explicit.</p></div>`;
  html += observationControls();
  if (state.selected.length) html += `<div class="selected-strip"><span>${state.selected.length} candidate IDs held in context</span><div><button class="text-button" data-screen="W">Inspect sequences →</button> <button class="text-button" data-screen="R">Record selection →</button></div></div>`;
  html += `<div class="table-wrap"><table><thead><tr><th>Select</th><th>Candidate</th><th>Format / chains</th><th>Sequence QC</th><th>Imported CDR-H3</th><th>Ordering observation</th><th>Evidence</th></tr></thead><tbody>`;
  for (const m of shown) {
    const ev = evidenceByMolecule.get(m.id) || [];
    const repeat = repeated.get(JSON.stringify(m.chains.map((c) => c.sequence))) > 1;
    const group = groupIndex.get(m.id);
    const groupCell = group?.cdr3_sequence ? `<span class="mono">${esc(group.cdr3_sequence)}</span><small>${esc(group.options.find((o) => o.id === group.map_id)?.verification)}</small>` : `<span class="muted">${esc(group?.status || "mapping unavailable")}</span>`;
    const choice = group?.options.length > 1 ? `<select data-map-choice="${m.id}" aria-label="CDR-H3 map for ${esc(m.external_id)}"><option value="">Choose map/domain</option>${group.options.map((o) => `<option value="${o.id}" ${group.map_id === o.id ? "selected" : ""}>${esc(o.chain_id)} / ${esc(o.domain_id)} / ${o.id.slice(-8)}</option>`).join("")}</select>` : "";
    html += `<tr data-candidate-id="${m.id}" class="${state.selected.includes(m.id) ? "selected" : ""}"><td><input type="checkbox" data-select="${m.id}" aria-label="Select ${esc(m.external_id)}" ${state.selected.includes(m.id) ? "checked" : ""}></td><td><button class="name-button" data-open="${m.id}">${esc(m.name)}</button><small>${esc(m.external_id)}</small></td><td>${esc(m.format)}<small>${m.chains.length} chain${m.chains.length === 1 ? "" : "s"} · ${m.chains.reduce((n, c) => n + c.sequence.length, 0)} aa</small></td><td><span class="tag ${repeat ? "warning" : ""}">${repeat ? "Sequence repeat" : "Imported sequence"}</span><small>${numberingView.maps.some((map) => map.molecule_id === m.id) ? "Imported map — inspect status" : "Numbering not registered"}</small></td><td>${groupCell}${choice}</td>${observationCell(m,observationIndex.get(m.id))}<td>${ev.length ? `${ev.length} record${ev.length === 1 ? "" : "s"}<small>Traceable to subject IDs</small>` : '<span class="muted">Not measured / not predicted</span>'}</td></tr>`;
  }
  return html + '</tbody></table></div><div class="panel-body subtle">Sequence repeats do not establish molecular identity. CDR groups use complete source-bearing imported maps. Observation choices retain their original subject and source IDs.</div></div>';
}

function renderWorkspace() {
  let html = heading("FOLLOW THE MOLECULE", "Molecule Workspace", "Inspect chain identity and sequence positions without inventing biological correspondence.");
  const selected = selectedMolecules();
  const focus = entities("molecule").find((m) => m.id === state.focus);
  const molecules = focus ? [focus, ...selected.filter((m) => m.id !== focus.id)] : selected;
  if (!molecules.length) return html + emptySelection();
  html += '<p class="muted">Raw sequence indexes are 1-based and unaligned. Imported antibody and structural coordinates retain separate chain/domain/model identities. Shared camera orientation is not structural superposition.</p>';
  if (molecules.length > 2) html += `<p class="muted">Showing the first 2 of ${molecules.length} candidates in context. The full selection is retained.</p>`;
  const displayed = molecules.slice(0, 2);
  const chains = displayed.map((m) => m.chains.find((c) => c.id === state.chains[m.id]) || m.chains[0]);
  html += '<div class="two-columns">';
  for (let n = 0; n < displayed.length; n++) {
    const m = displayed[n], chain = chains[n], other = chains[1 - n];
    const maps = numberingView.maps.filter((map) => map.molecule_id === m.id && map.chain_id === chain.id);
    const mapKey = m.id + "|" + chain.id;
    const map = maps.find((item) => item.id === state.chainMaps[mapKey]) || (maps.length === 1 ? maps[0] : null);
    const positions = new Map((map?.entries || []).map((entry) => [entry.sequence_index, entry]));
    html += `<div class="panel"><div class="panel-head"><div><h2>${esc(m.name)}</h2><p class="subtle">${esc(m.external_id)}</p></div><span class="tag">${esc(m.format)}</span></div><div class="panel-body"><p class="mono">Molecule: ${m.id}</p><label class="field">Chain<select data-chain="${m.id}" aria-label="Chain for ${esc(m.external_id)}">${m.chains.map((c) => `<option value="${esc(c.id)}" ${c.id === chain.id ? "selected" : ""}>${esc(c.id)} / ${esc(c.role)} / ${c.sequence.length} aa</option>`).join("")}</select></label>`;
    html += maps.length ? `<label class="field">Imported numbering map / domain<select data-chain-map="${esc(mapKey)}" aria-label="Numbering map for ${esc(m.external_id)} ${esc(chain.id)}"><option value="">${maps.length > 1 ? "Choose map/domain — no implicit match" : "Inspect imported map"}</option>${maps.map((item) => `<option value="${item.id}" ${map?.id === item.id ? "selected" : ""}>${esc(item.scheme)} / ${esc(item.domain_id)} / ${esc(item.status)} / ${esc(item.verification.status)}</option>`).join("")}</select></label>` : '<p class="muted">Numbering: mapping unavailable (no imported map).</p>';
    if (map) html += `<p class="muted">${esc(map.scheme)} / ${esc(map.domain_id)}: <strong>${esc(map.status)}</strong> · ${esc(map.verification.status)}${map.reason ? " / " + esc(map.reason) : ""}<br>${map.eligible ? (map.verification.status === "engineering_fixture" ? "Synthetic engineering annotation; human scientific validation pending." : "Source verification is a recorded external attestation; the application does not assign numbering.") : "Not eligible for source-verified numbering actions."}<br>CDR3: ${map.cdr3_complete ? esc(map.cdr3_sequence) : "partial / unavailable"}</p><details><summary>Numbering source, definition and verification</summary><p>${esc(map.source.name)} / ${esc(map.source.version || "version unknown")}</p><pre>${pretty(map.verification)}</pre><p class="muted">${esc(map.region_source)}</p></details>`;
    html += '<div class="sequence">';
    // Long chains stay inspectable without rendering hundreds of thousands of buttons.
    const start = state.position && state.position > 200 ? Math.floor((state.position - 1) / 200) * 200 : 0;
    for (let i = start; i < Math.min(start + 200, chain.sequence.length); i++) {
      const difference = other && (other.sequence[i] ?? "absent") !== chain.sequence[i];
      const annotation = positions.get(i + 1);
      html += `<button class="residue ${difference ? "diff" : ""} ${state.position === i + 1 ? "active" : ""} ${annotation?.region.startsWith("CDR") ? "cdr-residue" : ""}" data-position="${i + 1}" data-position-molecule="${m.id}" data-position-chain="${esc(chain.id)}" aria-label="${esc(m.external_id)} ${esc(chain.id)} sequence index ${i + 1} ${chain.sequence[i]}" title="${annotation ? esc(`${map.scheme} ${annotation.coordinate} / ${annotation.region} / ${map.domain_id}`) : "No imported antibody coordinate"}"><small>${i + 1}</small>${chain.sequence[i]}${annotation ? `<small>${esc(annotation.coordinate)}</small>` : ""}</button>`;
    }
    const current = positions.get(state.position);
    html += `</div><label class="field">Jump to sequence index<input type="number" data-jump="${m.id}" min="1" max="${chain.sequence.length}" value="${state.position || 1}"></label><p class="sequence-details">${state.position ? `Selected raw index ${state.position}: ${esc(chain.sequence[state.position - 1] || "absent in this chain")} · ${current ? esc(`${map.scheme} ${current.coordinate} / ${current.region} / ${map.domain_id}`) : "numbering mapping unavailable for this index"}` : "Choose a sequence index to compare. Gold marks raw position differences."}</p><details><summary>Sequence source and raw record</summary><p>${esc(m.source.name)} / ${esc(m.source.version || "version unknown")}</p><pre>${pretty(m)}</pre></details>`;
    html += StructureUI.panel(m);
    html += renderComposition(m);
    const constructs = entities("construct").filter((c) => c.molecule_id === m.id);
    html += '<p class="section-label">CONSTRUCTS & MATERIALS</p>';
    html += constructs.length ? constructs.map((c) => `<details><summary>${esc(c.name)} (${c.id})</summary><pre>${pretty(c)}</pre><p class="muted">CDS translation and signal-peptide processing are not validated.</p>${entities("material").filter((s) => s.construct_id === c.id).map((s) => `<p class="muted">${esc(s.name)} / lot ${esc(s.lot)}<br><span class="mono">${s.id}</span></p>`).join("")}</details>`).join("") : '<p class="muted">No construct or material registered.</p>';
    html += '</div></div>';
  }
  return html + '</div><button data-design-selected>Design a substitution at the selected residue</button> <button data-screen="R">Follow evidence and record a question →</button>';
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
    DesignUI.panel()+DesignUI.hypothesesPanel();
}

function renderEvidence() {
  let html = heading("RETAIN THE REASONING", "Evidence & Decision", "Separate observations from calculations, and keep the subject and source attached.");
  if (!state.selected.length) return html + emptySelection();
  html += '<p><button data-open-hypothesis>Record research hypothesis</button></p>';
  const evidence = selectedEvidence();
  html += `<div class="two-columns"><div><div class="panel"><div class="panel-head"><h2>Evidence for ${state.selected.length} selected candidates</h2><span class="subtle">${evidence.length} records</span></div>`;
  if (!evidence.length) html += '<div class="panel-body"><p class="muted">Not measured / not predicted. No evidence records were registered for this selection.</p></div>';
  for (const e of evidence) {
    const path = subjectPath(e);
    html += `<article class="evidence-row"><div class="metric"><div><span class="tag ${esc(e.kind)}">${esc(e.kind)}</span><p>${esc(e.metric)}</p></div><div class="value">${e.value === null ? '<span class="muted">Value missing</span>' : esc(e.value) + ' <span class="muted">' + esc(e.unit) + '</span>'}</div></div><p class="muted">${path.map((p) => `${esc(p.type)}: ${esc(p.name)}`).join(" → ")}</p><p>Source: ${esc(e.source.name)} / ${esc(e.source.version || "version unknown")}<br>Event time: ${esc(e.timestamp)}</p><p>${e.conditions === null ? '<span class="tag warning">Conditions unknown — do not pool</span>' : 'Conditions: ' + esc(JSON.stringify(e.conditions))}</p>${["iptm","ptm"].includes(e.metric.toLowerCase()) ? '<p class="muted">Model-internal metric; not measured binding affinity. Model scope is declared in the source conditions or remains unspecified.</p>' : ""}${e.kind === "computed" ? '<p class="muted">Computed result. Interpretation and uncertainty depend on the source; this is not an experimental measurement.</p>' : ""}<details><summary>Original record, subject IDs & provenance</summary><pre>${pretty(e)}</pre>${path.map((p) => `<p class="mono">${esc(p.type)}: ${p.id}</p>`).join("")}</details><label class="evidence-check"><input type="checkbox" data-evidence="${e.id}" checked> Include in draft snapshot</label></article>`;
  }
  html += '</div></div><div><div class="panel"><div class="panel-head"><h2>Save a shortlist draft</h2><span class="tag">Draft only</span></div><div class="panel-body"><p class="muted">Record why these candidates deserve further investigation. Final decisions with criteria, weights and missing-data gates are scheduled for M4.</p><p class="section-label">CANDIDATES IN CONTEXT</p>';
  html += selectedMolecules().map((m) => `<p class="wrap">${esc(m.external_id)} — ${esc(m.name)}<br><span class="mono">${m.id}</span></p>`).join("");
  html += '<label class="field">Reason and next research question<textarea id="shortlist-reason" rows="5" placeholder="What did you observe? Why keep this selection? What remains unverified?"></textarea></label><button id="review-shortlist">Review before saving</button></div></div>';
  const decisions = entities("decision").filter((d) => d.candidate_ids.some((id) => state.selected.includes(id)));
  html += `<div class="panel"><div class="panel-head"><h2>Saved shortlist drafts</h2><span class="subtle">${decisions.length} records</span></div>`;
  if (!decisions.length) html += '<p class="panel-body muted">No saved draft for this selection.</p>';
  for (const d of decisions.toReversed()) html += `<article class="saved-draft"><span class="tag">Draft · immutable record</span><p>${esc(d.reason)}</p><p class="muted">${d.candidate_ids.length} candidate IDs · ${d.evidence_snapshot.length} evidence snapshots<br>${esc(d.timestamp)}</p><button class="text-button" data-restore="${d.id}">Restore this selection</button><details><summary>Saved IDs and frozen evidence</summary><pre>${pretty(d)}</pre></details></article>`;
  return html + '</div></div></div><p class="muted">Measurements are not averaged or ranked across different units or conditions. Missing values remain unknown.</p>'+DesignUI.hypothesesPanel();
}

async function loadProject(id) {
  DesignUI.invalidate();
  StructureUI.dispose();
  remember();
  readyControls(false);
  bundle = await api("/api/bundle?project_id=" + encodeURIComponent(id));
  let saved;
  try { saved = JSON.parse(safeStorage("awx-state-" + id) || "null"); } catch { saved = null; }
  state = emptyState();
  if (saved && Array.isArray(saved.selected)) {
    const ids = new Set(entities("molecule").map((m) => m.id));
    const knownSaved = Object.fromEntries(Object.keys(emptyState()).filter((key) => Object.hasOwn(saved,key)).map((key) => [key,saved[key]]));
    state = {...state, ...knownSaved, screen:screenNames[saved.screen] ? saved.screen : "E", selected:saved.selected.filter((x) => ids.has(x))};
    if (state.selected.length !== saved.selected.length) notify("Some saved candidate IDs are unavailable; selection was not replaced with another candidate.", true);
  }
  await refreshNumbering();
  safeStorage("awx-project", id); $("#project-select").value = id; readyControls(true); render();
}
async function refreshNumbering() {
  if (!bundle) { numberingView = {maps:[]}; groupView = {candidates:[],groups:[]}; return; }
  numberingView = await api("/api/numbering?project_id=" + encodeURIComponent(bundle.project.id));
  const ids = new Set(numberingView.maps.map((item) => item.id));
  for (const key of Object.keys(state.mapChoices)) if (!ids.has(state.mapChoices[key])) {delete state.mapChoices[key];notify("A saved numbering-map choice is unavailable. Choose a map explicitly.",true);}
  groupView = await api("/api/cdr3-groups", {project_id:bundle.project.id, map_choices:state.mapChoices});
  if (state.cdr3Group && !groupView.groups.some((g) => g.group_id === state.cdr3Group)) {
    state.cdr3Group = ""; notify("The saved CDR-H3 group is unavailable. The group filter was cleared; candidate selection was retained.");
  }
  await refreshObservations();
}
async function refreshObservations() {
  const request=++observationRequest;
  if(!bundle){observationView={cohorts:[],candidates:[],ineligible:[]};observationLoading=false;return;}
  const data={project_id:bundle.project.id,cohort_id:state.observationCohort,choices:state.observationChoices,direction:state.observationDirection};
  const current=()=>request===observationRequest && bundle?.project.id===data.project_id;
  observationLoading=true;
  if(ready && state.screen==='E')render();
  try {const result=await api('/api/observation-order',data);if(current())observationView=result;}
  catch(error){
    if(!current())return;
    // Never silently substitute the first observation for an unavailable choice.
    state.observationCohort=null;state.observationChoices={};state.observationDirection='ascending';
    const fallback=await api('/api/observation-order',{project_id:data.project_id,cohort_id:null,choices:{},direction:'ascending'});
    if(!current())return;
    observationView=fallback;
    notify(error.message+' Numeric ordering was cleared; candidate selection was retained. Choose context and observations explicitly.',true);
  }
  finally{if(current())observationLoading=false;}
}
async function refreshProjects(preferred) {
  const boot = await api("/api/bootstrap"); csrf = boot.csrf; projects = boot.projects;
  $("#project-select").innerHTML = projects.length ? projects.map((p) => `<option value="${p.id}">${esc(p.title)}</option>`).join("") : '<option value="">No project yet</option>';
  $("#import-target").innerHTML = '<option value="">New project</option>' + projects.map((p) => `<option value="${p.id}">${esc(p.title)}</option>`).join("");
  const id = projects.find((p) => p.id === preferred)?.id || projects.find((p) => p.id === safeStorage("awx-project"))?.id || projects[0]?.id;
  if (id) await loadProject(id); else {readyControls(true);render();}
}
function showImport() {
  pendingImport = null; $("#import-preview").hidden = true; $("#import-form").hidden = false;
  $("#import-target").value = bundle?.project.id || ""; $("#new-project-fields").hidden = !!bundle;
  $("#import-dialog").showModal();
  updateStructureImport();
}
async function updateStructureImport() {
  const coordinate = ["pdb","mmcif"].includes($("#import-format").value);
  $("#structure-import-options").hidden = !coordinate;
  if (!coordinate) return;
  const target=$("#import-target").value;
  let incoming=target===bundle?.project.id?entities("molecule"):[];
  if (target && target!==bundle?.project.id) {try {incoming=(await api('/api/bundle?project_id='+encodeURIComponent(target))).entities.filter((e)=>e.type==='molecule');} catch(error){notify(error.message,true);}}
  if ($("#import-target").value!==target) return;
  $("#structure-molecule").innerHTML = '<option value="">Choose an explicitly registered molecule</option>' + incoming.map((m)=>`<option value="${m.id}">${esc(m.external_id)} / ${esc(m.name)}</option>`).join("");
}
function renderPreview(result, synthetic = false) {
  pendingImport = result.bundle;
  const r = result.report;
  $("#import-form").hidden = true; const target = $("#import-preview"); target.hidden = false;
  const samples = pendingImport.entities.filter((e) => e.type === "molecule").slice(0, 5);
  target.innerHTML = `<h2>Review before saving</h2>${synthetic ? '<p class="fixture-notice">Synthetic fixture. These are invented engineering values, not real scientific results.</p>' : ""}<p class="muted">Project: ${esc(pendingImport.project.title)}</p><div class="preview-summary">${r.total_rows} input rows · ${r.valid_rows} valid · ${r.excluded.length} excluded · ${r.duplicates.length} sequence-repeat warnings</div><p class="muted">${pendingImport.entities.length} entities will be added. Existing records are never overwritten. IDs and references are revalidated at save time.</p>${r.excluded.length ? `<h3>Excluded records (not saved)</h3><pre class="preview-list">${pretty(r.excluded)}</pre>` : ""}${r.duplicates.length || r.warnings.length ? `<details><summary>QC warnings</summary><pre class="preview-list">${pretty([...r.duplicates, ...r.warnings])}</pre></details>` : ""}<h3>Sample of incoming candidates</h3><ul class="muted">${samples.map((m) => `<li>${esc(m.external_id)} / ${esc(m.name)} / ${esc(m.format)}</li>`).join("")}</ul><details><summary>Incoming records and source metadata</summary><pre class="preview-list">${pretty(pendingImport.entities.slice(0, 8))}</pre></details><div class="dialog-actions"><button class="secondary" id="back-import">Back</button><button id="commit-import" ${pendingImport.entities.length ? "" : "disabled"}>Save ${r.valid_rows} valid rows${r.excluded.length ? " (excluded rows omitted)" : ""}</button></div>`;
}

const guides = {
  en:`<h3>Observe, then retain the reasoning</h3><ol class="scope-list"><li>Import a local FASTA, sequence CSV or awx/1 JSON. Inspect the preview and excluded rows before saving.</li><li>Select candidates in E. Open W to inspect chains and compare raw sequence indexes. These are not IMGT positions or an alignment.</li><li>In R, follow each evidence record to its source and subject. Measured values belong to a particular material and construct.</li><li>Write a reason, review the candidate IDs and evidence snapshot, and save a shortlist draft.</li><li>Export JSON for an explicit local backup or import into a fresh database. An existing ID collision rejects the entire import.</li></ol><p>Missing values stay unknown; zero remains zero. Measured, computed, literature and annotation are distinct. Drafts are not finalized decisions. Imported numbering maps, CDR-H3 groups and local PDB/mmCIF observation with explicit correspondence are supported. D can create an explicit source-numbered substitution design and a proposed research hypothesis. Select a residue in W, choose Design a substitution, inspect a reference if supplied, then review the new child and exact lineage. Child numbering, structures and measurements are not inherited. In R, save the proposed hypothesis, original evidence, limitations and next experiment. Automatic numbering, interactive assembly and final decisions remain pending. Camera linking shares orientation and zoom; it does not superpose structures. B-values are not automatically treated as confidence.</p><h3>Contextual numeric ordering</h3><p>In E, choose an observation context and numeric direction. Units, assay conditions, evidence kind and source/version remain separate. Matching metadata does not prove scientific comparability. If several observations exist, choose the actual material/evidence record explicitly. No averaging, unit conversion or missing-value replacement is performed. The original records remain available in R.</p><h3>Terminology</h3><p>Humanization means engineering a non-human antibody toward a human antibody framework while evaluating effects experimentally. A humanness score has a model-specific definition; no such score is implemented or inferred here.</p>`,
  ja:`<h3>観察した内容と判断の理由を残す</h3><ol class="scope-list"><li>ローカルのFASTA、配列CSV、awx/1形式のJSONを読み込みます。保存前に取込内容と除外行を確認します。</li><li>Eで候補を選び、Wで鎖と配列を確認します。表示位置は配列先頭からの通し番号で、IMGT番号やアラインメントによる対応位置ではありません。</li><li>Rでは根拠の出典と対象を確認します。実測値は特定の試料とコンストラクトに紐づきます。</li><li>選定理由を書き、候補IDと根拠の保存内容を確認して、ショートリストの下書きを保存します。</li><li>明示的にJSONを書き出し、バックアップや空のデータベースへの再取込に利用できます。同じIDがあれば取込全体を拒否します。</li></ol><p>欠測値と0は区別します。実測、計算結果、文献、注釈も区別します。下書きは確定した意思決定ではありません。出典を持つ番号対応表の取込、CDR-H3群分け、ローカルのPDB/mmCIF表示に対応しています。構造ファイル中の鎖ID、残基番号、挿入コードと配列位置を明示的に対応付けます。視点の同期は構造の重ね合わせではありません。B値を予測信頼度と自動的に同一視しません。Wで残基を選び、Design a substitutionからDへ進むと、出典を持つ番号対応表を使って置換を指定できます。比較配列があれば対応位置を確認し、新しい子候補と変更記録を保存前に確認します。子の番号付け、構造、実測値は親から引き継ぎません。Rでは未検証の仮説、原根拠、限界、次の実験を別の記録として保存します。番号付けの自動実行、対話的な組立、判断の確定は未実装です。</p><h3>条件を区別した値の並べ替え</h3><p>EでObservation contextと並び順を選びます。単位、測定条件、実測と計算、出典と版を区別します。記録された条件が一致しても、科学的に比較可能であることを保証しません。複数の結果がある場合は、使用する試料と根拠の記録を明示的に選びます。平均、単位換算、欠測値の補完は行いません。原記録はRで確認できます。</p><h3>用語について</h3><p>humanizationは「ヒト化」です。非ヒト抗体の配列をヒト抗体に近づける改変を指し、機能への影響は別途評価します。humanness（ヒト抗体らしさ）は指標ごとに定義が異なるため、必要に応じて英語を併記し、ヒト抗体配列との類似性をどう評価した値かを説明します。この製品では現時点でその指標を計算していません。</p>`
};
function renderHelp() {
  const language=$("#help-language").value;
  $("#help-content").lang=language;
  $("#help-content").innerHTML=guides[language];
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button || button.disabled || loading) return;
  try {
    if (button.dataset.screen) { state.screen = button.dataset.screen; render(); }
    else if (button.dataset.close) $("#" + button.dataset.close).close();
    else if (button.dataset.action === "import" || button.id === "import-button") showImport();
    else if (button.dataset.open) { state.focus = button.dataset.open; state.screen = "W"; render(); }
    else if (button.dataset.position) { state.position = Number(button.dataset.position); state.focus=button.dataset.positionMolecule; state.residueSelection={molecule_id:button.dataset.positionMolecule,chain_id:button.dataset.positionChain,sequence_index:state.position}; render(); }
    else if (button.dataset.designSelected!==undefined) DesignUI.fromSelection();
    else if (button.dataset.restore) { const d = entities("decision").find((e) => e.id === button.dataset.restore); state.selected = [...d.candidate_ids]; state.focus = null; render(); }
    else if (button.id === "back-import") { pendingImport = null; $("#import-preview").hidden = true; $("#import-form").hidden = false; }
    else if (button.id === "commit-import") {
      loading = true; button.disabled = true;
      const saved = await api("/api/import", pendingImport); $("#import-dialog").close(); pendingImport = null;
      await refreshProjects(saved.project_id); notify(`Saved ${saved.imported} entities. IDs and source metadata were retained.`);
    } else if (["fixture-button", "composition-fixture-button", "numbering-fixture-button", "structure-fixture-button"].includes(button.id)) {
      const route = {"fixture-button":"/api/example", "composition-fixture-button":"/api/example-composition", "numbering-fixture-button":"/api/example-numbering", "structure-fixture-button":"/api/example-structures"}[button.id];
      const example = await api(route); renderPreview({bundle:example, report:{total_rows:example.entities.length, valid_rows:example.entities.length, excluded:[], duplicates:[], warnings:[]}}, true);
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
      bundle = await api("/api/bundle?project_id=" + encodeURIComponent(bundle.project.id)); await refreshNumbering(); render(); notify(`Saved shortlist draft ${saved.id}. This record and its evidence snapshot are immutable.`);
    } else if (button.id === "help-button") { renderHelp(); $("#help-dialog").showModal(); }
  } catch (error) { notify(error.message, true); }
  finally { loading = false; if (button.isConnected) button.disabled = false; }
});
document.addEventListener("change", async (event) => {
  const el = event.target;
  try {
    if (el.dataset.select) { if (el.checked) state.selected.push(el.dataset.select); else state.selected = state.selected.filter((x) => x !== el.dataset.select); render(); }
    else if (el.dataset.chain) { state.chains[el.dataset.chain] = el.value; if(state.residueSelection?.molecule_id===el.dataset.chain&&state.residueSelection.chain_id!==el.value)state.residueSelection=null; render(); }
    else if (el.dataset.chainMap) { if (el.value) state.chainMaps[el.dataset.chainMap] = el.value; else delete state.chainMaps[el.dataset.chainMap]; render(); }
    else if (el.dataset.mapChoice) { if (el.value) state.mapChoices[el.dataset.mapChoice] = el.value; else delete state.mapChoices[el.dataset.mapChoice]; await refreshNumbering(); render(); }
    else if (el.id === "group-by") {state.groupBy = el.value;render();}
    else if (el.id === "cdr3-filter") {state.cdr3Group = el.value;render();}
    else if (el.id === "observation-context") {state.observationCohort=el.value||null;state.observationChoices={};await refreshObservations();render();}
    else if (el.id === "observation-direction") {state.observationDirection=el.value;await refreshObservations();render();}
    else if (el.dataset.observationChoice) {if(el.value)state.observationChoices[el.dataset.observationChoice]=el.value;else delete state.observationChoices[el.dataset.observationChoice];await refreshObservations();render();}
    else if (el.dataset.jump) { const pos = Number(el.value), m = entities("molecule").find((x) => x.id === el.dataset.jump); const c = m.chains.find((x) => x.id === state.chains[m.id]) || m.chains[0]; if (!Number.isInteger(pos) || pos < 1 || pos > c.sequence.length) throw new Error("Sequence index is outside this chain."); state.position = pos; render(); }
    else if (el.id === "project-select") { await loadProject(el.value); }
    else if (el.id === "import-target") {$("#new-project-fields").hidden = !!el.value;updateStructureImport();}
    else if (el.id === "import-format") updateStructureImport();
    else if (el.id === "import-file" && el.files[0]) { const file = el.files[0]; if (file.size > 24 * 1024 * 1024) throw new Error("Maximum input file size is 24 MiB."); $("#import-text").value = await file.text(); const ext = file.name.split(".").pop().toLowerCase(); if (["json","csv","pdb"].includes(ext)) $("#import-format").value = ext; else if (["cif","mmcif"].includes(ext)) $("#import-format").value="mmcif"; else if (["fa","fasta","faa"].includes(ext)) $("#import-format").value = "fasta"; else throw new Error("Unsupported file format; no data saved.");updateStructureImport(); }
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
    const request = {text:$("#import-text").value, format:$("#import-format").value,
      filename:$("#import-file").files[0]?.name || "pasted-local-input", project_id:$("#import-target").value || null,
      title:$("#project-title").value, goal:$("#project-goal").value,data_class:$("#project-data-class").value};
    if (["pdb","mmcif"].includes(request.format)) request.structure_options={molecule_id:$("#structure-molecule").value,origin_kind:$("#structure-origin").value,
      source_name:$("#structure-source").value,source_version:$("#structure-source-version").value || null};
    const result = await api("/api/preview", request);
    renderPreview(result);
  } catch (error) { notify(error.message, true); }
  finally { loading = false; }
});
StructureUI.configure({api,bundle:()=>bundle,state:()=>state,remember,notify,render,
  focusSequence(selection){state.residueSelection=selection;state.focus=selection.molecule_id;state.chains[selection.molecule_id]=selection.chain_id;state.position=selection.sequence_index;render();},
  async reload(){
    readyControls(false);StructureUI.dispose();
    try{bundle=await api('/api/bundle?project_id='+encodeURIComponent(bundle.project.id));await refreshNumbering();}
    finally{readyControls(true);render();}
  }
});
DesignUI.configure({api,bundle:()=>bundle,state:()=>state,maps:()=>numberingView.maps,esc,pretty,subjectPath,notify,render,
  async reload(){readyControls(false);StructureUI.dispose();try{bundle=await api('/api/bundle?project_id='+encodeURIComponent(bundle.project.id));await refreshNumbering();}finally{readyControls(true);render();}}
});
refreshProjects().catch((error) => notify(error.message, true));
