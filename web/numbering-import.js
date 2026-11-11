"use strict";

window.NumberingImportUI = (() => {
  let cfg;
  let draft = null;
  const query = (selector) => document.querySelector(selector);
  const reset = () => { draft = null; };

  async function preview(request, current) {
    if (!request.project_id) throw Error("Register the candidate chains in a project first.");
    const version = query("#numbering-tool-version").value.trim() || null;
    const scope = [request.project_id, request.filename, request.text, version];
    const previous = draft?.scope.every((value, index) => value === scope[index]) ? draft : null;
    const result = await cfg.api("/api/numbering-file-preview", {
      project_id: request.project_id,
      text: request.text,
      filename: request.filename,
      version,
      bindings: previous?.bindings || [],
      bindings_text_sha256: previous?.digest || null
    });
    if (!current()) return null;
    if (!previous) {
      const target = cfg.bundle()?.project.id === request.project_id
        ? cfg.bundle()
        : await cfg.api("/api/bundle?project_id=" + encodeURIComponent(request.project_id));
      if (!current()) return null;
      const targets = new Map();
      for (const molecule of target.entities.filter((entity) => entity.type === "molecule")) {
        for (const chain of molecule.chains) {
          const label = `${molecule.external_id} / ${chain.id} (${targets.size + 1})`;
          targets.set(label, {molecule_id: molecule.id, chain_id: chain.id});
        }
      }
      draft = {scope, targets, bindings: [], digest: result.report.text_sha256};
    }
    return result;
  }

  function panel(report, bundle) {
    if (report.kind !== "anarci_text") return "";
    const esc = cfg.esc;
    const domains = report.numbering_domains;
    if (!domains.length) {
      const maps = bundle.entities.filter((entity) => entity.type === "residue_map");
      if (!maps.length) return '<p>No numbered domains are available in this file.</p>';
      const names = new Map([...draft.targets].map(([label, target]) =>
        [JSON.stringify([target.molecule_id, target.chain_id]), label]));
      return `<h3>Review numbering assignments</h3><table>
        <thead><tr><th>Source record and domain</th><th>Target chain</th><th>Raw interval</th><th>Verification</th></tr></thead>
        <tbody>${maps.map((map) => {
          const target = names.get(JSON.stringify([map.molecule_id, map.chain_id]));
          return `<tr><td>${esc(map.domain_id)}</td><td>${esc(target)}</td><td>${map.sequence_start}–${map.sequence_end}</td><td>${esc(map.verification.status)}</td></tr>`;
        }).join("")}</tbody></table>`;
    }
    const rows = domains.map((domain) => `<tr><td>${esc(domain.record_name)} · record ${domain.record_index + 1}, domain ${domain.domain_index}</td>
      <td>${esc(domain.source_chain_type)} · ${domain.sequence_start}–${domain.sequence_end}</td>
      <td><input list="numbering-target-chains" data-numbering-record="${domain.record_index}" data-numbering-domain="${domain.domain_index}"
        aria-label="Target for record ${domain.record_index + 1} domain ${domain.domain_index}"></td></tr>`).join("");
    return `<section id="numbering-binding-panel"><h3>Bind numbered domains to registered chains</h3>
      <p>Choose the exact candidate and chain for each domain you want to import.</p>
      <datalist id="numbering-target-chains">${[...draft.targets.keys()].map((label) => `<option value="${esc(label)}"></option>`).join("")}</datalist>
      <table><thead><tr><th>ANARCI record</th><th>Source chain and raw interval</th><th>Target chain</th></tr></thead><tbody>${rows}</tbody></table>
      <details><summary>Record an existing scientific review</summary>
        <label class="evidence-check"><input id="numbering-reviewed" type="checkbox"> The review covers the assigned domains and target chains</label>
        <div class="form-row">
          <label class="field">Reviewer<input id="numbering-reviewer" maxlength="500"></label>
          <label class="field">Review timestamp<input id="numbering-review-time" placeholder="ISO 8601 with timezone"></label>
          <label class="field">Review reference<input id="numbering-review-reference"></label>
        </div>
      </details>
      <button id="apply-numbering-bindings">Review numbering assignments</button></section>`;
  }

  function bind() {
    if (!draft) throw Error("Preview the numbering file first.");
    const verified = query("#numbering-reviewed").checked;
    const verification = {
      status: verified ? "source_verified" : "unverified",
      reviewer: verified ? query("#numbering-reviewer").value.trim() : null,
      reviewed_at: verified ? query("#numbering-review-time").value.trim() : null,
      reference: verified ? query("#numbering-review-reference").value.trim() : null
    };
    const bindings = [];
    for (const input of document.querySelectorAll("[data-numbering-domain]")) {
      if (!input.value) continue;
      const target = draft.targets.get(input.value);
      if (!target) throw Error("Choose a registered candidate and chain from the list.");
      bindings.push({...target, record_index: Number(input.dataset.numberingRecord),
        domain_index: Number(input.dataset.numberingDomain), verification});
    }
    if (!bindings.length) throw Error("Assign at least one numbered domain.");
    draft.bindings = bindings;
  }

  function origin(map) {
    const ref = map.numbering_origin;
    if (!ref) return "";
    const file = cfg.find(ref.file_id);
    if (!file || file.type !== "numbering_file") return "";
    return `<p>${cfg.esc(file.name)} · record ${ref.record_index + 1}, domain ${ref.domain_index}<br>
      <span class="mono">${cfg.esc(file.sha256)}</span></p>
      <button class="secondary" data-numbering-download="${cfg.esc(file.id)}">Download original ANARCI output</button>`;
  }

  function download(id) {
    const file = cfg.find(id);
    if (!file || file.type !== "numbering_file") return;
    const url = URL.createObjectURL(new Blob([file.content], {type: "text/plain;charset=utf-8"}));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = file.name;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return {configure(options) { cfg = options; }, reset, preview, panel, bind, origin, download};
})();
