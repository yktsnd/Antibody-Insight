"use strict";

// Local coordinate display. All correspondence decisions are validated by the domain API.
window.StructureUI = (() => {
  let cfg, generation = 0, editor = null, previewBundle = null, cachedBundle = null;
  const live = new Map(), cache = new Map();
  const escape = (v) => String(v ?? "").replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const key = (object, names) => JSON.stringify(names.map((name)=>object[name]));
  const chainKey = (c) => key(c,["model","auth_chain","label_asym","segment"]);
  const residueKey = (r) => key(r,["model","auth_chain","label_asym","segment","auth_number","label_number","insertion_code","residue_name"]);
  const sourceLabel = (r) => `model ${r.model??"unknown"} / author ${r.auth_chain ?? "unknown"}:${r.auth_number ?? "?"}${r.insertion_code ?? "?"} / label ${r.label_asym ?? "unknown"}:${r.label_number ?? "?"} / segment ${r.segment === null ? "unknown" : r.segment || "blank"} / ${r.residue_name}`;
  const state = () => cfg.state();
  const option = (value,label,chosen) => `<option value="${escape(value)}" ${String(value)===String(chosen)?"selected":""}>${escape(label)}</option>`;
  function choices(molecule) {return cfg.bundle()?.entities.filter((e)=>e.type==="structure" && e.molecule_id===molecule.id) || [];}
  function panel(molecule) {
    const list=choices(molecule), selected=state().structureChoices[molecule.id] || (list.length===1?list[0].id:"");
    return `<section class="structure-section" data-structure-molecule="${molecule.id}"><p class="section-label">LOCAL STRUCTURAL OBSERVATION</p>${list.length ? `<label class="field">Coordinate source<select data-coordinate-choice="${molecule.id}" aria-label="Structure for ${escape(molecule.external_id)}">${option("","Choose coordinate source",selected)}${list.map((s)=>option(s.id,`${s.name} / ${s.origin_kind}`,selected)).join("")}</select></label><div class="structure-mount" data-structure-host="${molecule.id}">${selected?"Loading local coordinates…":"No structure chosen; no implicit first match."}</div>` : '<p class="muted">Structure: not registered. Import a local PDB/mmCIF and explicitly assign its molecule and correspondence.</p>'}</section>`;
  }
  function dispose() {
    generation++;
    for(const context of live.values()) {
      try {state().structureViews[context.viewKey]=context.viewer.getView();context.viewer.clear();
        const canvas=context.host.querySelector('canvas');const gl=canvas?.getContext('webgl2') || canvas?.getContext('webgl');gl?.getExtension('WEBGL_lose_context')?.loseContext();
      } catch { /* The detached view may already have released its resources. */ }
    }
    live.clear();
  }
  async function load(id,mapId) {
    if(cachedBundle!==cfg.bundle()){cache.clear();cachedBundle=cfg.bundle();}
    const project=cfg.bundle().project.id, cacheKey=project+":"+id+":"+(mapId||"");
    if(!cache.has(cacheKey)) cache.set(cacheKey,await cfg.api('/api/structure-view?project_id='+encodeURIComponent(project)+'&structure_id='+encodeURIComponent(id)+(mapId?'&map_id='+encodeURIComponent(mapId):'')));
    return cache.get(cacheKey);
  }
  function confidence(data, model) {
    const scoped=data.confidence.filter((e)=>e.conditions?.structure_model===model);
    const unspecified=data.confidence.filter((e)=>e.conditions?.structure_model===undefined);
    const record=(e,label)=>`<p class="muted">${escape(e.metric)}: ${e.value===null?"missing":escape(e.value)} ${escape(e.unit)} / ${label}<br>Source: ${escape(e.source.name)} / ${escape(e.source.version||"version unknown")} / ${escape(e.timestamp)}</p>`;
    return `<div class="struct-confidence"><h3>Model-internal computed metrics</h3><p class="muted">These are not measured binding affinity. B-values are not relabeled as confidence.</p>${scoped.length?scoped.map((e)=>record(e,`declared model ${model}`)).join(""):'<p class="muted">No model-scoped confidence registered.</p>'}${unspecified.map((e)=>record(e,"model scope unspecified / file-level")).join("")}</div>`;
  }
  async function mount() {
    const tick=generation;
    for(const host of document.querySelectorAll('[data-structure-host]')) {
      const molecule=cfg.bundle().entities.find((e)=>e.id===host.dataset.structureHost), list=choices(molecule);
      const sid=state().structureChoices[molecule.id] || (list.length===1?list[0].id:null);if(!sid)continue;
      try {
        let data=await load(sid,null);if(tick!==generation || !host.isConnected)return;
        const modelChoice=state().structureModels[sid] || (data.parsed.models.length===1?(data.parsed.models[0]??'unknown'):null);
        const model=modelChoice==='unknown'?null:modelChoice;
        const available=cfg.bundle().entities.filter((e)=>e.type==='structure_map'&&e.structure_id===sid&&e.chain_assignments.some((a)=>a.model===model));
        const viewKey=sid+":"+modelChoice, mapId=state().structureMapChoices[viewKey] || (available.length===1?available[0].id:null);
        if(mapId) data=await load(sid,mapId);
        if(tick!==generation || !host.isConnected)return;
        host.innerHTML=`<div class="form-row"><label class="field">Source model<select data-coordinate-model="${sid}" aria-label="Source model for ${escape(molecule.external_id)}">${option("","Choose a source model",model)}${data.parsed.models.map((m)=>option(m??'unknown',m===null?'Model unknown (source omitted ID)':`Model ${m}`,modelChoice)).join("")}</select></label><label class="field">Correspondence<select data-coordinate-map="${escape(viewKey)}" aria-label="Correspondence for ${escape(molecule.external_id)}">${option("","No map selected",mapId)}${available.map((m)=>option(m.id,`${m.source.name} / ${m.id.slice(-8)}`,mapId)).join("")}</select></label></div><p class="muted">${escape(data.structure.name)} · ${escape(data.structure.origin_kind)} · ${escape(data.parsed.parser.name)} ${escape(data.parsed.parser.version)}<br>Source: ${escape(data.structure.source.name)} / ${escape(data.structure.source.version||"version unknown")}</p>${modelChoice?`<label class="evidence-check"><input type="checkbox" data-link-views ${state().linkStructureViews?"checked":""}> Link orientation &amp; zoom (independent centers; no superposition)</label><div class="coordinate-canvas" id="coordinate-${molecule.id}" aria-label="Interactive structure for ${escape(molecule.external_id)}"></div><p class="structure-selection muted" role="status">Choose an atom or a mapped sequence position.</p><details><summary>Selected residue source atom fields</summary><div class="source-atom-details muted">No mapped residue selected.</div></details><button class="secondary" data-edit-correspondence="${molecule.id}" ${model===null?'disabled':''}>Create correspondence revision</button><div class="declared-struct-chains">${data.map?data.map.chain_assignments.filter((a)=>a.model===model).map((a)=>`<p class="muted">${escape(a.role)}: author ${escape(a.auth_chain??"unknown")} / label ${escape(a.label_asym??"unknown")} / segment ${escape(a.segment===null?"unknown":a.segment||"blank")} → ${a.molecule_chain_id?escape(a.molecule_chain_id):a.target_ref?escape(a.target_ref.namespace+":"+a.target_ref.identifier):"unassigned"}</p>`).join(""):'<p class="muted">Correspondence unavailable. No sequence identity is inferred.</p>'}</div>${confidence(data,model)}<details><summary>Source digest, mapping IDs and actual coordinates</summary><p class="mono">${sid}<br>${escape(data.structure.sha256)}<br>${mapId||"No correspondence chosen"}</p><p class="muted">Cartesian coordinates use Å. All supplied alternate locations are displayed. Mapping chooses an explicit conformer. Spheres/cartoon are viewer representations, not proof of bonds or secondary structure.</p></details>`:'<p class="muted">Choose a source model before observing coordinates. No first-model fallback.</p>'}`;
        if(!modelChoice)continue;
        const element=host.querySelector('.coordinate-canvas');
        const viewer=$3Dmol.createViewer(element,{backgroundColor:'#f6f9fa',antialias:true});
        const assignment=new Map((data.map?.chain_assignments||[]).map((a)=>[chainKey(a),a]));
        const colors={antibody:'#237d85',antigen:'#bd8c3a',other:'#849ba5'};
        const atoms=data.parsed.atoms.filter((a)=>a.model===model).map((a)=>({x:a.x,y:a.y,z:a.z,elem:a.element||'X',atom:a.atom_name,resn:a.residue_name,
          resi:Number(a.residue_uid.split('-')[1]),chain:chainKey(a),serial:a.index+1,ss:'c',color:colors[assignment.get(chainKey(a))?.role]||'#899aa5',
          properties:{sourceIndex:a.index,residueUid:a.residue_uid,altloc:a.altloc}}));
        const glModel=viewer.addModel();glModel.addAtoms(atoms);viewer.setStyle({},{sphere:{radius:.55}});
        const context={viewer,glModel,host,molecule,data,model,viewKey,atoms};live.set(molecule.id,context);
        viewer.setClickable({},true,(atom)=>selectAtom(context,atom));viewer.zoomTo();
        const saved=state().structureViews[viewKey];
        if(Array.isArray(saved)&&saved.length===8&&saved.every(Number.isFinite))viewer.setView(saved);
        else if(state().linkStructureViews) {const other=[...live.values()].find((c)=>c!==context);if(other){const own=viewer.getView();viewer.setView([...own.slice(0,3),...other.viewer.getView().slice(3)]);}}
        viewer.setViewChangeCallback(()=>cameraChanged(context));viewer.render();highlight(context);
      } catch(error) {host.textContent='Structure observation unavailable: '+error.message;cfg.notify(error.message,true);}
    }
  }
  let synchronizing=false;
  function cameraChanged(context) {
    if(synchronizing)return;
    const view=context.viewer.getView();state().structureViews[context.viewKey]=view;
    if(state().linkStructureViews) {
      synchronizing=true;
      for(const other of live.values()) if(other!==context) {const current=other.viewer.getView();const next=[...current.slice(0,3),...view.slice(3)];other.viewer.setView(next);other.viewer.render();state().structureViews[other.viewKey]=next;}
      synchronizing=false;
    }
    cfg.remember();
  }
  function highlight(context) {
    context.viewer.setStyle({},{sphere:{radius:.55}});
    const selection=state().residueSelection;
    const entry=selection?.molecule_id===context.molecule.id ? context.data.map?.residues.find((e)=>e.status==='mapped'&&e.chain_id===selection.chain_id&&e.sequence_index===selection.sequence_index&&e.structure_residue.model===context.model):null;
    let atoms=[];
    if(entry) atoms=context.data.parsed.atoms.filter((a)=>residueKey(a)===residueKey(entry.structure_residue)&&(a.altloc===''||a.altloc===entry.altloc));
    if(atoms.length) {context.viewer.setStyle({serial:atoms.map((a)=>a.index+1)},{sphere:{radius:.85,color:'#cf733b'}});context.host.querySelector('.structure-selection').textContent=`Mapped ${entry.chain_id} raw index ${entry.sequence_index} ↔ ${sourceLabel(entry.structure_residue)} / conformer ${entry.altloc||'common'}`;}
    else if(selection?.molecule_id===context.molecule.id) context.host.querySelector('.structure-selection').textContent='Mapping unavailable for this sequence position; no other residue was highlighted.';
    const details=context.host.querySelector('.source-atom-details');
    if(details)details.innerHTML=atoms.length?atoms.map((a)=>`<p>${escape(a.atom_name)} / alt ${escape(a.altloc??'unknown')} / (${a.x}, ${a.y}, ${a.z}) Å<br>Source occupancy: ${a.occupancy??'unknown'} / source B-field (uninterpreted): ${a.b_value??'unknown'}</p>`).join(''):'No mapped source atom fields; no adjacent residue substituted.';
    context.viewer.render();
  }
  function selectAtom(context,atom) {
    const source=context.data.parsed.atoms.find((a)=>a.index===atom.properties.sourceIndex);
    const entry=context.data.map?.residues.find((e)=>e.status==='mapped'&&residueKey(e.structure_residue)===residueKey(source)&&(source.altloc===''||source.altloc===e.altloc));
    state().structureResidues[context.viewKey]={residue_uid:source.residue_uid,altloc:source.altloc};
    if(entry) cfg.focusSequence({molecule_id:context.molecule.id,chain_id:entry.chain_id,sequence_index:entry.sequence_index});
    else {state().residueSelection=null;state().position=null;cfg.remember();cfg.render();cfg.notify(`Structure selection is unmapped: ${sourceLabel(source)} / alt ${source.altloc??'unknown'}. No sequence residue was selected.`);}
  }
  function editorRows() {
    const context=editor.context, molecule=context.molecule;
    const rows=editor.definition.chain_assignments.map((a,i)=>`<div class="map-chain-row" data-assignment-row="${i}"><p class="mono">model ${a.model} / author ${escape(a.auth_chain??"unknown")} / label ${escape(a.label_asym??"unknown")} / segment ${escape(a.segment===null?"unknown":a.segment||"blank")}</p><div class="form-row"><label class="field">Declared role<select data-map-role="${i}">${['antibody','antigen','other'].map((r)=>option(r,r,a.role)).join('')}</select></label><label class="field">Molecule chain (antibody only)<select data-map-chain="${i}">${option('', 'Not assigned',a.molecule_chain_id)}${molecule.chains.map((c)=>option(c.id,c.id,a.molecule_chain_id)).join('')}</select></label></div><div class="form-row"><label class="field">Target namespace (antigen only)<input data-target-namespace="${i}" value="${escape(a.target_ref?.namespace||'')}"></label><label class="field">Target identifier<input data-target-identifier="${i}" value="${escape(a.target_ref?.identifier||'')}"></label></div></div>`).join('');
    return rows;
  }
  function openEditor(context) {
    document.querySelector('#structure-map-dialog')?.remove();previewBundle=null;
    const existing=context.data.map;
    editor={context,definition:{structure_id:context.data.structure.id,molecule_id:context.molecule.id,source:{name:'Local researcher correspondence',version:null},
      chain_assignments:existing?structuredClone(existing.chain_assignments.filter((a)=>a.model===context.model)):context.data.parsed.chains.filter((c)=>c.model===context.model).map((c)=>({...c,role:'other',molecule_chain_id:null,target_ref:null,label:'Explicit source chain'})),
      residues:existing?structuredClone(existing.residues.filter((e)=>e.status==='unavailable'||e.structure_residue.model===context.model)):[]}};
    const dialog=document.createElement('dialog');dialog.id='structure-map-dialog';
    dialog.innerHTML=`<div class="dialog-heading"><h2>Explicit chain &amp; residue correspondence</h2><button class="icon-button" data-map-close aria-label="Close correspondence editor">×</button></div><p class="muted">This creates a new immutable map. No alignment or pairing is inferred. Review all assignments before saving.</p><div id="map-edit-fields">${editorRows()}<h3>Explicit residue pair</h3><div class="form-row"><label class="field">Molecule chain<select id="map-pair-chain">${context.molecule.chains.map((c)=>option(c.id,c.id,c.id===state().chains[context.molecule.id]?c.id:null)).join('')}</select></label><label class="field">Raw sequence index<input id="map-pair-index" type="number" min="1" value="${state().residueSelection?.sequence_index||1}"></label></div><label class="field">Actual source residue<select id="map-pair-residue">${option('','No coordinate selected','')}${context.data.parsed.residues.filter((r)=>r.model===context.model).map((r)=>option(r.uid,sourceLabel(r),null)).join('')}</select></label><label class="field">Explicit alternate conformer<select id="map-pair-alt"><option value="">Common / no alternate</option></select></label><label class="field">Unavailable reason (only when no source residue selected)<input id="map-pair-reason" placeholder="Why are coordinates unavailable?"></label><button class="secondary" data-map-add-pair>Add / replace explicit pair</button><div id="map-pair-list"></div><div class="dialog-actions"><button data-map-preview>Validate &amp; review new map</button></div></div><div id="map-review" hidden></div>`;
    document.body.append(dialog);renderPairs();dialog.showModal();
  }
  function renderPairs() {document.querySelector('#map-pair-list').innerHTML=editor.definition.residues.map((e,i)=>`<p class="muted">${escape(e.chain_id)} index ${e.sequence_index} → ${e.status==='mapped'?escape(sourceLabel(e.structure_residue))+' / alt '+escape(e.altloc||'common'):'unavailable: '+escape(e.reason)} <button class="text-button" data-map-remove="${i}">Remove pair</button></p>`).join('');}
  async function click(event) {
    const b=event.target.closest('button');if(!b||!cfg)return;
    try {
      if(b.dataset.editCorrespondence)openEditor(live.get(b.dataset.editCorrespondence));
      else if(b.hasAttribute('data-map-close'))document.querySelector('#structure-map-dialog').close();
      else if(b.hasAttribute('data-map-remove')){editor.definition.residues.splice(Number(b.dataset.mapRemove),1);renderPairs();}
      else if(b.hasAttribute('data-map-add-pair')) {
        const chain_id=document.querySelector('#map-pair-chain').value, sequence_index=Number(document.querySelector('#map-pair-index').value), uid=document.querySelector('#map-pair-residue').value;
        const residue=editor.context.data.parsed.residues.find((r)=>r.uid===uid), names=['model','auth_chain','label_asym','segment','auth_number','label_number','insertion_code','residue_name'];
        const entry={chain_id,sequence_index,status:residue?'mapped':'unavailable',structure_residue:residue?Object.fromEntries(names.map((n)=>[n,residue[n]])):null,
          altloc:residue?document.querySelector('#map-pair-alt').value:'',reason:residue?null:document.querySelector('#map-pair-reason').value};
        editor.definition.residues=editor.definition.residues.filter((e)=>e.chain_id!==chain_id||e.sequence_index!==sequence_index);editor.definition.residues.push(entry);renderPairs();
      } else if(b.hasAttribute('data-map-preview')) {
        for(const [i,a] of editor.definition.chain_assignments.entries()) {a.role=document.querySelector(`[data-map-role="${i}"]`).value;a.molecule_chain_id=a.role==='antibody'?document.querySelector(`[data-map-chain="${i}"]`).value:null;
          a.target_ref=a.role==='antigen'?{namespace:document.querySelector(`[data-target-namespace="${i}"]`).value,identifier:document.querySelector(`[data-target-identifier="${i}"]`).value}:null;}
        previewBundle=await cfg.api('/api/structure-map-preview',{project_id:cfg.bundle().project.id,definition:editor.definition});
        document.querySelector('#map-edit-fields').hidden=true;const review=document.querySelector('#map-review');review.hidden=false;
        review.innerHTML=`<h3>Review new immutable map</h3><p class="muted">${editor.definition.chain_assignments.length} declared chains / ${editor.definition.residues.length} explicit residue states. Existing maps and evidence remain unchanged.</p><pre>${escape(JSON.stringify(previewBundle.entities[0],null,2))}</pre><div class="dialog-actions"><button class="secondary" data-map-back>Back to assignments</button><button data-map-save>Save correspondence</button></div>`;
      } else if(b.hasAttribute('data-map-back')){document.querySelector('#map-edit-fields').hidden=false;document.querySelector('#map-review').hidden=true;previewBundle=null;}
      else if(b.hasAttribute('data-map-save')) {
        b.disabled=true;await cfg.api('/api/import',previewBundle);state().structureMapChoices[editor.context.viewKey]=previewBundle.entities[0].id;
        document.querySelector('#structure-map-dialog').close();cache.clear();await cfg.reload();cfg.notify('Saved explicit correspondence as a new immutable map. No alignment or prediction was performed.');
      }
    }catch(error){cfg.notify(error.message,true);if(b.isConnected)b.disabled=false;}
  }
  async function change(event) {
    const e=event.target;if(!cfg)return;
    if(e.dataset.coordinateChoice){state().structureChoices[e.dataset.coordinateChoice]=e.value;cfg.render();}
    else if(e.dataset.coordinateModel){if(e.value)state().structureModels[e.dataset.coordinateModel]=e.value==='unknown'?'unknown':Number(e.value);else delete state().structureModels[e.dataset.coordinateModel];cfg.render();}
    else if(e.dataset.coordinateMap){if(e.value)state().structureMapChoices[e.dataset.coordinateMap]=e.value;else delete state().structureMapChoices[e.dataset.coordinateMap];cfg.render();}
    else if(e.hasAttribute('data-link-views')){state().linkStructureViews=e.checked;document.querySelectorAll('[data-link-views]').forEach((control)=>{control.checked=e.checked;});const first=live.values().next().value;if(first)cameraChanged(first);}
    else if(e.id==='map-pair-residue'){const r=editor.context.data.parsed.residues.find((r)=>r.uid===e.value);const alts=r?.altlocs.filter((a)=>a!==''&&a!==null)||[];
      document.querySelector('#map-pair-alt').innerHTML=alts.length?option('','Choose a supplied alternate','')+alts.map((a)=>option(a,a,null)).join(''):option('','Common / no alternate','');}
  }
  document.addEventListener('click',click);document.addEventListener('change',change);
  return {configure(options){cfg=options;},panel,mount,dispose,viewerFor(id){return live.get(id)?.viewer;},contextFor(id){return live.get(id);}};
})();
