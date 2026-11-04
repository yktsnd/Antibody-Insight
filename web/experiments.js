"use strict";

// F17/F18: declared expression designs and original per-Material observations.
const ExperimentUI = (() => {
  let cfg, cacheBundle, contexts=new Map(), request=0, contextRequest=0, preview=null, revision=0;
  const drafts=new Map();
  const records=()=>cfg.bundle()?.entities||[], state=()=>cfg.state(), esc=(v)=>cfg.esc(v);
  const find=(id)=>records().find((e)=>e.id===id);
  function molecule(){
    const s=state();
    return records().find((e)=>e.type==='molecule'&&e.id===s.expressionMolecule&&s.selected.includes(e.id))||
      records().find((e)=>e.type==='molecule'&&e.id===s.focus&&s.selected.includes(e.id))||
      records().find((e)=>e.type==='molecule'&&s.selected.includes(e.id));
  }
  const option=(value,label,current)=>`<option value="${esc(value)}" ${value===current?'selected':''}>${esc(label)}</option>`;
  function key(){return JSON.stringify([cfg.bundle()?.project.id,molecule()?.id,state().expressionLeft,state().expressionRight,state().expressionCohort]);}
  function intent(){return JSON.stringify([key(),state().screen,state().designTask,state().selected,state().expressionMaterial]);}
  function context(){return cacheBundle===cfg.bundle()?contexts.get(key()):null;}
  function draft(kind){const id=cfg.bundle().project.id+':'+molecule().id+':'+kind;if(!drafts.has(id))drafts.set(id,{});return drafts.get(id);}
  function invalidate(){request++;contextRequest++;preview=null;document.querySelector('#metadata-preview-dialog')?.close();}
  function choices(){
    const m=molecule();if(!m)return '<p class="muted">Select a candidate to inspect its actual Constructs and Materials.</p>';
    return `<label class="field">Expression Molecule<select id="expression-molecule">${records().filter((e)=>e.type==='molecule'&&state().selected.includes(e.id)).map((e)=>option(e.id,`${e.external_id} / ${e.id}`,m.id)).join('')}</select></label>`;
  }
  function metadataForm(kind){
    const d=draft(kind),m=molecule(),constructs=records().filter((e)=>e.type==='construct'&&e.molecule_id===m.id);
    const input=(name,label,area=false)=>`<label class="field">${label}${area?`<textarea data-metadata-field="${name}" rows="3">${esc(d[name]||'')}</textarea>`:`<input data-metadata-field="${name}" value="${esc(d[name]||'')}">`}</label>`;
    return `<details><summary>Register a ${kind==='construct'?'Construct':'Material'} explicitly</summary><form data-metadata-form="${kind}">${input('name','Record name')}${kind==='construct'?input('cds','Recorded CDS (uppercase ACGTN; empty = unknown)',true)+input('vector','Recorded vector (empty = unknown)')+input('signal_peptide','Recorded signal peptide metadata (empty = unknown)'):`<label class="field">Actual Construct<select data-metadata-field="construct_id"><option value="">Choose a Construct ID</option>${constructs.map((c)=>option(c.id,`${c.name} / ${c.id}`,d.construct_id)).join('')}</select></label>${input('lot','Actual batch / lot (required)')}`}<p class="muted">Declared association to ${esc(m.id)}. No translation, chain/CDS assignment, signal processing or expression is validated. A new distinct ID is created; no measurements are generated. Source records the local entry mechanism and application version.</p><button type="submit">Review ${kind}</button></form></details>`;
  }
  function panel(){
    if(!cfg.bundle())return '<p class="muted">Import a project first.</p>';
    let html=`<section class="panel" id="expression-design"><div class="panel-head"><h2>Expression constructs</h2></div><div class="panel-body">${choices()}`;
    const m=molecule();if(!m)return html+'</div></section>';
    const constructs=records().filter((e)=>e.type==='construct'&&e.molecule_id===m.id),c=context();
    html+=`<p class="mono">Declared Molecule: ${esc(m.id)}</p><div class="form-row">${['Left','Right'].map((side)=>`<label class="field">${side} Construct<select id="expression-${side.toLowerCase()}"><option value="">Choose an actual Construct ID</option>${constructs.map((e)=>option(e.id,`${e.name} / ${e.id}`,state()['expression'+side])).join('')}</select></label>`).join('')}</div>`;
    html+='<div id="expression-comparison">';
    if(!c)html+='<p role="status">Loading exact Construct/Material context…</p>';
    else if(!c.comparison)html+='<p class="muted">Choose two distinct Constructs to compare recorded metadata. Unknown CDS is unavailable, including when both are unknown.</p>';
    else{
      html+='<p class="muted">Raw DNA positions are 1-based and unaligned. They are separate from amino-acid indexes. Equal recorded values establish neither coding equivalence nor equal expression.</p><div class="table-wrap"><table id="construct-differences"><thead><tr><th>Recorded field</th><th>Left</th><th>Right</th><th>Comparison</th></tr></thead><tbody>';
      for(const field of ['cds','vector','signal_peptide']){const value=c.comparison[field];html+=`<tr><td>${esc(field)}</td><td class="mono wrap">${value.left===null?'Unknown':esc(value.left)}</td><td class="mono wrap">${value.right===null?'Unknown':esc(value.right)}</td><td>${esc(value.status.replaceAll('_',' '))}</td></tr>`;}
      html+='</tbody></table></div>';
      const cds=c.comparison.cds;
      if(cds.status!=='unavailable')html+=`<details><summary>${cds.raw_differences.length} raw DNA position differences · lengths ${cds.left_length} / ${cds.right_length}</summary><pre>${cfg.pretty(cds.raw_differences)}</pre></details>`;
      html+=`<details><summary>Original Construct IDs and entry sources</summary><pre>${cfg.pretty(c.constructs.filter((e)=>[c.left_id,c.right_id].includes(e.id)))}</pre></details>`;
    }
    html+='</div>'+metadataForm('construct')+metadataForm('material');
    html+=`<p><button data-open="${m.id}">Follow Constructs and Materials in W</button> <button data-screen="R">Compare original measurements in R</button></p></div></section>`;
    return html;
  }
  function evidencePanel(){
    if(!cfg.bundle()||!molecule())return '';
    const c=context(),s=state();
    let html=`<section class="panel" id="expression-observations"><div class="panel-head"><h2>Construct / Material observations</h2></div><div class="panel-body">${choices()}<p class="muted">Each row belongs to its original Material. No averaging, unit conversion, replicate assumption or causal expression effect is inferred. Molecule/Construct-level results are available in the evidence cards below and are never repeated as Material results.</p>`;
    if(!c)return html+'<p role="status">Loading original observation context…</p></div></section>';
    const available=new Set(c.materials.map((e)=>e.id));
    const material=s.expressionMaterial&&available.has(s.expressionMaterial)?s.expressionMaterial:null;
    html+=`<div class="form-row"><label class="field">Material / lot<select id="expression-material"><option value="">All Materials in this Construct scope</option>${c.materials.map((e)=>option(e.id,`${e.name} / lot ${e.lot} / ${e.id}`,material)).join('')}</select></label><label class="field">Exact observation context<select id="expression-cohort"><option value="">All original contexts (separate rows)</option>${c.cohorts.map((e)=>option(e.id,`${e.kind} / ${e.metric} / ${e.unit} / ${e.source.name} ${e.source.version} / ${JSON.stringify(e.conditions)}`,e.evidence_ids.includes(s.expressionCohort)?e.id:null)).join('')}</select></label></div>`;
    html+=`<p class="muted">${c.materials.length} actual Materials · ${c.observations.length} original observations · ${c.ineligible.length} observations cannot establish a complete comparison context. Matching metadata alone does not establish scientific comparability.</p><div class="table-wrap"><table><thead><tr><th>Material / Construct</th><th>Type / metric</th><th>Original value / unit</th><th>Conditions / event time</th><th>Source / provenance</th></tr></thead><tbody>`;
    const rows=c.observations.filter((e)=>(!material||e.subject_id===material)&&(!s.expressionCohort||c.context_evidence_ids.includes(e.id)));
    for(const e of rows){const mat=find(e.subject_id),con=find(mat.construct_id),issue=c.ineligible.find((i)=>i.evidence_id===e.id)?.reason;
      html+=`<tr data-material-observation="${e.id}"><td>${esc(mat.name)} / lot ${esc(mat.lot)}<small class="mono">${esc(mat.id)}</small>${esc(con.name)}<small class="mono">${esc(con.id)}</small></td><td><span class="tag ${esc(e.kind)}">${esc(e.kind)}</span> ${esc(e.metric)}${issue?`<small>${esc(issue)}</small>`:''}</td><td>${e.value===null?'Not supplied':esc(e.value)} / ${e.unit===null?'Unit unknown':esc(e.unit)}</td><td>${e.conditions===null?'Conditions unknown — do not pool':esc(JSON.stringify(e.conditions))}<small>${esc(e.timestamp)}</small></td><td>${esc(e.source.name)} / ${esc(e.source.version||'version unknown')}<small class="mono">${esc(e.id)}</small><button class="text-button" data-source-evidence="${e.id}">Inspect original evidence</button>${e.import_origin?`<details><summary>File record ${e.import_origin.record_index}, end-line ${e.import_origin.line_number}</summary><pre>${cfg.pretty(e.import_origin)}</pre><p>Recorded submitted-text provenance; imported attestations do not authenticate an absent original file.</p></details>`:''}</td></tr>`;
    }
    html+=`</tbody></table></div>${rows.length?'':'<p class="muted">No observations in this selected scope. No zero is substituted.</p>'}<button data-open-hypothesis>Retain question and next controlled experiment</button></div></section>`;
    return html;
  }
  async function mount(){
    if(!cfg.bundle()||!molecule())return;
    if(cacheBundle!==cfg.bundle()){cacheBundle=cfg.bundle();contexts.clear();}
    const owner=key(),ticket=++contextRequest;if(contexts.has(owner))return;
    const project=cfg.bundle().project.id,s=state(),query=new URLSearchParams({project_id:project,molecule_id:molecule().id});
    for(const [field,name] of [['expressionLeft','left_id'],['expressionRight','right_id'],['expressionCohort','cohort_id']])if(s[field])query.set(name,s[field]);
    try{const c=await cfg.api('/api/construct-context?'+query);if(ticket!==contextRequest||owner!==key())return;contexts.set(owner,c);
      // Refresh only the asynchronous readout; preserve in-progress metadata,
      // shortlist text, hypothesis context and any unrelated renderer/camera.
      if(s.screen==='R'){const host=document.querySelector('#expression-observations');if(host)host.outerHTML=evidencePanel();}
      else if(s.screen==='D'&&s.designTask==='expression'){const host=document.querySelector('#expression-comparison');if(host){const template=document.createElement('template');template.innerHTML=panel();host.innerHTML=template.content.querySelector('#expression-comparison').innerHTML;}}
    }
    catch(error){if(ticket!==contextRequest||owner!==key())return;s.expressionLeft=null;s.expressionRight=null;s.expressionCohort=null;cfg.notify(error.message+' Explicit Construct comparison was cleared; candidate identity was retained.',true);}
  }
  function ensureDialog(){if(document.querySelector('#metadata-preview-dialog'))return;const dialog=document.createElement('dialog');dialog.id='metadata-preview-dialog';dialog.innerHTML='<h2>Review declared metadata</h2><div id="metadata-preview-content"></div><div class="dialog-actions"><button data-metadata-close class="secondary">Back</button><button id="save-metadata">Save new record</button></div>';document.body.append(dialog);dialog.addEventListener('close',()=>{preview=null;});}
  document.addEventListener('input',(event)=>{const el=event.target,form=el.closest('[data-metadata-form]');if(!cfg||!form||!el.dataset.metadataField)return;draft(form.dataset.metadataForm)[el.dataset.metadataField]=el.value;revision++;});
  document.addEventListener('change',(event)=>{
    if(!cfg||!cfg.bundle())return;const el=event.target,s=state();
    const fields={'expression-molecule':'expressionMolecule','expression-left':'expressionLeft','expression-right':'expressionRight','expression-material':'expressionMaterial','expression-cohort':'expressionCohort'};
    if(!fields[el.id])return;
    invalidate();s[fields[el.id]]=el.value||null;
    if(el.id==='expression-molecule'){s.expressionLeft=null;s.expressionRight=null;s.expressionCohort=null;s.expressionMaterial=null;}
    if(['expression-left','expression-right'].includes(el.id)){s.expressionCohort=null;s.expressionMaterial=null;}
    cfg.render();
  });
  document.addEventListener('submit',async(event)=>{
    const form=event.target;if(!cfg||!form.matches('[data-metadata-form]'))return;event.preventDefault();ensureDialog();
    const kind=form.dataset.metadataForm,d=draft(kind),m=molecule(),scope=intent(),version=revision,ticket=++request,project=cfg.bundle().project.id;
    const values=Object.fromEntries([...form.querySelectorAll('[data-metadata-field]')].map((el)=>[el.dataset.metadataField,el.value]));
    Object.assign(d,values);const definition={type:kind,...values};
    if(kind==='construct'){definition.molecule_id=m.id;for(const field of ['cds','vector','signal_peptide'])definition[field]=definition[field]||null;}
    const button=event.submitter;if(button)button.disabled=true;
    try{const result=await cfg.api('/api/metadata-preview',{project_id:project,definition});if(scope!==intent()||version!==revision||ticket!==request)return;
      preview={bundle:result,scope,version,draft:d,kind,project};document.querySelector('#metadata-preview-content').innerHTML=`<p>New ${kind} ID with the exact declared association below. No measurements, translation check or authenticated authorship is created.</p><pre>${cfg.pretty(result)}</pre>`;
      document.querySelector('#metadata-preview-dialog > .dialog-error')?.remove();
      document.querySelector('#save-metadata').disabled=false;document.querySelector('#metadata-preview-dialog').showModal();
    }catch(error){if(scope===intent()&&version===revision&&ticket===request)cfg.notify(error.message,true);}
    finally{if(button?.isConnected)button.disabled=false;}
  });
  document.addEventListener('click',async(event)=>{
    const b=event.target.closest('button');if(!cfg||!cfg.bundle()||!b||b.disabled)return;
    if(b.hasAttribute('data-expression-material')){const mat=find(b.dataset.expressionMaterial),con=find(mat.construct_id),s=state();s.expressionMolecule=con.molecule_id;s.expressionLeft=null;s.expressionRight=null;s.expressionCohort=null;s.expressionMaterial=mat.id;if(!s.selected.includes(con.molecule_id))s.selected.push(con.molecule_id);s.screen='R';cfg.render();}
    else if(b.hasAttribute('data-metadata-close'))document.querySelector('#metadata-preview-dialog').close();
    else if(b.id==='save-metadata'){
      const p=preview;if(!p)return;b.disabled=true;const owns=()=>preview===p&&p.scope===intent()&&p.version===revision;
      let saved=false;
      try{await cfg.api('/api/import',p.bundle);saved=true;if(owns()){for(const key of Object.keys(p.draft))delete p.draft[key];document.querySelector('#metadata-preview-dialog').close();await cfg.reload();cfg.notify('Saved distinct '+p.kind+' with its declared association and entry source.');}else cfg.notify('Submitted metadata saved. The newer selection and draft were retained.');}
      catch(error){if(saved)cfg.notify('Metadata saved; reload the workspace to refresh the view.');else if(owns()){cfg.notify(error.message,true);b.disabled=false;}}
    }
  });
  return {configure(options){cfg=options;},panel,evidencePanel,mount,invalidate};
})();
