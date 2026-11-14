"use strict";

// UI state and display only; identity/provenance rules live in the Python domain.
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pretty = (value) => esc(JSON.stringify(value, null, 2));
const screenNames = {E:"Candidate Explorer", W:"Molecule Workspace", D:"Design & Compare", R:"Evidence & Decision"};
let csrf = "", projects = [], bundle = null, pendingImport = null, pendingShortlist = null;
let importEpoch=0, mappingDraft=null, importSourceText=null, importFileRead=null;
let sequenceGrouping=null;
// Scientific draft text stays in this tab's memory, never browser storage.
const shortlistDrafts = new Map();
let pendingShortlistScope = null;
function shortlistScope() {return JSON.stringify([bundle?.project.id,[...new Set(state.selected)].sort()]);}
function shortlistDraft() {
  const key=shortlistScope();
  if(!shortlistDrafts.has(key))shortlistDrafts.set(key,{reason:'',evidenceIds:new Set(selectedEvidence().map((e)=>e.id)),version:0});
  return shortlistDrafts.get(key);
}
function invalidateShortlistPreview() {pendingShortlist=null;pendingShortlistScope=null;}
const emptyState = () => ({screen:"E", selected:[], focus:null, chains:{}, position:null, filter:"", mapChoices:{}, chainMaps:{}, groupBy:"none", cdr3Group:"",
  structureChoices:{},structureModels:{},structureMapChoices:{},structureViews:{},structureResidues:{},structureModes:{},residueSelection:null,linkStructureViews:false,
  observationCohort:null,observationChoices:{},observationDirection:"ascending",
  designParent:null,designMap:null,designReferenceMap:null,designLineage:null,observedStructures:{},selectedUnits:[],compositionOpen:false,
  compositionParent:null,compositionCurrent:null,compositionCompareLeft:'',compositionCompareRight:'',designTask:'substitution',
  expressionMolecule:null,expressionLeft:null,expressionRight:null,expressionCohort:null,expressionMaterial:null,
  researchTask:'evidence',decisionBase:null,decisionEditorOpen:true,comparisonContext:null,comparisonRegion:null});
let state = emptyState();
let numberingView = {maps:[]}, groupView = {candidates:[], groups:[]};
let observationView = {cohorts:[],candidates:[],ineligible:[]}, observationRequest = 0, observationLoading = false;
let loading = false;
let ready = false;
let indexedBundle = null, indexedEntities = null;
const approvedBundleJson = new WeakMap();
const isBundle = (value) => value?.schema_version === 'awx/1' && Array.isArray(value.entities) && !!value.project;
function retainBundleJson(value, raw) {
  const clientJson=JSON.stringify(value);
  if(JSON.stringify(JSON.parse(raw))!==clientJson)throw Error('Preview serialization differs from its records. Review the source again; no data saved.');
  approvedBundleJson.set(value,{raw,clientJson});
}
function exactBundleJson(value) {
  const snapshot=approvedBundleJson.get(value);
  if(!snapshot)return JSON.stringify(value);
  if(snapshot.clientJson!==JSON.stringify(value))throw Error('Reviewed records changed. Request a new preview before saving; no data saved.');
  return snapshot.raw;
}

async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method:"POST", headers:{"Content-Type":"application/json", "X-CSRF-Token":csrf}, body:path==='/api/import'?exactBundleJson(data):JSON.stringify(data)
  });
  const raw=await response.text(),result=JSON.parse(raw);
  if (!response.ok) throw new Error([result.error, ...(result.details || [])].join("\n"));
  if(isBundle(result))retainBundleJson(result,raw);
  if(isBundle(result.bundle)&&typeof result.serialized_bundle==='string')retainBundleJson(result.bundle,result.serialized_bundle);
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
function reportedPositions(e) {
  const molecule=subjectPath(e).find((s)=>s.type==='molecule');
  return (e.residue_refs||[]).map((r)=>`<button class="text-button" data-reported-evidence="${e.id}" data-reported-chain="${esc(r.chain_id)}" data-reported-index="${r.sequence_index}">Source-reported position: ${esc(molecule?.external_id)} / ${esc(r.chain_id)} / raw ${r.sequence_index}</button>`).join(' ');
}
function reportedEvidence(molecule) {
  const records=entities('evidence').filter((e)=>e.residue_refs?.length&&subjectPath(e).some((p)=>p.id===molecule.id));
  if(!records.length)return '';
  return `<section class="reported-evidence"><h3>Source-reported positions</h3><p class="muted">Position associations supplied by the source. They do not localize a whole-material measurement or establish a liability.</p>${records.map((e)=>`<article><span class="tag ${esc(e.kind)}">${esc(e.kind)}</span> ${esc(e.metric)}${e.description?`<p>${esc(e.description)}</p>`:''}<p class="muted">${esc(e.source.name)} / ${esc(e.source.version||'version unknown')}</p>${reportedPositions(e)}${PredictionUI.origin(e)} <button class="text-button" data-source-evidence="${e.id}">Open source evidence in R</button></article>`).join('')}</section>`;
}
function heading(label, title, description) {
  return `<div class="page-heading"><div><p class="eyebrow">${label}</p><h1>${title}</h1><p class="muted">${description}</p></div><span class="project-chip">${esc(bundle?.project.title || "No active project")}</span></div>`;
}
function fixtureBanner() { return bundle?.project.data_class === "synthetic_fixture" ? '<div class="fixture-notice">Synthetic engineering fixture. Values are invented test data, not real experiments or model predictions.</div>' + (state.screen !== 'R' && bundle.project.title.startsWith('[SYNTHETIC EXAMPLE]')?'<div class="panel panel-body"><h2>Which candidate should we investigate next?</h2><p>Compare the declared H/L chains, inspect the original materials and assay conditions, then save your reason and next experiment. One thermal value is missing; the alternate material was measured under a different condition.</p><button data-screen="W">Compare paired candidates</button> <button class="secondary" data-screen="R">Inspect evidence and retain reasoning</button></div>':'') : ""; }
function emptySelection() { return '<div class="panel empty"><h2>Choose candidates to continue</h2><p class="muted">Select candidates in the Explorer. Their IDs remain selected as you move through the workspace.</p><button data-screen="E">Open Candidate Explorer</button></div>'; }
function render() {
  const sequenceViewports = new Map([...document.querySelectorAll('[data-sequence-viewport]')]
    .map((element) => [element.dataset.sequenceViewport, element.scrollTop]));
  StructureUI.dispose();
  remember();
  document.querySelectorAll("nav [data-screen]").forEach((b) => { b.classList.toggle("active", b.dataset.screen === state.screen); b.setAttribute("aria-current", b.dataset.screen === state.screen ? "page" : "false"); });
  $("#selection-count").textContent = `${state.selected.length} selected`;
  $("#breadcrumb").textContent = `${bundle?.project.title || "Project"} / ${screenNames[state.screen]}`;
  const workspace = state.screen === "W" ? workspaceMolecules() : null;
  if (workspace) {
    const selection = state.residueSelection;
    const active = workspace.slice(0, 2).find((molecule) => molecule.id === selection?.molecule_id) || workspace[0];
    if (active) {
      const chain = active.chains.find((c) => c.id === state.chains[active.id]) || active.chains[0];
      const index = selection?.molecule_id === active.id && selection.chain_id === chain.id ? selection.sequence_index : null;
      $("#breadcrumb").textContent += ` / ${active.external_id} / ${chain.id}${index ? " / index " + index : ""}`;
    }
  }
  readyControls(ready);
  const markup = workspace ? renderWorkspace(workspace) : ({E:renderExplorer, D:renderDesign, R:renderEvidence}[state.screen])();
  $("#content").innerHTML = fixtureBanner() + markup;
  if (state.screen === "W") {
    for (const element of document.querySelectorAll('[data-sequence-viewport]')) {
      element.scrollTop = sequenceViewports.get(element.dataset.sequenceViewport) || 0;
      const selected = element.querySelector('[aria-pressed="true"]');
      if (selected) {
        const bounds = element.getBoundingClientRect();
        const residue = selected.getBoundingClientRect();
        if (residue.top < bounds.top) element.scrollTop += residue.top - bounds.top;
        if (residue.bottom > bounds.bottom) element.scrollTop += residue.bottom - bounds.bottom;
      }
    }
    StructureUI.mount();
  }
  if (state.screen === "D") {if(state.designTask==='composition')CompositionUI.mount();else if(state.designTask==='expression')ExperimentUI.mount();else DesignUI.mount();}
  if (state.screen === "R") {if(state.researchTask==='decision')DecisionUI.mount();else ExperimentUI.mount();}
}

function observationControls() {
  const context=observationView.cohorts.find((c)=>c.evidence_ids.includes(state.observationCohort));
  return `<div class="panel-body observation-controls"><label class="field">Observation context<select id="observation-context" ${observationLoading?"disabled":""}><option value="">No numeric ordering</option>${observationView.cohorts.map((c)=>`<option value="${c.id}" ${context?.id===c.id?'selected':''}>${esc(c.kind)} / ${esc(c.metric)} / ${esc(c.unit)} / ${esc(c.conditions_text.slice(0,160))}${c.conditions_text.length>160?"…":""} / ${esc(c.source.name)} / ${esc(c.source.version)} / ${c.evidence_ids.length} records / ${c.id}</option>`).join('')}</select></label><label class="field">Numeric order<select id="observation-direction" ${observationLoading?"disabled":""}><option value="ascending" ${state.observationDirection==='ascending'?'selected':''}>Ascending</option><option value="descending" ${state.observationDirection==='descending'?'selected':''}>Descending</option></select></label><p class="muted">Exact recorded context only; no averaging or unit conversion. Matching metadata does not establish scientific comparability. Missing values follow numeric values in either direction.</p></div>`+
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
  if (!bundle) return html + `<div class="panel empty"><p class="eyebrow">START WITH YOUR RESEARCH QUESTION</p><h2>Which candidate should we investigate next?</h2><p>Observe sequence differences, follow measurements to their original samples and conditions, and keep the reasoning for the next experiment.</p><button id="research-example-button">Explore two paired candidates — synthetic example</button> <button class="secondary" data-action="import">Import your local data</button><p class="muted">The example contains invented H/L candidates, distinct materials and a missing measurement. Preview it before saving. It does not validate the workflow with your own data.</p><p class="subtle">FASTA · Sequence CSV · Workspace JSON · PDB/mmCIF · Measurements</p></div>`;
  html += CompositionUI.explorer();
  html += `<p class="candidate-summary" aria-label="Candidate counts"><strong id="candidate-count">${molecules.length}</strong> candidates · <span id="candidate-selection-summary">${state.selected.length}</span> selected · ${evidence.length} evidence records (${evidence.filter((e)=>e.kind==="measured").length} measured, ${evidence.filter((e)=>e.kind==="computed").length} computed) · ${duplicateCount} sequence repeats. IDs remain distinct.</p>`;
  html += `<div class="panel"><div class="panel-head"><h2>Research candidates <span class="subtle">${shown.length} shown</span></h2><input class="search" id="candidate-search" type="search" placeholder="Search name, external ID or format" aria-label="Search candidates" value="${esc(state.filter)}"></div>`;
  html += `<div class="panel-body observation-controls"><label class="field">Group/order<select id="group-by"><option value="none" ${state.groupBy === "none" ? "selected" : ""}>Import order</option><option value="cdr3" ${state.groupBy === "cdr3" ? "selected" : ""}>Imported heavy-chain CDR3</option></select></label><label class="field">CDR-H3 group<select id="cdr3-filter"><option value="">All groups and unavailable maps</option>${groupView.groups.map((g) => `<option value="${g.group_id}" ${state.cdr3Group === g.group_id ? "selected" : ""}>${esc(g.cdr3_sequence)} (${g.candidate_ids.length})</option>`).join("")}</select></label><p class="muted">${groupView.groups.length} complete groups. Truncated, unverified and ambiguous maps remain explicit.</p></div>`;
  html += observationControls();
  html += `<div id="explorer-selection-context">${explorerSelectionContext()}</div>`;
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

function explorerSelectionContext(){
  return state.selected.length?`<div class="selected-strip"><span>${state.selected.length} candidate IDs held in context</span><div><button class="text-button" data-screen="W">Inspect sequences →</button> <button class="text-button" data-screen="R">Record selection →</button></div></div>`:'';
}
function updateExplorerSelection(checkbox){
  const context=$('#explorer-selection-context'),summary=$('#candidate-selection-summary');
  if(state.screen!=='E'||!context||!summary){render();return;}
  remember();
  $('#selection-count').textContent=`${state.selected.length} selected`;
  summary.textContent=String(state.selected.length);
  context.innerHTML=explorerSelectionContext();
  checkbox.closest('tr[data-candidate-id]')?.classList.toggle('selected',checkbox.checked);
}

function workspaceChain(molecule) {
  const chain = molecule.chains.find((c) => c.id === state.chains[molecule.id]) || molecule.chains[0];
  const maps = numberingView.maps.filter((map) => map.molecule_id === molecule.id && map.chain_id === chain.id);
  const mapKey = molecule.id + "|" + chain.id;
  const map = maps.find((item) => item.id === state.chainMaps[mapKey]) || (maps.length === 1 ? maps[0] : null);
  return {molecule, chain, maps, mapKey, map};
}

function comparableMaps(first, second) {
  return first?.status === 'mapped' && second?.status === 'mapped' && first.chain_type !== 'unknown' &&
    ['scheme', 'definition', 'chain_type'].every((field) => first[field] === second[field]);
}

function renderNumberedComparison(views) {
  const rows = views.toSorted((a, b) => a.molecule.external_id.localeCompare(b.molecule.external_id) ||
    a.molecule.id.localeCompare(b.molecule.id)).map((view) => ({
      ...view, entries: new Map(view.map.entries.map((entry) => [entry.coordinate, entry]))
    }));
  const positions = [...new Map(rows.flatMap((row) => [...row.entries])).values()].sort((a, b) =>
    a.order[0] - b.order[0] || a.order[1] - b.order[1] || a.order[2] - b.order[2]);
  const regions = [...new Set(positions.map((entry) => entry.region))];
  const selection = state.residueSelection;
  const selectedRow = rows.find(({molecule, chain}) => molecule.id === selection?.molecule_id && chain.id === selection.chain_id);
  const selectedRegion = selectedRow?.map.entries.find((entry) => entry.sequence_index === selection.sequence_index)?.region;
  const preferred = state.comparisonRegion || selectedRegion || 'CDR3';
  const region = preferred === 'all' || regions.includes(preferred) ? preferred : 'all';
  const columns = region === 'all' ? positions : positions.filter((entry) => entry.region === region);
  const headers = columns.map((entry) => `<th scope="col" title="${esc(entry.region)}">${esc(entry.coordinate)}</th>`).join('');
  const body = rows.map(({molecule, chain, map, entries}, index) => {
    const peer = rows[1 - index].entries;
    const cells = columns.map(({coordinate}) => {
      const entry = entries.get(coordinate);
      if (!entry) return '<td><span class="muted" aria-label="No annotation at this position">—</span></td>';
      const different = peer.has(coordinate) && peer.get(coordinate).aa !== entry.aa;
      const active = selectedRow?.molecule.id === molecule.id && selection.sequence_index === entry.sequence_index;
      const label = `${molecule.external_id} ${chain.id} ${map.scheme} ${coordinate} ${entry.aa}, raw index ${entry.sequence_index}`;
      return `<td class="${different ? 'coordinate-difference' : ''}"><button type="button" class="numbered-cell"
        data-numbered-index="${entry.sequence_index}" data-numbered-molecule="${molecule.id}" data-numbered-chain="${esc(chain.id)}"
        aria-label="${esc(label)}" aria-pressed="${active}">${esc(entry.aa)}<small>${entry.sequence_index}</small></button></td>`;
    }).join('');
    return `<tr><th scope="row">${esc(molecule.external_id)} / ${esc(chain.id)}<small>${esc(map.domain_id)} · ${esc(map.verification.status)}</small></th>${cells}</tr>`;
  }).join('');
  const options = [['all', 'All numbered positions'], ...regions.map((name) => [name, name])];
  return `<section class="panel numbered-comparison" aria-labelledby="numbered-comparison-title">
    <div class="panel-head"><h2 id="numbered-comparison-title">IMGT comparison</h2>
      <label>Region <select id="numbered-region">${options.map(([value, label]) =>
        `<option value="${esc(value)}" ${value === region ? 'selected' : ''}>${esc(label)}</option>`).join('')}</select></label>
    </div>
    <div class="table-wrap" id="numbered-scroll" role="region" aria-label="Numbered residue table" tabindex="0">
      <table aria-label="Imported IMGT coordinates"><thead><tr><th scope="col">Candidate / chain</th>${headers}</tr></thead><tbody>${body}</tbody></table>
    </div>
    <p class="comparison-note muted">Cells show the residue and its raw index. Gold marks differences. A dash means this map has no entry at that coordinate.</p>
    <div class="numbered-actions">
      ${selectedRow && entities('structure').some((structure) => structure.molecule_id === selectedRow.molecule.id)
        ? `<button class="secondary" data-numbered-structure="${selectedRow.molecule.id}">Inspect selected residue in structure</button>` : ''}
      <button class="secondary" data-design-selected>Design a substitution at the selected residue</button>
    </div>
  </section>`;
}

function selectWorkspaceResidue(moleculeId, chainId, rawIndex, keepComparison = false) {
  state.position = Number(rawIndex);
  if (!keepComparison) state.focus = moleculeId;
  state.residueSelection = {molecule_id:moleculeId, chain_id:chainId, sequence_index:state.position};
  render();
}

function workspaceMolecules() {
  const selected = selectedMolecules();
  const focus = entities("molecule").find((m) => m.id === state.focus);
  return focus ? [focus, ...selected.filter((m) => m.id !== focus.id)] : selected;
}

function renderWorkspace(molecules) {
  let html = '<div class="workspace-heading"><h1>Molecule Workspace</h1><p class="muted">Raw sequence indexes are 1-based and unaligned. Imported numbering and structure coordinates use their own identifiers.</p></div>';
  if (!molecules.length) return html + emptySelection();
  if (molecules.length > 2) html += `<p class="muted">Showing the first 2 of ${molecules.length} candidates in context. The full selection is retained.</p>`;
  const displayed = molecules.slice(0, 2);
  const views = displayed.map(workspaceChain);
  const paired = comparableMaps(views[0].map, views[1]?.map);
  const focusedMap = views.find(({molecule, chain}) =>
    molecule.id === state.residueSelection?.molecule_id && chain.id === state.residueSelection.chain_id)?.map;
  const focusedEntry = focusedMap?.entries.find((entry) => entry.sequence_index === state.position);
  if (paired) html += renderNumberedComparison(views);
  else if (views.length === 2 && views.some(({maps}) => maps.length)) {
    html += '<p class="muted">IMGT comparison needs two mapped domains with the same known chain type and numbering definition.</p>';
  }
  html += '<div class="two-columns workspace-candidates">';
  for (const [n, {molecule: m, chain, maps, mapKey, map}] of views.entries()) {
    const other = views[1 - n]?.chain;
    const positions = new Map((map?.entries || []).map((entry) => [entry.sequence_index, entry]));
    const exactSelection = state.residueSelection?.molecule_id === m.id && state.residueSelection.chain_id === chain.id;
    const rawPosition = paired && state.residueSelection && !exactSelection
      ? map.entries.find((entry) => entry.coordinate === focusedEntry?.coordinate)?.sequence_index
      : state.position;
    html += `<div class="panel"><div class="panel-head"><div><h2>${esc(m.name)}</h2>${m.external_id === m.name ? '' : `<p class="subtle">${esc(m.external_id)}</p>`}</div><span class="tag">${esc(m.format)}</span></div><div class="panel-body"><div class="workspace-chain-controls"><label class="field">Chain<select data-chain="${m.id}" aria-label="Chain for ${esc(m.external_id)}">${m.chains.map((c) => `<option value="${esc(c.id)}" ${c.id === chain.id ? "selected" : ""}>${esc(c.id)} / ${esc(c.role)} / ${c.sequence.length} aa</option>`).join("")}</select></label><label class="field">Jump to sequence index<input type="number" data-jump="${m.id}" min="1" max="${chain.sequence.length}" value="${rawPosition || 1}"></label></div>`;
    html += maps.length ? `<label class="field">Imported numbering map / domain<select data-chain-map="${esc(mapKey)}" aria-label="Numbering map for ${esc(m.external_id)} ${esc(chain.id)}"><option value="">${maps.length > 1 ? "Choose map/domain — no implicit match" : "Inspect imported map"}</option>${maps.map((item) => `<option value="${item.id}" ${map?.id === item.id ? "selected" : ""}>${esc(item.scheme)} / ${esc(item.domain_id)} / ${esc(item.status)} / ${esc(item.verification.status)}</option>`).join("")}</select></label>` : '<p class="muted">Numbering: mapping unavailable (no imported map).</p>';
    if (map) html += `<p class="muted">${esc(map.scheme)} / ${esc(map.domain_id)}: <strong>${esc(map.status)}</strong> · ${esc(map.verification.status)}${map.reason ? " / " + esc(map.reason) : ""}<br>${map.eligible ? (map.verification.status === "engineering_fixture" ? "Synthetic engineering annotation; human scientific validation pending." : "Source verification is a recorded external attestation; the application does not assign numbering.") : "Not eligible for source-verified numbering actions."}<br>CDR3: ${map.cdr3_complete ? esc(map.cdr3_sequence) : "partial / unavailable"}</p><details><summary>Numbering source, definition and verification</summary><p>${esc(map.source.name)} / ${esc(map.source.version || "version unknown")}</p><pre>${pretty(map.verification)}</pre><p class="muted">${esc(map.region_source)}</p>${NumberingImportUI.origin(map)}</details>`;
    // Long chains stay inspectable without rendering hundreds of thousands of buttons.
    const start = rawPosition > 200 ? Math.floor((rawPosition - 1) / 200) * 200 : 0;
    html += `<div class="sequence-viewport" role="region" aria-label="Sequence for ${esc(m.external_id)} ${esc(chain.id)}" tabindex="0" data-sequence-viewport="${esc(JSON.stringify([bundle.project.id, m.id, chain.id, start]))}"><div class="sequence">`;
    for (let i = start; i < Math.min(start + 200, chain.sequence.length); i++) {
      const difference = other && (other.sequence[i] ?? "absent") !== chain.sequence[i];
      const annotation = positions.get(i + 1);
      html += `<button class="residue ${difference ? "diff" : ""} ${rawPosition === i + 1 ? "active" : ""} ${annotation?.region.startsWith("CDR") ? "cdr-residue" : ""}" data-position="${i + 1}" data-position-molecule="${m.id}" data-position-chain="${esc(chain.id)}" aria-pressed="${exactSelection && rawPosition === i + 1}" aria-label="${esc(m.external_id)} ${esc(chain.id)} sequence index ${i + 1} ${chain.sequence[i]}" title="${annotation ? esc(`${map.scheme} ${annotation.coordinate} / ${annotation.region} / ${map.domain_id}`) : "No imported antibody coordinate"}"><small>${i + 1}</small>${chain.sequence[i]}${annotation ? `<small>${esc(annotation.coordinate)}</small>` : ""}</button>`;
    }
    const current = positions.get(rawPosition);
    const cursor = exactSelection ? 'Selected raw index' : paired ? 'Corresponding raw index' : 'Same raw index';
    html += `</div></div><p class="sequence-details">${rawPosition ? `${cursor} ${rawPosition}: ${esc(chain.sequence[rawPosition - 1] || "absent in this chain")} · ${current ? esc(`${map.scheme} ${current.coordinate} / ${current.region} / ${map.domain_id}`) : "numbering mapping unavailable for this index"}` : "Choose a sequence index to compare. Gold marks raw position differences."}</p>`;
    html += StructureUI.panel(m);
    html += `<details><summary>Sequence source and raw record</summary><p class="mono">Molecule: ${m.id}</p><p>${esc(m.source.name)} / ${esc(m.source.version || "version unknown")}</p><pre>${pretty(m)}</pre></details>`;
    html += reportedEvidence(m);
    const computedSources=entities('evidence').filter((e)=>e.prediction_origin&&subjectPath(e).some((p)=>p.id===m.id));
    if(computedSources.length)html+=`<section class="reported-evidence"><h3>Original computed sources</h3>${computedSources.map((e)=>`<article><span class="tag computed">computed</span> ${esc(e.metric)} / ${e.subject_id}${PredictionUI.origin(e)} <button class="text-button" data-source-evidence="${e.id}">Open source evidence in R</button></article>`).join('')}</section>`;
    html += renderComposition(m);
    const constructs = entities("construct").filter((c) => c.molecule_id === m.id);
    html += '<p class="section-label">CONSTRUCTS & MATERIALS</p>';
    html += constructs.length ? constructs.map((c) => `<details><summary>${esc(c.name)} (${c.id})</summary><pre>${pretty(c)}</pre><p class="muted">CDS translation and signal-peptide processing are not validated.</p>${entities("material").filter((s) => s.construct_id === c.id).map((s) => `<p class="muted">${esc(s.name)} / lot ${esc(s.lot)}<br><span class="mono">${s.id}</span><br><button class="text-button" data-expression-material="${s.id}">Inspect this Material's observations</button></p>`).join("")}</details>`).join("") : '<p class="muted">No construct or material registered.</p>';
    html += `<button class="secondary" data-expression-design="${m.id}">Compare / register expression constructs</button>`;
    html += '</div></div>';
  }
  return html + '</div>' + (paired ? '' : '<button data-design-selected>Design a substitution at the selected residue</button> ') +
    '<button data-screen="R">Follow evidence and record a question →</button>';
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
  const taskControls=bundle?`<div class="dialog-actions" aria-label="Design task"><button class="secondary" data-design-task="substitution" aria-pressed="${state.designTask==='substitution'}">Source-numbered substitutions</button>${CompositionUI.available()?`<button class="secondary" data-design-task="composition" aria-pressed="${state.designTask==='composition'}">Molecular composition</button>`:''}<button class="secondary" data-design-task="expression" aria-pressed="${state.designTask==='expression'}">Expression constructs</button></div>`:'';
  return heading("PRESERVE THE DESIGN HISTORY", "Design & Compare", "A shared design context for mutations, molecular composition and expression constructs.") +
    taskControls+(state.designTask==='composition'?CompositionUI.panel():state.designTask==='expression'?ExperimentUI.panel():DesignUI.panel())+DesignUI.hypothesesPanel();
}

function originalObservationValue(value) {
  return Object.is(value, -0) ? '-0' : value;
}

function comparisonObservation(evidence, showTime = false) {
  const subject = index().get(evidence.subject_id);
  const number = originalObservationValue(evidence.value);
  const value = number === null ? 'Value missing' : `${number} ${evidence.unit}`;
  const label = subject.type === 'material' ? `${subject.name} · lot ${subject.lot}` : `${subject.type} · ${subject.name}`;
  return `<button type="button" class="text-button comparison-record" data-source-evidence="${evidence.id}">${esc(value)}<small>${esc(label)}</small>${showTime ? `<small>${esc(evidence.timestamp)}</small>` : ''}</button>`;
}

function renderCandidateObservations(evidence) {
  const candidates = selectedMolecules();
  if (candidates.length < 2) return '';
  const owners = new Map(evidence.map((record) => [record.id, subjectPath(record).at(-1).id]));
  const rows = [];
  for (const context of observationView.cohorts) {
    const byCandidate = new Map();
    for (const id of context.evidence_ids) {
      const owner = owners.get(id);
      if (!owner) continue;
      if (!byCandidate.has(owner)) byCandidate.set(owner, []);
      byCandidate.get(owner).push(index().get(id));
    }
    if (byCandidate.size) rows.push({context, byCandidate});
  }
  // Show contexts shared by more selected candidates first, independent of the values.
  rows.sort((left, right) => right.byCandidate.size - left.byCandidate.size);
  const incomplete = observationView.ineligible.filter((entry) => owners.has(entry.evidence_id)).length;
  let html = '<section class="panel" id="candidate-observations"><div class="panel-head"><h2>Compare original observations</h2></div>';
  if (!rows.length) {
    return html + '<p class="panel-body muted">No observations with a complete comparison context. See the original Evidence below.</p></section>';
  }

  const maxOverviewRows = 4;
  let selected;
  if (rows.length > maxOverviewRows) {
    selected = rows.find(({context}) => context.evidence_ids.includes(state.comparisonContext));
    html += `<label class="field comparison-filter">Observation context<select id="comparison-context">
      <option value="">Overview · ${maxOverviewRows} of ${rows.length} recorded contexts</option>
      ${rows.map((row) => {
        const {context} = row;
        const label = `${context.kind} / ${context.metric} / ${context.unit} / ${context.conditions_text} / ${context.source.name} ${context.source.version}`;
        return `<option value="${context.id}" ${selected === row ? 'selected' : ''}>${esc(label)}</option>`;
      }).join('')}
      </select></label>`;
  }
  html += '<div class="table-wrap"><table class="comparison-table"><thead><tr><th scope="col">Recorded context</th>';
  html += candidates.map((candidate) => `<th scope="col">${esc(candidate.external_id)}<small>${esc(candidate.name)}</small></th>`).join('');
  html += '</tr></thead><tbody>';
  for (const {context, byCandidate} of selected ? [selected] : rows.slice(0, maxOverviewRows)) {
    html += `<tr><th scope="row"><span class="tag ${esc(context.kind)}">${esc(context.kind)}</span> ${esc(context.metric)} <small>${esc(context.unit)} · ${esc(context.source.name)} ${esc(context.source.version)}</small><small>${esc(context.conditions_text)}</small></th>`;
    for (const candidate of candidates) {
      const records = byCandidate.get(candidate.id) || [];
      let cell = '<span class="muted">No record in this context</span>';
      if (records.length === 1) cell = comparisonObservation(records[0]);
      if (records.length > 1) cell = `<details><summary>${records.length} original observations</summary>${records.map((record) => comparisonObservation(record, true)).join('')}</details>`;
      html += `<td>${cell}</td>`;
    }
    html += '</tr>';
  }
  return html + `</tbody></table></div><p class="comparison-note muted">Rows share recorded conditions and source. Check sample details for scientific comparability.${incomplete ? ` ${incomplete} records outside these contexts are available under original Evidence.` : ''}</p></section>`;
}

function renderEvidence() {
  let html = heading("RETAIN THE REASONING", "Evidence & Decision", "Separate observations from calculations, and keep the subject and source attached.");
  if (!state.selected.length) return html + emptySelection();
  html+=`<div class="dialog-actions" aria-label="Research task"><button class="secondary" data-research-task="evidence" aria-pressed="${state.researchTask!=='decision'}">Evidence and research questions</button><button class="secondary" data-research-task="decision" aria-pressed="${state.researchTask==='decision'}">Criteria and decision versions</button></div>`;
  const deciding=state.researchTask==='decision';
  const evidence = selectedEvidence();
  const conditionsByEvidence = new Map();
  for (const context of observationView.cohorts) {
    for (const id of context.evidence_ids) conditionsByEvidence.set(id, context.conditions_text);
  }
  html += renderCandidateObservations(evidence);
  html += '<p><button data-open-hypothesis>Record research hypothesis</button></p>';
  html += deciding?DecisionUI.panel():ExperimentUI.evidencePanel();
  const draft=shortlistDraft();
  html += `${deciding?'<details id="decision-original-evidence"><summary>Inspect all original Evidence cards (subjects and sources unchanged)</summary>':''}<div class="${deciding?'':'two-columns'}"><div><div class="panel"><div class="panel-head"><h2>Evidence for ${state.selected.length} selected candidates</h2><span class="subtle">${evidence.length} records</span></div>`;
  if (!evidence.length) html += '<div class="panel-body"><p class="muted">Not measured / not predicted. No evidence records were registered for this selection.</p></div>';
  for (const e of evidence) {
    const path = subjectPath(e);
    const conditions = conditionsByEvidence.get(e.id) ?? JSON.stringify(e.conditions);
    html += `<article class="evidence-row" id="evidence-${e.id}" tabindex="-1"><div class="metric"><div><span class="tag ${esc(e.kind)}">${esc(e.kind)}</span><p>${esc(e.metric)}</p></div><div class="value">${e.value === null ? '<span class="muted">'+(e.description?'No numeric value supplied':'Value missing')+'</span>' : esc(originalObservationValue(e.value)) + ' <span class="muted">' + esc(e.unit) + '</span>'}</div></div>${e.description?`<p>${esc(e.description)}</p>`:''}${reportedPositions(e)}<p class="muted">${path.map((p) => `${esc(p.type)}: ${esc(p.name)}`).join(" → ")}</p><p>Source: ${esc(e.source.name)} / ${esc(e.source.version || "version unknown")}<br>Event time: ${esc(e.timestamp)}</p><p>${e.conditions === null ? '<span class="tag warning">Conditions unknown — do not pool</span>' : 'Conditions: ' + esc(conditions)}</p>${["iptm","ptm"].includes(e.metric.toLowerCase()) ? '<p class="muted">Model-internal metric; not measured binding affinity. Model scope is declared in the source conditions or remains unspecified.</p>' : ""}${e.kind === "computed" ? '<p class="muted">Computed result. Interpretation and uncertainty depend on the source; this is not an experimental measurement.</p>' : ""}${PredictionUI.origin(e)}<details><summary>Original record, subject IDs & provenance</summary><pre>${pretty(e)}</pre>${path.map((p) => `<p class="mono">${esc(p.type)}: ${p.id}</p>`).join("")}</details>${deciding?'':`<label class="evidence-check"><input type="checkbox" data-evidence="${e.id}" ${draft.evidenceIds.has(e.id)?"checked":""}> Include in draft snapshot</label>`}</article>`;
  }
  if(deciding)return html+'</div></div></div></details>'+DesignUI.hypothesesPanel();
  html += '</div></div><div><div class="panel"><div class="panel-head"><h2>Save a shortlist draft</h2><span class="tag">Draft only</span></div><div class="panel-body"><p class="muted">Record why these candidates deserve further investigation. Use Criteria and decision versions above for explicit requirements, finalization and revisions.</p><p class="section-label">CANDIDATES IN CONTEXT</p>';
  html += selectedMolecules().map((m) => `<p class="wrap">${esc(m.external_id)} — ${esc(m.name)}<br><span class="mono">${m.id}</span></p>`).join("");
  html += `<label class="field">Reason and next research question<textarea id="shortlist-reason" rows="5" placeholder="What did you observe? Why keep this selection? What remains unverified?">${esc(draft.reason)}</textarea></label><p class="muted">Unsaved text and evidence choices remain in this tab for this project and candidate set. Save a draft before closing or reloading the tab.</p><button id="review-shortlist">Review before saving</button></div></div>`;
  const decisions = entities("decision").filter((d) => !Object.hasOwn(d,"chosen_candidate_ids") && d.candidate_ids.some((id) => state.selected.includes(id)));
  html += `<div class="panel"><div class="panel-head"><h2>Saved shortlist drafts</h2><span class="subtle">${decisions.length} records</span></div>`;
  if (!decisions.length) html += '<p class="panel-body muted">No saved draft for this selection.</p>';
  for (const d of decisions.toReversed()) html += `<article class="saved-draft"><span class="tag">Draft · immutable record</span><p>${esc(d.reason)}</p><p class="muted">${d.candidate_ids.length} candidate IDs · ${d.evidence_snapshot.length} evidence snapshots<br>${esc(d.timestamp)}</p><button class="text-button" data-restore="${d.id}">Restore this selection</button> <button class="text-button" data-revise-decision="${d.id}" ${entities("decision").some((next)=>next.supersedes===d.id)?"disabled":""}>Continue as a criterion-based revision</button><details><summary>Saved IDs and frozen evidence</summary><pre>${pretty(d)}</pre></details></article>`;
  return html + '</div></div></div><p class="muted">Measurements are not averaged or ranked across different units or conditions. Missing values remain unknown.</p>'+DesignUI.hypothesesPanel();
}

async function loadProject(id) {
  invalidateShortlistPreview();$('#shortlist-dialog').close();
  DecisionUI.invalidate();
  importEpoch++;PredictionUI.reset();pendingImport=null;mappingDraft=null;ExperimentUI.invalidate();
  DesignUI.invalidate();
  CompositionUI.invalidate();
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
    const unitIds=new Set(entities('binding_unit').map((u)=>u.id));
    state.selectedUnits=Array.isArray(state.selectedUnits)?state.selectedUnits.filter((id)=>unitIds.has(id)):[];
    for(const key of ['compositionCurrent','compositionParent','compositionCompareLeft','compositionCompareRight'])if(state[key]&&!ids.has(state[key]))state[key]=null;
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
  NumberingImportUI.reset();
  $("#numbering-tool-version").value = "";
  sequenceGrouping=null;
  importEpoch++;mappingDraft=null;PredictionUI.reset();
  $('#import-dialog > .dialog-error')?.remove();
  pendingImport = null; $("#import-preview").hidden = true; $("#import-form").hidden = false;
  $("#import-target").value = bundle?.project.id || ""; $("#new-project-fields").hidden = !!bundle;
  $("#import-dialog").showModal();
  updateStructureImport();
}
async function updateStructureImport() {
  PredictionUI.update();
  $("#numbering-import-options").hidden = $("#import-format").value !== "anarci_text";
  const coordinate = ["pdb","mmcif"].includes($("#import-format").value);
  $("#structure-import-options").hidden = !coordinate;
  $("#measurement-import-options").hidden = $("#import-format").value!=='measurement_csv';
  if (!coordinate) return;
  const target=$("#import-target").value;
  let incoming=target===bundle?.project.id?entities("molecule"):[];
  if (target && target!==bundle?.project.id) {try {incoming=(await api('/api/bundle?project_id='+encodeURIComponent(target))).entities.filter((e)=>e.type==='molecule');} catch(error){notify(error.message,true);}}
  if ($("#import-target").value!==target) return;
  $("#structure-molecule").innerHTML = '<option value="">Choose an explicitly registered molecule</option>' + incoming.map((m)=>`<option value="${m.id}">${esc(m.external_id)} / ${esc(m.name)}</option>`).join("");
}
function renderPreview(result, synthetic = false) {
  $('#import-dialog > .dialog-error')?.remove();
  pendingImport = result.bundle;
  const r = result.report;
  $("#import-form").hidden = true; const target = $("#import-preview"); target.hidden = false;
  const previewRecords = pendingImport.entities.slice(0, 8).map((entity) => {
    if(entity.type!=="numbering_file")return entity;
    const {content,...metadata}=entity;
    return metadata;
  });
  const samples = pendingImport.entities.filter((e) => e.type === "molecule").slice(0, 5);
  target.innerHTML = `<h2>Review before saving</h2>${synthetic ? '<p class="fixture-notice">Synthetic fixture. These are invented engineering values, not real scientific results.</p>' : ""}<p class="muted">Project: ${esc(pendingImport.project.title)}</p><div class="preview-summary">${r.total_rows} input rows · ${r.valid_rows} valid · ${r.excluded.length} excluded · ${r.duplicates.length} ${r.kind==='computed_json'?'potential repeated-source':r.kind==='measurement_csv'?'potential repeated-observation':'sequence-repeat'} warnings</div><p class="muted">${pendingImport.entities.length} entities will be added. Existing records are never overwritten. IDs and references are revalidated at save time.</p>${r.excluded.length ? `<h3>Excluded records (not saved)</h3><pre class="preview-list">${pretty(r.excluded)}</pre>` : ""}${r.duplicates.length || r.warnings.length ? `<details><summary>QC warnings</summary><pre class="preview-list">${pretty([...r.duplicates, ...r.warnings])}</pre></details>` : ""}${samples.length?`<h3>Sample of incoming candidates</h3><ul class="muted">${samples.map((m) => `<li>${esc(m.external_id)} / ${esc(m.name)} / ${esc(m.format)}<ul>${m.chains.map((c)=>`<li>${esc(c.id)} / ${esc(c.role)} / ${c.sequence.length} aa<details><summary>Sequence</summary><pre>${esc(c.sequence)}</pre></details></li>`).join('')}</ul></li>`).join("")}</ul>`:''}${sequenceGroupingPanel(r)}${NumberingImportUI.panel(r,pendingImport)}${measurementMappingPanel(r)}${PredictionUI.mappingPanel(r)}<details><summary>Incoming records and source metadata</summary><pre class="preview-list">${pretty(previewRecords)}</pre></details>${r.kind==='measurement_csv'?`<details><summary>Full measurement import QC and mapping provenance</summary><pre>${pretty(r)}</pre></details>`:''}<div class="dialog-actions"><button class="secondary" id="back-import">Back</button><button id="commit-import" ${pendingImport.entities.length ? "" : "disabled"}>Save ${r.valid_rows} valid rows${r.excluded.length ? " (excluded rows omitted)" : ""}</button></div>`;
}

function sequenceGroupingPanel(report){
  if(report.kind!=='grouped_fasta'||!report.sequence_records.length)return '';
  return `<section><h3>Declare which chains belong to each candidate</h3><p>Use the same candidate ID for records belonging to one molecular candidate, and distinct chain IDs within it. Roles and format are your declarations. Header names and sequence similarity do not establish pairing. Every source record needs an explicit assignment.</p><label class="field">Declared molecular format for these candidates<input id="group-molecular-format" value="unspecified" placeholder="e.g. Fab (user declaration)"></label><table><thead><tr><th>Source FASTA record</th><th>Candidate external ID</th><th>Chain ID</th><th>Declared chain role</th></tr></thead><tbody>${report.sequence_records.map((r)=>`<tr data-sequence-record="${r.record_index}"><td>Record ${r.record_index+1}, line ${r.row}: ${esc(r.external_id)}<br>${r.sequence.length} aa<details><summary>Source sequence</summary><pre>${esc(r.sequence)}</pre></details></td><td><input data-group-candidate aria-label="Candidate for record ${r.record_index+1}" maxlength="500"></td><td><input data-group-chain aria-label="Chain ID for record ${r.record_index+1}" maxlength="100"></td><td><input data-group-role aria-label="Role for record ${r.record_index+1}" placeholder="heavy, light, or unknown" maxlength="100"></td></tr>`).join('')}</tbody></table><button id="apply-sequence-grouping">Apply declared grouping &amp; preview candidates</button></section>`;
}

function measurementMappingPanel(report){
  if(report.kind!=='measurement_csv'||!mappingDraft)return '';
  const byId=new Map(mappingDraft.records.map((e)=>[e.id,e]));
  return `<section id="measurement-mapping"><h3>Actual Material mapping</h3><p class="muted">Choose each external token's actual Material/lot. Equal names or protein sequences do not establish identity. Canonical application IDs cannot be redirected. Choices apply only to this submitted file text and project.</p>${report.unresolved_refs.map((ref,i)=>`<label class="field">Original token: ${esc(ref)}<select data-measurement-map="${i}"><option value="">Unresolved — exclude these rows</option>${mappingDraft.records.filter((e)=>e.type==='material').map((mat)=>{const con=byId.get(mat.construct_id),mol=byId.get(con.molecule_id);return `<option value="${mat.id}">${esc(mat.name)} / lot ${esc(mat.lot)} / ${mat.id} → ${esc(con.name)} / ${con.id} → ${esc(mol.external_id)} / ${mol.id}</option>`;}).join('')}</select></label>`).join('')}${report.unresolved_refs.length?'<button id="apply-measurement-mappings" class="secondary">Apply mappings &amp; preview again</button>':''}</section>`;
}

async function validateImport(){
  const ticket=++importEpoch,dialog=$('#import-dialog');
  const originalFile=importSourceText&&importSourceText.file===$('#import-file').files[0]&&importSourceText.text===$('#import-text').value;
  const request={text:originalFile?importSourceText.decoded:$('#import-text').value,format:$('#import-format').value,filename:$('#import-file').files[0]?.name||'pasted-local-input',
    project_id:$('#import-target').value||null,title:$('#project-title').value,goal:$('#project-goal').value,data_class:$('#project-data-class').value};
  let result;
  const current=()=>ticket===importEpoch&&dialog.open;
  try{
    if(request.format==='anarci_text'){
      result=await NumberingImportUI.preview(request,current);
    }else if(request.format==='fasta_grouped'){
      const mapped=sequenceGrouping?.text===request.text&&sequenceGrouping.project===request.project_id;
      request.sequence_options={assignments:mapped?sequenceGrouping.assignments:null,text_sha256:mapped?sequenceGrouping.sha:null,molecular_format:mapped?sequenceGrouping.format:'unspecified'};
      result=await api('/api/preview',request);if(!current())return;
      if(result.report.sequence_records.length)sequenceGrouping={text:request.text,project:request.project_id,sha:result.report.text_sha256,assignments:null,format:'unspecified'};
    }else if(request.format==='measurement_csv'){
      if(!request.project_id)throw Error('Measurement CSV requires an existing project with actual Construct/Material IDs. Register Materials first.');
      const mapped=mappingDraft?.project===request.project_id&&mappingDraft.text===request.text;
      result=await api('/api/measurement-preview',{project_id:request.project_id,text:request.text,filename:request.filename,
        mappings:mapped?Object.fromEntries(mappingDraft.choices):{},mapping_text_sha256:mapped?mappingDraft.sha:null,
        file_source:{name:$('#measurement-source').value||request.filename,version:$('#measurement-source-version').value||null}});
      if(!current())return;
      const original=await api('/api/bundle?project_id='+encodeURIComponent(request.project_id));if(!current())return;
      mappingDraft={project:request.project_id,text:request.text,sha:result.report.text_utf8_sha256,refs:result.report.unresolved_refs,
        choices:new Map(Object.entries(result.report.mappings)),records:original.entities};
    }else if(['prediction_json','af3_summary'].includes(request.format)){
      result=await PredictionUI.preview(request,current);
    }else{
      if(['pdb','mmcif'].includes(request.format))request.structure_options={molecule_id:$('#structure-molecule').value,origin_kind:$('#structure-origin').value,
        source_name:$('#structure-source').value,source_version:$('#structure-source-version').value||null};
      result=await api('/api/preview',request);
    }
    if(result&&current())renderPreview(result);
  }catch(error){if(current())notify(error.message,true);}
}

async function readImportFile(input, file, reading){
  const dialog=$('#import-dialog');
  const current=()=>importFileRead===reading&&input.files[0]===file&&dialog.open;
  try{
    if(file.size>24*1024*1024)throw Error('Maximum input file size is 24 MiB.');
    const format=$('#import-format');
    const name=file.name.toLowerCase(),ext=name.split('.').pop();
    if(name.endsWith('.anarci.txt'))format.value='anarci_text';
    else if(['txt','out','anarci'].includes(ext)&&format.value==='anarci_text'){}
    else if((ext==='csv'&&format.value==='measurement_csv')||(ext==='json'&&['prediction_json','af3_summary'].includes(format.value))){}
    else if(['json','csv','pdb'].includes(ext))format.value=ext;
    else if(['cif','mmcif'].includes(ext))format.value='mmcif';
    else if(['fa','fasta','faa'].includes(ext)){if(format.value!=='fasta_grouped')format.value='fasta';}
    else throw Error('Unsupported file format; no data saved.');
    updateStructureImport();
    let decoded;
    try{decoded=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(await file.arrayBuffer());}
    catch{throw Error('File must be valid UTF-8. Unsupported or unreadable file; no data saved.');}
    if(!current())return false;
    const text=$('#import-text');
    text.value=decoded;
    importSourceText={file,text:text.value,decoded};
    return true;
  }catch(error){
    if(current())notify(error.message,true);
    return false;
  }finally{
    if(importFileRead===reading)importFileRead=null;
  }
}

const guides = {
  en:`<h3>Observe, then retain the reasoning</h3><ol class="scope-list"><li>Import a local FASTA, sequence CSV or awx/1 JSON. Inspect the preview and excluded rows before saving.</li><li>Select candidates in E. Open W to inspect chains and compare raw sequence indexes. These are not IMGT positions or an alignment.</li><li>In R, follow each evidence record to its source and subject. Measured values belong to a particular material and construct.</li><li>Write a reason, review the candidate IDs and evidence snapshot, and save a shortlist draft.</li><li>Export JSON for an explicit local backup or import into a fresh database. An existing ID collision rejects the entire import.</li></ol><p>Missing values stay unknown; zero remains zero. Measured, computed, literature and annotation are distinct. Drafts are not finalized decisions. Imported numbering maps, CDR-H3 groups and local PDB/mmCIF observation with explicit correspondence are supported. D can create an explicit source-numbered substitution design and a proposed research hypothesis. Select a residue in W, choose Design a substitution, inspect a reference if supplied, then review the new child and exact lineage. Child numbering, structures and measurements are not inherited. In R, save the proposed hypothesis, original evidence, limitations and next experiment. Automatic numbering remains unavailable. Criterion-bearing decision versions are a separate R task with explicit requirements and immutable revisions. Composition recipes are declarations, not validated physical assembly. Camera linking shares orientation and zoom; it does not superpose structures. B-values are not automatically treated as confidence.</p><h3>Explicit molecular composition</h3><p>In E, select actual BindingUnit sources and choose Design an explicit composition. In D, enter chains, roles, copy counts and ordered source-chain intervals or literal linker/component sequences. Preview the actual source-chain usage, including absent partners and unequal declared occurrences, before saving. These counts do not establish functional units or valency. Inspect each saved chain in W; compare two saved designs in D. Using an explicit parent recipe retains exact component IDs and composition Lineage. In R, retain unverified assembly questions and the next experiment as a proposed hypothesis. Computed results can be imported with explicit source/subject scope; no predictive model is executed here. Imported maps and coordinates retain their actual scope.</p><h3>Reported positions and structural context</h3><p>Follow Source-reported position links from W or R to the actual molecule/chain/raw index. These links retain an association from the source; they do not localize a whole-material measurement or establish causality. In W, choose atoms, distance-based ball-and-stick or C-alpha atoms and focus the exact selected source residue. C-alpha is an atom subset, not assigned secondary structure. Unmapped source selections do not select an antibody sequence residue. A reviewed hypothesis can retain the exact file/model/source residue/alternate state without converting it into experimental evidence.</p><h3>Contextual numeric ordering</h3><p>In E, choose an observation context and numeric direction. Units, assay conditions, evidence kind and source/version remain separate. Matching metadata does not prove scientific comparability. If several observations exist, choose the actual material/evidence record explicitly. No averaging, unit conversion or missing-value replacement is performed. The original records remain available in R.</p><details><summary>Domain terminology: humanization and humanness</summary><p>Humanization means engineering a non-human antibody toward a human antibody framework while evaluating effects experimentally. A humanness score has a model-specific definition; no such score is implemented or inferred here.</p></details>`,
  ja:`<h3>観察した内容と判断の理由を残す</h3><ol class="scope-list"><li>ローカルのFASTA、配列CSV、awx/1形式のJSONを読み込みます。保存前に取込内容と除外行を確認します。</li><li>Eで候補を選び、Wで鎖と配列を確認します。表示位置は配列先頭からの通し番号で、IMGT番号やアラインメントによる対応位置ではありません。</li><li>Rでは根拠の出典と対象を確認します。実測値は特定の試料とコンストラクトに紐づきます。</li><li>選定理由を書き、候補IDと根拠の保存内容を確認して、ショートリストの下書きを保存します。</li><li>明示的にJSONを書き出し、バックアップや空のデータベースへの再取込に利用できます。同じIDがあれば取込全体を拒否します。</li></ol><p>欠測値と0は区別します。実測、計算結果、文献、注釈も区別します。下書きは確定した意思決定ではありません。出典を持つ番号対応表の取込、CDR-H3群分け、ローカルのPDB/mmCIF表示に対応しています。構造ファイル中の鎖ID、残基番号、挿入コードと配列位置を明示的に対応付けます。視点の同期は構造の重ね合わせではありません。B値を予測信頼度と自動的に同一視しません。Wで残基を選び、Design a substitutionからDへ進むと、出典を持つ番号対応表を使って置換を指定できます。比較配列があれば対応位置を確認し、新しい子候補と変更記録を保存前に確認します。子の番号付け、構造、実測値は親から引き継ぎません。Rでは未検証の仮説、原根拠、限界、次の実験を別の記録として保存します。番号付けの自動実行は未対応です。評価項目を使う判断記録は、Rの別の作業として必須条件を明示し、確定後は新しい版として改訂します。分子構成の設計は宣言の保存であり、実際の会合を検証したものではありません。</p><h3>分子構成の明示的な設計</h3><p>Eで元の結合単位を選び、Design an explicit compositionからDへ進みます。鎖、役割、コピー数、使用する元の鎖と区間、領域やリンカーなどの構成要素の配列と順序を指定します。保存前に、結合単位で定義した各鎖について、全区間の使用数と部分区間の使い方、使用していない相方の鎖を確認します。使用数は宣言したコピー数に基づき、機能する結合単位の数や結合価を意味しません。Wで保存した各鎖の配列を観察し、Dで2つの設計を比較できます。元にする設計を明示して変更すると、構成要素のIDと構成変更の親子関係を保持します。Rでは会合などの未検証事項と次の実験を仮説として残します。検証済みの解析アダプターがないため、分子全体の予測は利用できません。取り込んだ番号対応表と構造の対象範囲は自動で広げません。</p><h3>報告された位置と構造の観察</h3><p>WとRのSource-reported positionから、出典に記載された分子・鎖・配列位置をたどれます。この関連付けは、試料全体の測定値が特定の残基に由来することや、因果関係を示すものではありません。Wでは原子表示、距離に基づく球棒表示、標準アミノ酸のCα原子表示を選び、選択した残基へ視点を合わせられます。Cα表示は原子の抜粋で、二次構造の判定ではありません。配列との対応がない構造上の選択から、抗体の配列位置を推測しません。仮説には観察したファイル・モデル・元の残基識別子・代替配座を保存でき、実測の根拠とは区別されます。</p><h3>条件を区別した値の並べ替え</h3><p>EでObservation contextと並び順を選びます。単位、測定条件、実測と計算、出典と版を区別します。記録された条件が一致しても、科学的に比較可能であることを保証しません。複数の結果がある場合は、使用する試料と根拠の記録を明示的に選びます。平均、単位換算、欠測値の補完は行いません。原記録はRで確認できます。</p><details><summary>専門用語：ヒト化とヒト抗体らしさ</summary><p>humanizationは「ヒト化」です。非ヒト抗体の配列をヒト抗体に近づける改変を指し、機能への影響は別途評価します。humanness（ヒト抗体らしさ）は指標ごとに定義が異なるため、必要に応じて英語を併記し、ヒト抗体配列との類似性をどう評価した値かを説明します。この製品では現時点でその指標を計算していません。</p></details>`
};
guides.en += `<h3>Expression constructs and original measurements</h3><p>Select the actual antibody in E and choose Expression constructs in D. Register each Construct against that Molecule, then each Material against its actual Construct and lot. Compare recorded CDS, vector and signal peptide metadata. Raw DNA positions are unaligned and separate from amino-acid indexes; no translation or expression effect is inferred. Follow the actual Materials in W. Import Measurement CSV into the existing project, review excluded rows and explicitly map external sample tokens to actual Materials. Use original units, assay conditions, source/version and timezone-bearing event times. Blank scalar values remain null; ND and qualified values such as &lt;0.1 are not supported point values. R shows separate original observations, including unknown conditions, and lets you retain a proposed explanation, limitations and the next controlled experiment. File/importer provenance is distinct from the experimental source; a recorded attestation does not authenticate an absent original file. No averaging, conversion or independent-replicate claim is made.</p>`;
guides.ja += `<h3>発現コンストラクトと元の測定結果</h3><p>Eで対象の抗体を選び、DのExpression constructsを開きます。各コンストラクトを対象の分子IDに、各試料を実際のコンストラクトIDとロットに対応付けて登録します。記録されたCDS、ベクター、シグナルペプチドの情報を比較できます。DNAの位置は未整列の配列上の位置であり、アミノ酸残基の位置とは区別します。翻訳の一致や発現への影響を推定する機能ではありません。Wでは実際の試料との関係を確認できます。測定CSVは既存プロジェクトに取り込み、除外行を確認し、ファイル内の試料名を実際の試料IDに明示的に対応付けます。元の単位、測定条件、出典とバージョン、タイムゾーンを含む測定日時を指定してください。数値の空欄は欠測として保持し、NDや「&lt;0.1」などをゼロや閾値の測定値に置き換えません。Rでは各試料の元の観測結果を別々に確認し、仮説、限界、次の比較実験を保存できます。ファイルの取り込み履歴と実験の出典は区別します。記録された来歴だけで、手元にない元ファイルの真正性が保証されるわけではありません。平均、単位変換、独立した反復実験であるとの判定は行いません。</p>`;
guides.en += `<h3>Criteria and immutable decision versions</h3><p>Select actual comparison candidates in E, open R and choose Criteria and decision versions. Add an original observation context, explicitly enter importance and preference, and choose each original Evidence record, including its actual subject/lot. A lone eligible result is not chosen automatically. Weight is declared importance; no composite score or recommendation is calculated. Required criteria need a selected numeric observation for every compared candidate, including unchosen candidates, even when importance is 0. Missing optional observations remain visible. Record your chosen subset, trade-offs and supporting proposed hypotheses, then review/save a draft or finalized version. Inspect an original subject in W and return to the same in-memory draft. A later change creates a new ID and revision; it cannot overwrite a finalized record. Review explicitly changed criteria/weights/requirements and explain the new version. Saved versions retain original sources and event times; later results do not update old snapshots. Export JSON includes the full project and revision dependencies. Finalized means the decision record is fixed; it does not validate a scientific conclusion or authenticate the researcher.</p>`;
guides.ja += `<h3>評価項目と変更できない判断記録</h3><p>Eで実際の比較対象を選び、RのCriteria and decision versionsを開きます。元の観測結果の条件を選び、重要度と評価の方向を明示し、各候補に使う根拠の記録を実際の試料・ロットとともに指定します。利用できる結果が1件だけでも自動選択しません。重みは研究者が指定した重要度であり、総合点や推奨候補を計算するものではありません。必須項目には、採用しない候補も含め、比較対象すべてについて数値を持つ元の観測結果の選択が必要です。重要度が0でも、この必須条件は変わりません。任意項目の欠測はそのまま表示します。採用する候補、トレードオフ、関連する提案段階の仮説を記録し、下書きまたは確定版を確認して保存します。Wで元の対象を調べてRに戻っても、操作中の下書きを保持します。確定済みの記録は上書きできず、変更は別IDの新しい版として保存します。評価項目・重み・必須条件の変更点を確認し、その理由を記入してください。後日の結果追加で、過去の根拠の保存内容が変わることはありません。Export JSONには、プロジェクト全体と改訂元も含まれます。確定は判断記録を固定する意味であり、科学的結論の妥当性や入力者の本人認証を保証しません。</p>`;
guides.en += `<h3>Start with paired candidates or your own FASTA</h3><p>On an empty workspace, preview the synthetic two-candidate example, compare H/L chains in W, inspect original materials and conditions in R, then save a reason and next experiment. To register your own chains, choose FASTA (explicit candidate / chain grouping). Assign each source record to a candidate ID and a distinct chain ID with a declared role. Review the actual sequences before saving. Normal FASTA imports remain unpaired. Structures, numbering, constructs, materials and measurements must be registered against their actual subjects separately.</p>`;
guides.ja += `<h3>複数鎖の候補と手元のFASTAから始める</h3><p>空のワークスペースでは、2候補の合成例を保存前に確認できます。Wで重鎖・軽鎖を比較し、Rで元の試料と測定条件を確認して、選定理由と次の実験を保存します。手元のFASTAは、明示的な候補・鎖の割当を行う形式を選び、各レコードに候補ID、候補内で重複しない鎖ID、鎖の役割を指定します。実際の配列を確認してから保存してください。通常のFASTA取込では各配列を別候補として扱います。構造、番号対応、コンストラクト、試料、測定結果は、それぞれ実際の対象に紐付けて別途登録します。</p>`;
guides.en += `<h3>Numbering and deposited coordinates</h3><p>Import ANARCI IMGT numbering text into an existing project. Bind each source domain to its exact candidate chain and review the interval and verification state. W can download the original file. Enter a scientific review record when it covers the selected domains. For mmCIF, assign the source chains in W and choose Use deposited polymer positions to check the complete sequences and review mapped or unavailable positions.</p>`;
guides.ja += `<h3>番号付け結果と構造の残基対応</h3><p>既存のプロジェクトにANARCIのIMGT番号付けテキストを取り込みます。元のドメインを実際の候補と鎖に割り当て、配列範囲と照合状態を確認します。元ファイルはWから保存できます。対象ドメインを人が照合した記録がある場合は、その記録を入力します。mmCIFでは、Wで元の鎖を指定し、Use deposited polymer positionsから全鎖配列の一致と、座標が対応する位置・対応できない位置を確認できます。</p>`;
guides.en += PredictionUI.guide.en;
guides.ja += PredictionUI.guide.ja;
function renderHelp() {
  const language=$("#help-language").value;
  $("#help-content").lang=language;
  $("#help-content").innerHTML=guides[language];
}

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button || button.disabled || loading) return;
  let ownsError=()=>true;
  try {
    if (button.dataset.screen) { state.screen = button.dataset.screen; render(); }
    else if (button.dataset.close) $("#" + button.dataset.close).close();
    else if (button.dataset.action === "import" || button.id === "import-button") showImport();
    else if (button.dataset.open) { state.focus = button.dataset.open; state.screen = "W"; render(); }
    else if (button.dataset.position) {
      selectWorkspaceResidue(button.dataset.positionMolecule, button.dataset.positionChain, button.dataset.position);
      $('.sequence-viewport [aria-pressed="true"]')?.focus({preventScroll:true});
    }
    else if (button.dataset.numberedIndex) {
      const left = $('#numbered-scroll').scrollLeft;
      const {numberedMolecule, numberedChain, numberedIndex} = button.dataset;
      selectWorkspaceResidue(numberedMolecule, numberedChain, numberedIndex, true);
      const scroll = $('#numbered-scroll');
      if (scroll) scroll.scrollLeft = left;
      $('.numbered-cell[aria-pressed="true"]')?.focus({preventScroll:true});
    }
    else if (button.dataset.numberedStructure) {
      const section = $(`[data-structure-molecule="${button.dataset.numberedStructure}"]`);
      section?.scrollIntoView({block:'start'});
      section?.querySelector('select')?.focus({preventScroll:true});
    }
    else if (button.dataset.reportedEvidence) {
      const evidence=index().get(button.dataset.reportedEvidence),molecule=subjectPath(evidence).find((p)=>p.type==='molecule');
      state.focus=molecule.id;state.chains[molecule.id]=button.dataset.reportedChain;state.position=Number(button.dataset.reportedIndex);
      state.residueSelection={molecule_id:molecule.id,chain_id:button.dataset.reportedChain,sequence_index:state.position};state.screen='W';render();
    }
    else if (button.dataset.sourceEvidence) {
      const evidence=index().get(button.dataset.sourceEvidence),molecule=subjectPath(evidence).find((p)=>p.type==='molecule');
      if (state.screen !== 'R' || !state.selected.includes(molecule.id)) {
        if (!state.selected.includes(molecule.id)) state.selected.push(molecule.id);
        state.screen = 'R';
        render();
      }
      const card = document.getElementById('evidence-' + evidence.id);
      for (let parent = card?.parentElement; parent; parent = parent.parentElement) {
        if (parent.tagName === 'DETAILS') parent.open = true;
      }
      card?.focus({preventScroll:true});
      card?.scrollIntoView({block:'center'});
    }
    else if (button.dataset.designSelected!==undefined) DesignUI.fromSelection();
    else if (button.dataset.expressionDesign) {const id=button.dataset.expressionDesign;if(!state.selected.includes(id))state.selected.push(id);state.expressionMolecule=id;state.expressionLeft=null;state.expressionRight=null;state.expressionCohort=null;state.expressionMaterial=null;state.designTask='expression';state.screen='D';render();}
    else if (button.dataset.restore) { const d = entities("decision").find((e) => e.id === button.dataset.restore); state.selected = [...d.candidate_ids]; state.focus = null; render(); }
    else if (button.id === "back-import") { NumberingImportUI.reset();importEpoch++;pendingImport = null; $("#import-preview").hidden = true; $("#import-form").hidden = false; }
    else if(button.dataset.predictionDownload) PredictionUI.download(button.dataset.predictionDownload);
    else if(button.dataset.numberingDownload) NumberingImportUI.download(button.dataset.numberingDownload);
    else if(button.id==='apply-numbering-bindings'){NumberingImportUI.bind();loading=true;await validateImport();}
    else if(button.id === 'apply-prediction-mappings') {loading=true;await validateImport();}
    else if (button.id === 'apply-measurement-mappings') {loading=true;await validateImport();}
    else if(button.id==='apply-sequence-grouping'){
      sequenceGrouping.assignments=[...document.querySelectorAll('[data-sequence-record]')].map((row)=>({record_index:Number(row.dataset.sequenceRecord),external_id:row.querySelector('[data-group-candidate]').value,chain_id:row.querySelector('[data-group-chain]').value,role:row.querySelector('[data-group-role]').value}));
      sequenceGrouping.format=$('#group-molecular-format').value;loading=true;await validateImport();
    }
    else if (button.id === "commit-import") {
      loading = true; button.disabled = true;
      const pending=pendingImport,ticket=importEpoch,active=bundle?.project.id,scope=JSON.stringify(state);
      ownsError=()=>ticket===importEpoch&&pendingImport===pending&&active===bundle?.project.id&&scope===JSON.stringify(state);
      if(!pending)throw Error('Review the current source before saving.');
      const saved = await api("/api/import", pending);
      if(ticket===importEpoch&&pendingImport===pending&&active===bundle?.project.id&&scope===JSON.stringify(state)){
        $("#import-dialog").close();pendingImport=null;await refreshProjects(saved.project_id);
        if(pending.project.title.startsWith('[SYNTHETIC EXAMPLE]')){state.selected=entities('molecule').map((e)=>e.id);state.focus=state.selected[0];state.screen='W';render();}
        notify(`Saved ${saved.imported} entities. IDs and source metadata were retained.`);
      }else notify(`Saved ${saved.imported} submitted entities. The newer project, selection and import draft were retained.`);
    } else if (["research-example-button", "fixture-button", "composition-fixture-button", "numbering-fixture-button", "structure-fixture-button"].includes(button.id)) {
      if(button.id==='research-example-button')showImport();
      if(importFileRead){importFileRead=null;$('#import-file').value='';}
      const route = {"research-example-button":"/api/example-research", "fixture-button":"/api/example", "composition-fixture-button":"/api/example-composition", "numbering-fixture-button":"/api/example-numbering", "structure-fixture-button":"/api/example-structures"}[button.id];
      const ticket=++importEpoch;const example = await api(route); if(ticket===importEpoch&&$('#import-dialog').open)renderPreview({bundle:example, report:{total_rows:example.entities.length, valid_rows:example.entities.length, excluded:[], duplicates:[], warnings:[]}}, true);
    } else if (button.id === "export-button") {
      // Fetch fresh DB state, rather than exporting a stale tab snapshot.
      const fresh = await api("/api/bundle?project_id=" + encodeURIComponent(bundle.project.id));
      const url = URL.createObjectURL(new Blob([exactBundleJson(fresh)], {type:"application/json"}));
      const a = document.createElement("a"); a.href = url; a.download = "antibody-workspace-" + bundle.project.id + ".json"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } else if (button.id === "review-shortlist") {
      const reason = $("#shortlist-reason").value.trim(); if (!reason) throw new Error("Enter a reason before reviewing the draft.");
      const ids = [...document.querySelectorAll("[data-evidence]:checked")].map((e) => e.dataset.evidence);
      pendingShortlist = {project_id:bundle.project.id, candidate_ids:[...state.selected], evidence_ids:ids, reason};
      pendingShortlistScope=shortlistScope();
      $("#shortlist-preview").innerHTML = `<p class="muted">This saves a draft, not a finalized scientific decision.</p><p>${esc(reason)}</p><p>${state.selected.length} candidate IDs · ${ids.length} evidence records will be frozen</p><pre>${pretty(pendingShortlist)}</pre>`;
      $("#shortlist-dialog").showModal();
    } else if (button.id === "confirm-shortlist") {
      const submitted=pendingShortlist,scope=pendingShortlistScope;
      if(!submitted||scope!==shortlistScope())throw Error('Selection or draft changed. Review the shortlist again before saving.');
      const draft=shortlistDraft(),version=draft.version,submittedBundle=bundle;
      ownsError=()=>scope===shortlistScope()&&pendingShortlist===submitted;
      loading = true; button.disabled = true;
      const saved = await api("/api/shortlist", submitted);
      if(shortlistDrafts.get(scope)===draft&&draft.version===version)shortlistDrafts.delete(scope);
      if(!ownsError())return;
      invalidateShortlistPreview();$("#shortlist-dialog").close();
      ownsError=()=>bundle===submittedBundle&&scope===shortlistScope();
      notify(`Saved shortlist draft ${saved.id}. Refreshing the saved records…`);
      let fresh;
      try {fresh=await api("/api/bundle?project_id=" + encodeURIComponent(submitted.project_id));}
      catch(error){throw Error(`Saved shortlist draft ${saved.id}. Could not refresh the records: ${error.message}. Reopen this project to inspect the saved draft.`);}
      if(bundle!==submittedBundle||scope!==shortlistScope())return;
      bundle=fresh;await refreshNumbering();
      if(bundle.project.id!==submitted.project_id||scope!==shortlistScope())return;
      render();notify(`Saved shortlist draft ${saved.id}. This record and its evidence snapshot are immutable.`);
    } else if (button.id === "help-button") { renderHelp(); $("#help-dialog").showModal(); }
  } catch (error) { if(ownsError())notify(error.message, true); }
  finally { loading = false; if (button.isConnected) button.disabled = false; }
});
document.addEventListener("change", async (event) => {
  const el = event.target;
  let ownsError=()=>true;
  try {
    if (el.dataset.evidence) {const draft=shortlistDraft();if(el.checked)draft.evidenceIds.add(el.dataset.evidence);else draft.evidenceIds.delete(el.dataset.evidence);draft.version++;invalidateShortlistPreview();}
    else if (el.dataset.select) { if (el.checked) {if(!state.selected.includes(el.dataset.select))state.selected.push(el.dataset.select);} else state.selected = state.selected.filter((x) => x !== el.dataset.select); updateExplorerSelection(el); }
    else if (el.dataset.chain) {
      state.chains[el.dataset.chain] = el.value;
      if (state.residueSelection?.molecule_id === el.dataset.chain && state.residueSelection.chain_id !== el.value) {
        state.residueSelection = null;
        state.position = null;
      }
      render();
    }
    else if (el.dataset.chainMap) { if (el.value) state.chainMaps[el.dataset.chainMap] = el.value; else delete state.chainMaps[el.dataset.chainMap]; render(); }
    else if (el.id === 'numbered-region') { state.comparisonRegion = el.value; render(); $('#numbered-region')?.focus({preventScroll:true}); }
    else if (el.dataset.mapChoice) { if (el.value) state.mapChoices[el.dataset.mapChoice] = el.value; else delete state.mapChoices[el.dataset.mapChoice]; await refreshNumbering(); render(); }
    else if (el.id === "group-by") {state.groupBy = el.value;render();}
    else if (el.id === "cdr3-filter") {state.cdr3Group = el.value;render();}
    else if (el.id === "observation-context") {state.observationCohort=el.value||null;state.observationChoices={};await refreshObservations();render();}
    else if (el.id === "comparison-context") {
      state.comparisonContext = el.value || null;
      remember();
      $('#candidate-observations').outerHTML = renderCandidateObservations(selectedEvidence());
      $('#comparison-context')?.focus();
    }
    else if (el.id === "observation-direction") {state.observationDirection=el.value;await refreshObservations();render();}
    else if (el.dataset.observationChoice) {if(el.value)state.observationChoices[el.dataset.observationChoice]=el.value;else delete state.observationChoices[el.dataset.observationChoice];await refreshObservations();render();}
    else if (el.dataset.jump) {
      const molecule = index().get(el.dataset.jump);
      const {chain} = workspaceChain(molecule);
      const position = Number(el.value);
      if (!Number.isInteger(position) || position < 1 || position > chain.sequence.length) throw new Error("Sequence index is outside this chain.");
      selectWorkspaceResidue(molecule.id, chain.id, position, true);
    }
    else if (el.id === "project-select") { await loadProject(el.value); }
    else if(PredictionUI.change(el)){}
    else if (el.id === 'import-target') {importEpoch++;PredictionUI.reset();mappingDraft=null;pendingImport=null;$('#new-project-fields').hidden=!!el.value;updateStructureImport();}
    else if (el.id === 'import-format') {importEpoch++;PredictionUI.reset();mappingDraft=null;pendingImport=null;updateStructureImport();}
    else if (el.hasAttribute('data-measurement-map')) {if(!mappingDraft)return;const ref=mappingDraft.refs[Number(el.dataset.measurementMap)];if(el.value)mappingDraft.choices.set(ref,el.value);else mappingDraft.choices.delete(ref);pendingImport=null;$('#commit-import').disabled=true;}
    else if (el.id === 'import-file') {
      NumberingImportUI.reset();sequenceGrouping=null;
      $("#numbering-tool-version").value = "";
      const file=el.files[0];
      importEpoch++;PredictionUI.reset();mappingDraft=null;pendingImport=null;importFileRead=null;
      // A failed/new file cannot leave the previous file text available for saving.
      $('#import-text').value='';importSourceText=null;
      if(!file)return;
      const reading={};
      importFileRead=reading;
      reading.finished=readImportFile(el,file,reading);
    }
    else if (el.id === "help-language") renderHelp();
  } catch (error) { if(ownsError())notify(error.message, true); }
});
document.addEventListener("input", (event) => {
  if(event.target.id==='shortlist-reason'){const draft=shortlistDraft();draft.reason=event.target.value;draft.version++;invalidateShortlistPreview();}
  if(event.target.closest('#numbering-binding-panel')){importEpoch++;pendingImport=null;}
  if(event.target.closest('#import-form')){NumberingImportUI.reset();importEpoch++;pendingImport=null;if(event.target.id==='import-text'){PredictionUI.reset();mappingDraft=null;importSourceText=null;importFileRead=null;$('#import-file').value='';$("#numbering-tool-version").value="";}}
  if (event.target.id === "candidate-search") {
    state.filter = event.target.value; const pos = event.target.selectionStart; render(); const input = $("#candidate-search"); input.focus(); if (input.type !== "search") input.setSelectionRange(pos, pos);
  }
});
$("#import-form").addEventListener("submit", async (event) => {
  event.preventDefault(); if (loading) return;
  const reading=importFileRead;
  if(reading&&(!await reading.finished||loading||!$('#import-dialog').open||!importSourceText))return;
  loading = true;
  try {
    await validateImport();
  } catch (error) { notify(error.message, true); }
  finally { loading = false; }
});
$('#import-dialog').addEventListener('close',()=>{NumberingImportUI.reset();importEpoch++;PredictionUI.reset();pendingImport=null;mappingDraft=null;if(importFileRead)$('#import-file').value='';importFileRead=null;});
NumberingImportUI.configure({api,bundle:()=>bundle,find:(id)=>index().get(id),esc});
PredictionUI.configure({api,bundle:()=>bundle,find:(id)=>index().get(id),esc,pretty,notify,invalidate(){importEpoch++;pendingImport=null;if($('#commit-import'))$('#commit-import').disabled=true;}});
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
CompositionUI.configure({api,bundle:()=>bundle,state:()=>state,esc,pretty,notify,render,remember,
  async reload(){readyControls(false);StructureUI.dispose();try{bundle=await api('/api/bundle?project_id='+encodeURIComponent(bundle.project.id));await refreshNumbering();}finally{readyControls(true);render();}}
});
ExperimentUI.configure({api,bundle:()=>bundle,state:()=>state,esc,pretty,notify,render,
  async reload(){readyControls(false);StructureUI.dispose();try{bundle=await api('/api/bundle?project_id='+encodeURIComponent(bundle.project.id));await refreshNumbering();}finally{readyControls(true);render();}}
});
DecisionUI.configure({api,bundle:()=>bundle,state:()=>state,esc,pretty,subjectPath,notify,render,
  async reload(){readyControls(false);StructureUI.dispose();try{bundle=await api('/api/bundle?project_id='+encodeURIComponent(bundle.project.id));await refreshNumbering();}finally{readyControls(true);render();}}
});
refreshProjects().catch((error) => notify(error.message, true));
