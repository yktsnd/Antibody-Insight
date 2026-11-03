"use strict";

// F10/F11: explicit, source-numbered designs and retained research questions.
// Scientific coordinate resolution and all persistence constraints live in Python.
const DesignUI = (() => {
  let cfg, cacheBundle, contextCache = new Map(), epoch = 0, hypothesisEpoch = 0, previewEpoch = 0, previewBundle = null, previewKind = null;
  const drafts = new Map(), hypothesisDrafts = new Map();
  const esc = (value) => cfg.esc(value);
  const records = () => cfg.bundle()?.entities || [];
  const find = (id) => records().find((e) => e.id === id);
  const molecules = () => records().filter((e) => e.type === "molecule");
  const maps = () => cfg.maps();
  const state = () => cfg.state();
  const option = (value, label, current, disabled=false) => `<option value="${esc(value)}" ${value===current?'selected':''} ${disabled?'disabled':''}>${esc(label)}</option>`;
  function parent() {return molecules().find((m)=>m.id===state().designParent) || null;}
  function draft() {
    const key=cfg.bundle().project.id+":"+(state().designParent||"");
    if(!drafts.has(key)) drafts.set(key,{changes:[],name:"",external_id:"",reason:"",filter:"",revision:0});
    return drafts.get(key);
  }
  function mapLabel(map) {
    return `${find(map.molecule_id)?.external_id} / ${map.chain_id} / ${map.scheme} / ${map.domain_id} / ${map.status} / ${map.verification.status}`;
  }
  function contextKey() {return JSON.stringify([state().designParent,state().designMap,state().designReferenceMap]);}
  function currentContext() {return contextCache.get(contextKey());}
  function invalidate() {
    epoch++;hypothesisEpoch++;previewEpoch++;previewBundle=null;previewKind=null;hypothesisScope=null;hypothesisDraftKey=null;
    document.querySelector('#design-preview-dialog')?.close();document.querySelector('#hypothesis-dialog')?.close();
  }
  function componentEffects(lineage) {
    const {before,after}=lineage.change_set;
    if(!before.component_graph)return "";
    const affected=new Set(lineage.change_set.mutations.map((m)=>m.chain_id));
    return '<h4>Component and copy effects</h4>'+after.component_graph.chains.filter((c)=>affected.has(c.chain_id)).map((chain)=>{
      const old=before.component_graph.chains.find((c)=>c.chain_id===chain.chain_id);
      return `<p>${esc(chain.chain_id)}: all ${chain.copies} declared copies have the changed chain sequence.</p>`+chain.components.filter((c,i)=>c.sequence!==old.components[i].sequence).map((c,i)=>`<p>${esc(c.id)}: changed segment; ${c.origin===null?'exact child BindingUnit origin unavailable. Parent origin remains in lineage.':'source retained.'}</p>`).join('');
    }).join('');
  }
  function changesTable(mutations, editable=false) {
    if(!mutations.length)return '<p class="muted">No substitutions staged. Choose a mapped coordinate and a target residue.</p>';
    return '<div class="table-wrap"><table><thead><tr><th>Parent chain / scheme / domain</th><th>Coordinate</th><th>Raw index</th><th>Change</th><th>Parent region</th><th>Source</th><th></th></tr></thead><tbody>'+mutations.map((m,i)=>{
      const r=m.request||m;
      return `<tr><td>${esc(m.chain_id)} / ${esc(m.scheme||find(r.parent_map_id)?.scheme)} / ${esc(m.domain_id||find(r.parent_map_id)?.domain_id)}</td><td>${r.number}${esc(r.ins_code)}</td><td>${m.sequence_index}</td><td class="mono">${esc(m.from_aa)} → ${esc(r.to_aa)}</td><td>${esc(m.region)}</td><td><details><summary>Imported map</summary><p>${esc(find(r.parent_map_id)?.source.name)} / ${esc(find(r.parent_map_id)?.source.version||'version unknown')}</p><p class="mono">${esc(r.parent_map_id)}</p>${r.reference_map_id?`<p>Reference map: ${esc(r.reference_map_id)}</p>`:''}</details></td><td>${editable?`<button class="text-button" data-remove-substitution="${i}">Remove</button>`:''}</td></tr>`;
    }).join('')+'</tbody></table></div>';
  }
  function savedDesign() {
    const lineage=find(state().designLineage);
    if(!lineage||lineage.type!=='lineage'||lineage.change_set.kind!=='substitution')return '';
    const p=find(lineage.parent_id),child=find(lineage.child_id);
    return `<section class="panel" id="saved-design"><div class="panel-head"><h2>Saved parent / child design</h2></div><div class="panel-body"><p>${esc(p.external_id)} → ${esc(child.external_id)}</p><p>${esc(lineage.change_set.reason)}</p><p class="muted">Region labels below refer to the imported parent map. Child numbering, structure, measurements and function are not validated by this design.</p>${changesTable(lineage.change_set.mutations)}${componentEffects(lineage)}<button data-inspect-design="${lineage.id}" class="secondary">Inspect parent and child in W</button> <button data-open-hypothesis>Record hypothesis and next experiment</button><details><summary>Exact identities, compositions and mutation records</summary><pre>${cfg.pretty(lineage)}</pre></details></div></section>`;
  }
  function panel() {
    if(!cfg.bundle())return '<div class="panel panel-body"><p>Import a project and choose a parent candidate first.</p></div>';
    if(!find(state().designParent)) {
      state().designParent=state().focus||state().selected[0]||null;
      state().designMap=null;state().designReferenceMap=null;
    }
    const p=parent(),d=draft();
    return `<section class="panel"><div class="panel-head"><h2>Substitution design</h2><button class="secondary" data-open-hypothesis>Record a variant hypothesis</button></div><div class="panel-body"><p class="muted">Choose source-numbered positions, inspect a reference if available, then preview a new child. The parent stays unchanged. No structure, numbering result or measured value is inherited.</p><div class="form-row"><label class="field">Parent candidate<select id="design-parent">${option('','Choose a parent',state().designParent)}${molecules().map((m)=>option(m.id,`${m.external_id} / ${m.name}`,state().designParent)).join('')}</select></label><label class="field">Parent numbering map / chain / domain<select id="design-map">${option('','Choose an imported map explicitly',state().designMap)}${maps().filter((m)=>m.molecule_id===p?.id).map((m)=>option(m.id,mapLabel(m),state().designMap,!m.eligible)).join('')}</select></label></div><label class="field">Optional reference map (researcher-supplied; species is not inferred)<select id="design-reference">${option('','No reference',state().designReferenceMap)}${maps().filter((m)=>m.id!==state().designMap&&m.eligible).map((m)=>option(m.id,mapLabel(m),state().designReferenceMap)).join('')}</select></label><div id="design-coordinate-context">${state().designMap?'Loading source coordinates…':'Numbering unavailable for design until an eligible map is chosen. Failed or unverified maps cannot authorize substitutions.'}</div><h3>Staged substitutions</h3><div id="design-staged">${changesTable(d.changes,true)}</div><div class="form-row"><label class="field">Child name<input id="design-name" value="${esc(d.name)}"></label><label class="field">Child external ID<input id="design-external" value="${esc(d.external_id)}"></label></div><label class="field">Reason for this design<textarea id="design-reason" rows="3">${esc(d.reason)}</textarea></label><button id="preview-variant" ${p?'':'disabled'}>Review child and lineage before saving</button><p class="muted">Staged changes and text stay in memory until explicitly saved. Explicit composition recipes use the Molecular composition task when source parts are available. Physical assembly and construct comparison are not validated here.</p></div></section>${savedDesign()}`;
  }
  function coordinateTable(context) {
    return `<p>${esc(context.comparison_scope)}</p>${context.different_observed_cdr_counts?'<p class="warning">Observed CDR counts differ. Shared labels do not establish equivalent loop geometry or an alignment.</p>':''}<details><summary>Actual map sources and verification</summary><p>Parent: ${esc(context.parent_map.source.name)} / ${esc(context.parent_map.source.version||'version unknown')} / ${esc(context.parent_map.verification.status)}</p><p class="mono">${context.parent_map.id}</p>${context.reference_map?`<p>Reference: ${esc(context.reference_map.source.name)} / ${esc(context.reference_map.source.version||'version unknown')}</p><p class="mono">${context.reference_map.id}</p>`:''}</details><p class="muted">Source-mapped observed residues: ${Object.keys(context.parent_observed_cdr_counts).map((region)=>`${region} parent ${context.parent_observed_cdr_counts[region]} / reference ${context.reference_observed_cdr_counts?context.reference_observed_cdr_counts[region]:"not supplied"}`).join("; ")}. Absent coverage does not imply a deletion.</p><p class="muted">CDR3 source coverage: parent ${context.parent_map.cdr3_complete?"complete observed CDR3":"partial / unavailable"}; reference ${context.reference_map?(context.reference_map.cdr3_complete?"complete observed CDR3":"partial / unavailable"):"not supplied"}.</p><label class="field">Find a recorded coordinate<input id="design-position-filter" value="${esc(draft().filter)}" placeholder="e.g. 111.1; clear to show all"></label><div class="table-wrap design-coordinate-table"><table><thead><tr><th>IMGT coordinate</th><th>Parent region</th><th>Parent raw index / AA</th><th>Reference raw index / AA</th><th>Target AA</th></tr></thead><tbody>${context.rows.map((row)=>{
      const staged=draft().changes.find((m)=>m.request.parent_map_id===context.parent_map.id&&m.request.number===row.number&&m.request.ins_code===row.ins_code);
      return `<tr data-design-coordinate="${esc(row.coordinate)}" ${(!draft().filter.trim()||row.coordinate===draft().filter.trim())?'':'hidden'} class="${row.parent&&row.reference&&row.parent.aa!==row.reference.aa?'coordinate-difference':''}"><td class="mono">${esc(row.coordinate)}</td><td>${esc(row.region)}</td><td>${row.parent?`${row.parent.sequence_index} / <strong>${esc(row.parent.aa)}</strong>`:'mapping unavailable'}</td><td>${row.reference?`${row.reference.sequence_index} / <strong>${esc(row.reference.aa)}</strong>`:'mapping unavailable'}</td><td>${row.parent?`<select data-stage-number="${row.number}" data-stage-insertion="${esc(row.ins_code)}" aria-label="Target AA at ${esc(context.parent_map.chain_id)} IMGT ${esc(row.coordinate)}">${option('','No change',staged?.request.to_aa||'')}${Array.from('ACDEFGHIKLMNPQRSTVWY').map((aa)=>option(aa,aa,staged?.request.to_aa)).join('')}</select>`:'No parent coordinate — no edit'}</td></tr>`;
    }).join('')}</tbody></table></div><p id="design-coordinate-missing" role="status" ${!draft().filter.trim()||context.rows.some((r)=>r.coordinate===draft().filter.trim())?'hidden':''}>No recorded coordinate matches. No neighbour or raw-index fallback.</p>`;
  }
  async function mount() {
    const ticket=++epoch,b=cfg.bundle(),key=contextKey();
    if(!b||!state().designMap)return;
    if(cacheBundle!==b){contextCache.clear();cacheBundle=b;}
    try {
      let context=contextCache.get(key);
      if(!context)context=await cfg.api('/api/design-context',{project_id:b.project.id,parent_id:state().designParent,map_id:state().designMap,reference_map_id:state().designReferenceMap});
      if(ticket!==epoch||cfg.bundle()!==b||contextKey()!==key||state().screen!=='D')return;
      contextCache.set(key,context);
      const host=document.querySelector('#design-coordinate-context');if(host)host.innerHTML=coordinateTable(context);
    } catch(error){if(ticket===epoch&&contextKey()===key&&state().screen==='D'){const host=document.querySelector('#design-coordinate-context');if(host)host.textContent=error.message;cfg.notify(error.message,true);}}
  }
  function ensureDialogs() {
    if(document.querySelector('#design-preview-dialog'))return;
    const holder=document.createElement('div');holder.innerHTML='<dialog id="design-preview-dialog"><div class="dialog-heading"><h2>Review new research records</h2><button data-design-close="design-preview-dialog" class="icon-button" aria-label="Close design preview">×</button></div><div id="design-preview-content"></div><div class="dialog-actions"><button class="secondary" data-design-close="design-preview-dialog">Back</button><button id="save-design-records">Save reviewed records</button></div></dialog><dialog id="hypothesis-dialog"><div class="dialog-heading"><h2>Proposed research hypothesis</h2><button data-design-close="hypothesis-dialog" class="icon-button" aria-label="Close hypothesis">×</button></div><form id="hypothesis-form"><p class="muted">A researcher-authored proposal, not an observation or validated conclusion.</p><div id="hypothesis-targets"></div><label class="field">Hypothesis<textarea id="hypothesis-text" rows="3" required></textarea></label><label class="field">Next experiment or question<textarea id="hypothesis-question" rows="3" required></textarea></label><label class="field">Limitations / what remains unverified<textarea id="hypothesis-limitations" rows="2"></textarea></label><div id="hypothesis-evidence"></div><button type="submit">Review hypothesis before saving</button></form></dialog>';
    document.body.append(...holder.children);
    document.querySelector('#hypothesis-form').addEventListener('submit',previewHypothesis);
    document.querySelector('#hypothesis-dialog').addEventListener('close',()=>{if(!document.querySelector('#hypothesis-dialog').open)hypothesisEpoch++;});
    document.querySelector('#design-preview-dialog').addEventListener('close',()=>{if(!document.querySelector('#design-preview-dialog').open)previewEpoch++;});
  }
  let hypothesisScope=null,hypothesisDraftKey=null;
  function hypothesisContext() {
    const s=state();
    return JSON.stringify([cfg.bundle().project.id,s.screen,s.designTask,s.selected,s.designParent,s.designMap,s.designReferenceMap,
      s.residueSelection,s.observedStructures,s.structureChoices,s.structureModels,s.structureMapChoices,s.structureResidues]);
  }
  async function openHypothesis() {
    ensureDialogs();
    const request=++hypothesisEpoch,project=cfg.bundle().project.id,ticket=epoch,intent=hypothesisContext();document.querySelector('#hypothesis-form').inert=false;
    const ids=[...state().selected];if(state().screen==='D'&&parent()&&!ids.includes(parent().id))ids.push(parent().id);
    if(!ids.length){cfg.notify('Choose the actual hypothesis candidates first.',true);return;}
    const residue=structuredClone(state().residueSelection);
    let structure_refs;
    try{structure_refs=await StructureUI.hypothesisContexts(ids);}catch(error){if(request===hypothesisEpoch&&intent===hypothesisContext())cfg.notify(error.message,true);return;}
    if(request!==hypothesisEpoch||ticket!==epoch||project!==cfg.bundle().project.id||intent!==hypothesisContext())return;
    hypothesisScope={project_id:cfg.bundle().project.id,molecule_ids:ids,residue_refs:residue&&ids.includes(residue.molecule_id)?[{molecule_id:residue.molecule_id,chain_id:residue.chain_id,sequence_index:residue.sequence_index}]:[],structure_refs};
    hypothesisDraftKey=JSON.stringify([hypothesisScope.project_id,[...ids].sort(),hypothesisScope.residue_refs,structure_refs]);
    const savedDraft=hypothesisDrafts.get(hypothesisDraftKey)||{};
    for(const key of ['text','question','limitations'])document.querySelector('#hypothesis-'+key).value=savedDraft[key]||'';
    const lineages=records().filter((e)=>e.type==='lineage'&&ids.includes(e.parent_id)&&ids.includes(e.child_id));
    document.querySelector('#hypothesis-targets').innerHTML=`<p>Related candidates: ${ids.map((id)=>esc(find(id)?.external_id)).join(', ')}</p>${hypothesisScope.residue_refs.length?`<p>Observed sequence position: ${esc(find(residue.molecule_id)?.external_id)} / ${esc(residue.chain_id)} / raw ${residue.sequence_index}</p>`:''}${structure_refs.map((r)=>`<p>Observed structure: ${esc(find(r.structure_id)?.name)} / model ${r.model??'unknown'} / ${r.structure_map_id?esc(r.structure_map_id):'correspondence not selected'}</p>`).join('')}${lineages.map((l)=>`<label class="evidence-check"><input type="checkbox" data-hypothesis-lineage="${l.id}" ${l.id===state().designLineage?'checked':''}> Include design ${esc(find(l.parent_id)?.external_id)} → ${esc(find(l.child_id)?.external_id)}</label>`).join('')}`;
    for(const r of structure_refs)if(r.residue)document.querySelector('#hypothesis-targets').insertAdjacentHTML('beforeend',`<p>Observed source residue: ${esc(StructureUI.sourceLabel(r.residue.source_key))} / alt ${esc(r.residue.altloc??'unknown')}. Coordinate context alone does not establish antibody sequence or measurement attribution.</p>`);
    const evidence=records().filter((e)=>e.type==='evidence'&&cfg.subjectPath(e).some((p)=>p.type==='molecule'&&ids.includes(p.id)));
    document.querySelector('#hypothesis-evidence').innerHTML='<h3>Original evidence to reference</h3>'+evidence.map((e)=>`<label class="evidence-check hypothesis-source"><input type="checkbox" data-hypothesis-evidence="${e.id}"> ${esc(e.kind)} / ${esc(e.metric)} / ${e.value===null?'Value missing':esc(e.value)+' '+esc(e.unit)}<small>${cfg.subjectPath(e).map((p)=>esc(p.type)+': '+esc(p.name)).join(' → ')}<br>${esc(e.source.name)} / ${esc(e.source.version||'version unknown')} / ${esc(e.timestamp)}</small></label>`).join('');
    if(hypothesisScope.residue_refs.length)document.querySelector('#hypothesis-targets').insertAdjacentHTML('beforeend','<label class="evidence-check"><input type="checkbox" id="include-hypothesis-residue" checked> Include the observed sequence position</label>');
    structure_refs.forEach((r,i)=>document.querySelector('#hypothesis-targets').insertAdjacentHTML('beforeend',`<label class="evidence-check"><input type="checkbox" data-hypothesis-structure="${i}" checked> Include ${esc(find(r.structure_id)?.name)} / model ${r.model??'unknown'}</label>`));
    document.querySelector('#hypothesis-dialog').showModal();
  }
  async function previewHypothesis(event) {
    event.preventDefault();
    const form=document.querySelector('#hypothesis-form'),request=++hypothesisEpoch;form.inert=true;
    try {
      if(!hypothesisScope||hypothesisScope.project_id!==cfg.bundle().project.id)throw Error('Hypothesis project context changed. Reopen it explicitly.');
      const {project_id,...scope}=hypothesisScope,ticket=epoch;
      const definition={...scope,text:document.querySelector('#hypothesis-text').value,question:document.querySelector('#hypothesis-question').value,
        limitations:document.querySelector('#hypothesis-limitations').value||null,related_evidence_ids:[...document.querySelectorAll('[data-hypothesis-evidence]:checked')].map((e)=>e.dataset.hypothesisEvidence),lineage_ids:[...document.querySelectorAll('[data-hypothesis-lineage]:checked')].map((e)=>e.dataset.hypothesisLineage)};
      if(!document.querySelector('#include-hypothesis-residue')?.checked)definition.residue_refs=[];
      definition.structure_refs=scope.structure_refs.filter((r,i)=>document.querySelector(`[data-hypothesis-structure="${i}"]`)?.checked);
      const result=await cfg.api('/api/hypothesis-preview',{project_id,definition});
      if(request!==hypothesisEpoch||ticket!==epoch||cfg.bundle().project.id!==project_id||!document.querySelector('#hypothesis-dialog').open)return;
      previewBundle=result;previewKind='hypothesis';
      showPreview(`<p>Proposed hypothesis: ${esc(definition.text)}</p><p>Next question: ${esc(definition.question)}</p><p>Limitations: ${definition.limitations?esc(definition.limitations):'not recorded'}</p><p>Evidence remains on its original subject. No validation or experimental result is created.</p><pre>${cfg.pretty(previewBundle.entities[0])}</pre>`);
    }catch(error){if(request===hypothesisEpoch)cfg.notify(error.message,true);}
    finally{if(request===hypothesisEpoch)form.inert=false;}
  }
  function showPreview(html) {ensureDialogs();previewEpoch++;document.querySelector('#save-design-records').disabled=false;document.querySelector('#design-preview-content').innerHTML=html;document.querySelector('#design-preview-dialog').showModal();}
  function hypothesesPanel() {
    const selected=new Set(state().selected),list=records().filter((e)=>e.type==='hypothesis'&&e.molecule_ids.some((id)=>selected.has(id)));
    return `<section class="panel" id="saved-hypotheses"><div class="panel-head"><h2>Research hypotheses</h2></div><div class="panel-body">${list.length?list.map((h)=>`<article class="saved-hypothesis"><span class="tag">Proposed · not validated</span><p>${esc(h.text)}</p><p><strong>Next experiment / question:</strong> ${esc(h.question)}</p><p>Limitations: ${h.limitations?esc(h.limitations):'not recorded'}</p><p>${h.molecule_ids.map((id)=>esc(find(id)?.external_id)).join(', ')} / ${esc(h.created_at)}</p><details><summary>Related source IDs and observation context</summary><pre>${cfg.pretty(h)}</pre>${h.related_evidence_ids.map((id)=>`<p>${esc(find(id)?.kind)} ${esc(find(id)?.metric)} — ${cfg.subjectPath(find(id)).map((p)=>esc(p.type)+': '+esc(p.name)).join(' → ')}</p>`).join('')}</details></article>`).join(''):'<p class="muted">No saved hypothesis for the selected candidates.</p>'}</div></section>`;
  }
  document.addEventListener('input',(event)=>{
    if(cfg&&hypothesisDraftKey&&['hypothesis-text','hypothesis-question','hypothesis-limitations'].includes(event.target.id)){
      const saved=hypothesisDrafts.get(hypothesisDraftKey)||{};saved[event.target.id.replace('hypothesis-','')]=event.target.value;hypothesisDrafts.set(hypothesisDraftKey,saved);return;
    }
    if(cfg?.bundle()&&event.target.id==='design-position-filter'){
      draft().filter=event.target.value;const rows=[...document.querySelectorAll('[data-design-coordinate]')];rows.forEach((row)=>row.hidden=!!event.target.value.trim()&&row.dataset.designCoordinate!==event.target.value.trim());document.querySelector('#design-coordinate-missing').hidden=rows.some((row)=>!row.hidden)||!event.target.value.trim();return;
    }
    if(!cfg?.bundle()||!['design-name','design-external','design-reason'].includes(event.target.id))return;
    const key={'design-name':'name','design-external':'external_id','design-reason':'reason'}[event.target.id];draft()[key]=event.target.value;draft().revision++;
  });
  document.addEventListener('change',async(event)=>{
    if(!cfg)return;const el=event.target;
    try {
      if(el.id==='design-parent'){state().designParent=el.value||null;state().designMap=null;state().designReferenceMap=null;cfg.render();}
      else if(el.id==='design-map'){state().designMap=el.value||null;state().designReferenceMap=null;draft().filter='';cfg.render();}
      else if(el.id==='design-reference'){state().designReferenceMap=el.value||null;cfg.render();}
      else if(el.dataset.stageNumber){
        const context=currentContext();if(!context)throw Error('Wait for the actual source coordinates.');
        const row=context.rows.find((r)=>r.number===Number(el.dataset.stageNumber)&&r.ins_code===el.dataset.stageInsertion);
        if(!row?.parent)throw Error('Parent coordinate mapping unavailable.');
        const d=draft(),existing=d.changes.findIndex((m)=>m.chain_id===context.parent_map.chain_id&&m.sequence_index===row.parent.sequence_index);
        if(existing>=0&&d.changes[existing].request.parent_map_id!==context.parent_map.id)throw Error('This raw residue is already staged through another map. Remove that change before choosing another map.');
        if(existing>=0)d.changes.splice(existing,1);
        if(el.value&&el.value!==row.parent.aa)d.changes.push({request:{parent_map_id:context.parent_map.id,number:row.number,ins_code:row.ins_code,to_aa:el.value,reference_map_id:state().designReferenceMap},chain_id:context.parent_map.chain_id,sequence_index:row.parent.sequence_index,from_aa:row.parent.aa,region:row.region});
        d.revision++;document.querySelector('#design-staged').innerHTML=changesTable(d.changes,true);
      }
    }catch(error){cfg.notify(error.message,true);}
  });
  document.addEventListener('click',async(event)=>{
    const b=event.target.closest('button');if(!b||b.disabled||!cfg)return;
    let restoreButton=()=>true;
    try {
      if(b.dataset.designClose){if(b.dataset.designClose==='hypothesis-dialog')hypothesisEpoch++;if(b.dataset.designClose==='design-preview-dialog')previewEpoch++;document.querySelector('#'+b.dataset.designClose).close();}
      else if(b.dataset.openHypothesis!==undefined)openHypothesis();
      else if(b.dataset.removeSubstitution!==undefined){draft().changes.splice(Number(b.dataset.removeSubstitution),1);draft().revision++;cfg.render();}
      else if(b.dataset.inspectDesign){const lineage=find(b.dataset.inspectDesign);for(const id of [lineage.parent_id,lineage.child_id])if(!state().selected.includes(id))state().selected.push(id);state().focus=lineage.child_id;state().screen='W';cfg.render();}
      else if(b.id==='preview-variant'){
        b.disabled=true;const d=draft(),projectId=cfg.bundle().project.id,parentId=state().designParent,ticket=epoch,revision=d.revision;
        const result=await cfg.api('/api/variant-preview',{project_id:projectId,parent_id:parentId,name:d.name,external_id:d.external_id,reason:d.reason,substitutions:d.changes.map((m)=>m.request)});
        if(ticket!==epoch||cfg.bundle().project.id!==projectId||state().designParent!==parentId||state().screen!=='D'||d.revision!==revision){cfg.notify('Design context changed while previewing. Review the current changes again.');return;}
        previewBundle=result;previewKind='variant';
        const child=previewBundle.entities[0],lineage=previewBundle.entities[1];
        showPreview(`<p>${esc(parent().external_id)} → ${esc(child.external_id)} / ${esc(child.name)}</p><p>${esc(lineage.change_set.reason)}</p>${changesTable(lineage.change_set.mutations)}${componentEffects(lineage)}<p>Parent unchanged. No inherited Construct, Material, Evidence, Structure or verified numbering. Region labels describe the parent map only.</p><details><summary>Exact records to save</summary><pre>${cfg.pretty(previewBundle)}</pre></details>`);
      }
      else if(b.id==='save-design-records'){
        b.disabled=true;const pending=previewBundle,kind=previewKind;
        if(!pending||pending.project.id!==cfg.bundle()?.project.id)throw Error('Preview context is unavailable. Review the current project again.');
        const submittedPreview=previewEpoch,submittedHypothesis=hypothesisEpoch,submittedHypothesisKey=hypothesisDraftKey;
        const originalDraft=kind==='variant'?drafts.get(pending.project.id+':'+pending.entities[1].parent_id):null;
        const originalRevision=originalDraft?.revision,originalHypothesisText=JSON.stringify(hypothesisDrafts.get(submittedHypothesisKey)||{});
        const ownsPreview=()=>previewEpoch===submittedPreview&&previewBundle===pending;
        restoreButton=ownsPreview;
        document.querySelector('#design-preview-content').insertAdjacentHTML('beforeend','<p role="status">Submitted save in progress…</p>');
        await cfg.api('/api/import',pending);
        // Clear only the exact unchanged draft that was submitted, never the active draft.
        if(originalDraft&&originalDraft.revision===originalRevision)originalDraft.changes=[];
        if(kind==='hypothesis'&&JSON.stringify(hypothesisDrafts.get(submittedHypothesisKey)||{})===originalHypothesisText&&
           (submittedHypothesisKey!==hypothesisDraftKey||submittedHypothesis===hypothesisEpoch))hypothesisDrafts.delete(submittedHypothesisKey);
        const owned=ownsPreview();
        if(owned){previewBundle=null;previewEpoch++;document.querySelector('#design-preview-dialog').close();}
        if(cfg.bundle()?.project.id!==pending.project.id){cfg.notify('Records saved in the original project. Current project selection was retained.');return;}
        const currentVariant=owned&&kind==='variant'&&state().designParent===pending.entities[1].parent_id&&originalDraft?.revision===originalRevision;
        const currentHypothesis=owned&&kind==='hypothesis'&&submittedHypothesis===hypothesisEpoch;
        if(currentVariant){const [child,lineage]=pending.entities;state().designLineage=lineage.id;for(const id of [lineage.parent_id,child.id])if(!state().selected.includes(id))state().selected.push(id);}
        else if(currentHypothesis){document.querySelector('#hypothesis-dialog').close();for(const id of pending.entities[0].molecule_ids)if(!state().selected.includes(id))state().selected.push(id);}
        await cfg.reload();cfg.notify(currentVariant?'Saved a new child and exact substitution lineage. Parent evidence remains on its original Material.':currentHypothesis?'Saved proposed hypothesis with original evidence and observation context.':'Submitted records saved. The current research selection and newer draft were retained.');
      }
    }catch(error){cfg.notify(error.message,true);}
    finally{if(b?.isConnected&&restoreButton())b.disabled=false;}
  });
  function fromSelection() {
    const selection=state().residueSelection;if(!selection){cfg.notify('Select an actual sequence residue in W first.',true);return;}
    const candidates=maps().filter((m)=>m.molecule_id===selection.molecule_id&&m.chain_id===selection.chain_id);
    const chosen=candidates.find((m)=>m.id===state().chainMaps[selection.molecule_id+'|'+selection.chain_id])||(candidates.length===1?candidates[0]:null);
    if(!chosen?.eligible||!chosen.entries.some((e)=>e.sequence_index===selection.sequence_index)){cfg.notify('Choose an eligible source map covering this residue; no map or neighbour is inferred.',true);return;}
    state().designParent=selection.molecule_id;state().designMap=chosen.id;state().designReferenceMap=null;
    const entry=chosen.entries.find((e)=>e.sequence_index===selection.sequence_index);draft().filter=entry.coordinate;
    state().designTask='substitution';state().screen='D';cfg.render();
  }
  return {configure(options){cfg=options;},panel,mount,hypothesesPanel,fromSelection,invalidate};
})();
