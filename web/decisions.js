"use strict";

// F19/F20: researcher-declared criteria and immutable decision versions.
const DecisionUI=(()=>{
  let cfg,cacheBundle,contexts=new Map(),contextRequest=0,previewRequest=0,activePreview=null;
  const drafts=new Map(),state=()=>cfg.state(),records=()=>cfg.bundle()?.entities||[],find=(id)=>records().find((e)=>e.id===id),esc=(v)=>cfg.esc(v);
  const scopeKey=()=>JSON.stringify([cfg.bundle()?.project.id,state().selected]);
  const draftKey=()=>JSON.stringify([cfg.bundle()?.project.id,state().selected,state().decisionBase]);
  const intent=()=>JSON.stringify([draftKey(),state().screen,state().researchTask]);
  const option=(value,label,current)=>`<option value="${esc(value)}" ${value===current?'selected':''}>${esc(label)}</option>`;
  function draft(){
    const key=draftKey();if(!drafts.has(key))drafts.set(key,{revision:0,definition:{candidate_ids:[...state().selected],chosen_candidate_ids:[],criteria:[],hypothesis_ids:[],supporting_evidence_ids:[],reason:'',status:'draft',supersedes:state().decisionBase||null}});
    return drafts.get(key);
  }
  function context(){return cacheBundle===cfg.bundle()?contexts.get(scopeKey()):null;}
  function invalidate(){previewRequest++;contextRequest++;activePreview=null;document.querySelector('#decision-preview-dialog')?.close();}
  function sourceLabel(e){const path=cfg.subjectPath(e);return `${e.kind} / ${e.metric} / ${e.value===null?'value missing':e.value+' '+e.unit} / ${path.map((p)=>p.name).join(' → ')} / ${e.subject_id} / ${e.timestamp} / ${e.id}`;}
  function controls(){
    const c=context();if(!c)return '<p role="status">Loading exact original observation contexts…</p>';
    return `<label class="field">Original observation context for a new criterion<select id="decision-add-context"><option value="">Choose measured/computed metric, unit, conditions and source</option>${c.cohorts.map((e)=>option(e.id,`${e.kind} / ${e.metric} / ${e.unit} / ${JSON.stringify(e.conditions)} / ${e.source.name} ${e.source.version} / ${e.id}`,null)).join('')}</select></label><button type="button" id="decision-add-criterion" class="secondary">Add an explicit criterion</button><p class="muted">${c.ineligible.length} original records have incomplete context or a nonnumeric evidence kind; they remain available in the source cards and supporting evidence. No sole observation is chosen automatically.</p>`;
  }
  function choices(criterion,candidate){
    const group=context()?.cohorts.find((c)=>c.evidence_ids.includes(criterion.anchor_evidence_id));
    return (group?.evidence_ids||[]).map(find).filter((e)=>cfg.subjectPath(e).some((p)=>p.type==='molecule'&&p.id===candidate));
  }
  function criterionPanel(criterion,i){
    const anchor=find(criterion.anchor_evidence_id);
    let html=`<fieldset data-decision-criterion="${i}"><legend>${esc(criterion.name)} / ${esc(criterion.key)}</legend><div class="form-row"><label class="field">Criterion name<input data-criterion-field="name" value="${esc(criterion.name)}"></label><label class="field">Declared importance weight (no composite score)<input data-criterion-field="weight" inputmode="decimal" value="${esc(criterion.weight)}" placeholder="Explicit nonnegative number"></label><label class="field">Researcher's preference<select data-criterion-field="preference"><option value="">Choose explicitly</option>${['higher','lower','inspect'].map((v)=>option(v,v,criterion.preference)).join('')}</select></label><label class="field"><span>Completeness requirement</span><span><input type="checkbox" data-criterion-required ${criterion.required?'checked':''}> Required numeric observation for every compared candidate</span></label></div>`;
    html+=`<details><summary>Exact original context and anchor</summary><p class="mono">${esc(criterion.anchor_evidence_id)}</p><pre>${cfg.pretty(anchor?{kind:anchor.kind,metric:anchor.metric,unit:anchor.unit,conditions:anchor.conditions,source:anchor.source}:null)}</pre><p class="muted">Matching metadata does not establish scientific comparability. Importance 0 does not disable a required observation. Preferences do not generate rankings.</p></details><div class="table-wrap"><table><thead><tr><th>Comparison candidate</th><th>Explicit original observation / actual subject</th><th>Source</th></tr></thead><tbody>`;
    for(const id of state().selected){const m=find(id),available=choices(criterion,id),chosen=find(criterion.evidence_choices[id]);
      html+=`<tr><td>${esc(m?.name)}<small class="mono">${esc(id)}</small>${draft().definition.chosen_candidate_ids.includes(id)?'<small>Chosen by researcher</small>':''}</td><td><select data-criterion-choice="${id}" aria-label="Observation for ${esc(criterion.key)} ${esc(m?.external_id)}"><option value="">${available.length?'Unchosen — explicitly select an original record':'No eligible observation — unknown'}</option>${available.map((e)=>option(e.id,sourceLabel(e),criterion.evidence_choices[id])).join('')}</select>${chosen?`<p>${chosen.value===null?'Selected source value is missing':esc(chosen.value)+' / '+esc(chosen.unit)}</p>`:'<p class="muted">No numeric value is substituted.</p>'}</td><td>${chosen?`<button type="button" class="text-button" data-decision-source="${chosen.id}">Inspect original subject in W</button><small class="mono">${esc(chosen.subject_id)}</small>${find(chosen.subject_id)?.type==='material'?`<small>Original lot: ${esc(find(chosen.subject_id).lot)}</small>`:''}<small>${esc(chosen.source.name)} / ${esc(chosen.source.version||'version unknown')}</small>`:''}</td></tr>`;
    }
    return html+`</tbody></table></div><button type="button" class="text-button" data-remove-criterion="${i}">Remove criterion</button></fieldset>`;
  }
  function supporting(d){
    const inScope=(e)=>cfg.subjectPath(e).some((p)=>p.type==='molecule'&&state().selected.includes(p.id));
    const evidence=records().filter((e)=>e.type==='evidence'&&inScope(e)),hypotheses=records().filter((e)=>e.type==='hypothesis'&&e.molecule_ids.every((id)=>state().selected.includes(id)));
    return `<details><summary>Additional supporting evidence and proposed hypotheses</summary><p class="muted">Criterion anchors/selected observations and a selected hypothesis's original sources are frozen automatically. These additional selections remain their original kinds; a proposed hypothesis does not become a fact.</p>${hypotheses.map((h)=>`<label class="hypothesis-source"><input type="checkbox" data-decision-hypothesis="${h.id}" ${d.hypothesis_ids.includes(h.id)?'checked':''}> Proposed: ${esc(h.text)}<small>${esc(h.id)}</small></label>`).join('')}${evidence.map((e)=>`<label class="hypothesis-source"><input type="checkbox" data-decision-support="${e.id}" ${d.supporting_evidence_ids.includes(e.id)?'checked':''}> ${esc(sourceLabel(e))}</label>`).join('')}</details>`;
  }
  function saved(){
    const decisions=records().filter((e)=>e.type==='decision'&&e.chosen_candidate_ids!==undefined&&e.candidate_ids.some((id)=>state().selected.includes(id)));
    return `<section class="panel" id="saved-decisions"><div class="panel-head"><h2>Saved decision versions</h2></div><div class="panel-body">${decisions.length?'':'<p class="muted">No criterion-bearing Decision saved for this scope. Existing shortlists remain drafts.</p>'}${decisions.toReversed().map((e)=>`<article class="saved-decision"><h3>${esc(e.status)} / revision ${e.revision}</h3><p>${esc(e.reason)}</p><p class="mono">${e.id}</p><p>${e.chosen_candidate_ids.length} explicitly chosen / ${e.candidate_ids.length} compared · ${esc(e.timestamp)}</p><button type="button" class="secondary" data-view-decision="${e.id}">Inspect frozen version</button> <button type="button" data-revise-decision="${e.id}" ${records().some((s)=>s.type==='decision'&&s.supersedes===e.id)?'disabled':''}>Create a new revision</button><details><summary>Exact immutable record and original snapshots</summary><pre>${cfg.pretty(e)}</pre></details></article>`).join('')}</div></section>`;
  }
  function panel(){
    if(!cfg.bundle()||!state().selected.length)return '<p>Select actual candidates in E.</p>';
    if(!state().decisionEditorOpen)return `<section class="panel panel-body"><p>Decision version saved. Inspect its exact frozen record or explicitly create a new revision below.</p><button type="button" id="decision-new">Start a separate decision</button></section>${saved()}`;
    const d=draft().definition,base=find(state().decisionBase);
    return `<section class="panel" id="decision-editor"><div class="panel-head"><h2>Criteria and research decision</h2><span class="tag">Researcher judgment</span></div><div class="panel-body"><p class="muted">Declare criteria, original observations and importance; then record your choice and trade-offs. No ranking or composite score is computed. Every required criterion needs an explicitly selected numeric observation for EVERY compared candidate, including unchosen candidates. Change requirements/scope explicitly and explain a saved revision.</p><p>${base?`New revision of ${esc(base.id)} / ${esc(base.status)} / revision ${base.revision}`:'First version of a new decision'} · <button type="button" class="text-button" id="decision-new">Start a separate decision</button></p><form id="decision-form"><fieldset><legend>Explicitly chosen candidate subset</legend>${state().selected.map((id)=>{const m=find(id);return `<label class="hypothesis-source"><input type="checkbox" data-decision-chosen="${id}" ${d.chosen_candidate_ids.includes(id)?'checked':''}> ${esc(m?.external_id)} / ${esc(m?.name)}<small>${esc(id)}</small></label>`;}).join('')}</fieldset><div id="decision-context-controls">${controls()}</div><div id="decision-criteria">${d.criteria.map(criterionPanel).join('')}</div>${supporting(d)}<label class="field">Decision reason, trade-offs and changes from the previous version<textarea id="decision-reason" rows="5">${esc(d.reason)}</textarea></label><p class="muted">Saved drafts may retain unknown observations or no chosen candidates. Finalized versions require criteria, an explicit chosen subset and complete required observations. Every saved version is immutable; changes create a new ID.</p><div class="dialog-actions"><button type="submit" data-decision-status="draft" class="secondary">Review draft version</button><button type="submit" data-decision-status="finalized">Review finalization</button></div></form></div></section>${saved()}`;
  }
  async function mount(){
    if(!cfg.bundle()||!state().selected.length)return;
    if(cacheBundle!==cfg.bundle()){cacheBundle=cfg.bundle();contexts.clear();}
    const key=scopeKey(),ticket=++contextRequest;if(contexts.has(key))return;
    try{const c=await cfg.api('/api/decision-context',{project_id:cfg.bundle().project.id,candidate_ids:[...state().selected]});
      if(ticket!==contextRequest||key!==scopeKey())return;contexts.set(key,c);
      if(state().screen==='R'&&state().researchTask==='decision'){
        const target=document.querySelector('#decision-context-controls');if(target)target.innerHTML=controls();
        const template=document.createElement('template');template.innerHTML=draft().definition.criteria.map(criterionPanel).join('');
        document.querySelectorAll('#decision-criteria [data-criterion-choice]').forEach((select)=>{const i=select.closest('[data-decision-criterion]').dataset.decisionCriterion,source=template.content.querySelector(`[data-decision-criterion="${i}"] [data-criterion-choice="${select.dataset.criterionChoice}"]`);if(source)select.innerHTML=source.innerHTML;});
      }
    }catch(error){if(ticket===contextRequest&&key===scopeKey())cfg.notify(error.message,true);}
  }
  function ensureDialog(){
    if(document.querySelector('#decision-preview-dialog'))return;
    const dialog=document.createElement('dialog');dialog.id='decision-preview-dialog';dialog.innerHTML='<h2 id="decision-preview-title">Review Decision version</h2><div id="decision-preview-content"></div><div class="dialog-actions"><button data-decision-back class="secondary">Back</button><button id="save-decision">Save reviewed version</button></div>';document.body.append(dialog);
    dialog.addEventListener('close',()=>{previewRequest++;activePreview=null;});
  }
  function reviewTable(review){
    return `<p class="muted">${esc(review.policy)}</p>${review.blockers.length?`<p class="tag warning">Finalization blocked</p><pre>${cfg.pretty(review.blockers)}</pre>`:'<p>Required information is complete under the declared policy. This does not validate scientific comparability.</p>'}${review.criteria.map((c)=>`<h3>${esc(c.name)} · weight ${esc(c.weight)} · ${c.required?'required':'optional'} · ${esc(c.preference)}</h3><details><summary>Original context and anchor</summary><p class="mono">${esc(c.anchor_evidence_id)}</p><pre>${cfg.pretty(c.context)}</pre></details><div class="table-wrap"><table><thead><tr><th>Candidate</th><th>Original observation</th><th>Actual subject</th><th>State</th></tr></thead><tbody>${c.rows.map((r)=>`<tr><td>${esc(find(r.molecule_id)?.external_id)}<small>${esc(r.molecule_id)}</small></td><td>${r.value===null?'Unknown / not supplied':esc(r.value)+' '+esc(r.unit)}<small>${esc(r.evidence_id||'No original selected')}</small></td><td>${esc(r.subject_id||'No subject reassigned')}</td><td>${esc(r.status)}</td></tr>`).join('')}</tbody></table></div>`).join('')}${review.changes.length?`<details open><summary>Explicit changes from predecessor</summary><pre>${cfg.pretty(review.changes)}</pre></details>`:''}`;
  }
  document.addEventListener('input',(event)=>{
    if(!cfg||!event.target.closest('#decision-form'))return;
    const el=event.target,d=draft();
    if(el.id==='decision-reason')d.definition.reason=el.value;
    else if(el.dataset.criterionField){const i=Number(el.closest('[data-decision-criterion]').dataset.decisionCriterion);d.definition.criteria[i][el.dataset.criterionField]=el.value;}
    else return;
    d.revision++;
  });
  document.addEventListener('change',(event)=>{
    if(!cfg||!cfg.bundle()||!event.target.closest('#decision-form'))return;
    const el=event.target,d=draft();let changed=true,redraw=false;
    const toggle=(field,id)=>{d.definition[field]=el.checked?[...d.definition[field].filter((v)=>v!==id),id]:d.definition[field].filter((v)=>v!==id);};
    if(el.dataset.decisionChosen){toggle('chosen_candidate_ids',el.dataset.decisionChosen);redraw=true;}
    else if(el.dataset.decisionHypothesis)toggle('hypothesis_ids',el.dataset.decisionHypothesis);
    else if(el.dataset.decisionSupport)toggle('supporting_evidence_ids',el.dataset.decisionSupport);
    else if(el.hasAttribute('data-criterion-required'))d.definition.criteria[Number(el.closest('[data-decision-criterion]').dataset.decisionCriterion)].required=el.checked;
    else if(el.dataset.criterionChoice){d.definition.criteria[Number(el.closest('[data-decision-criterion]').dataset.decisionCriterion)].evidence_choices[el.dataset.criterionChoice]=el.value||null;redraw=true;}
    else changed=false;
    if(changed){d.revision++;if(redraw)document.querySelector('#decision-criteria').innerHTML=d.definition.criteria.map(criterionPanel).join('');}
  });
  document.addEventListener('submit',async(event)=>{
    if(!cfg||event.target.id!=='decision-form')return;event.preventDefault();ensureDialog();
    const d=draft(),scope=intent(),revision=d.revision,ticket=++previewRequest,project=cfg.bundle().project.id;
    const definition=structuredClone(d.definition);definition.status=event.submitter?.dataset.decisionStatus||'draft';
    const button=event.submitter;if(button)button.disabled=true;
    try{const result=await cfg.api('/api/decision-review',{project_id:project,definition});
      if(scope!==intent()||revision!==d.revision||ticket!==previewRequest)return;
      activePreview={bundle:result.bundle,project,draft:d,scope,revision,ticket};
      document.querySelector('#decision-preview-dialog > .dialog-error')?.remove();document.querySelector('#decision-preview-title').textContent='Review '+definition.status+' version '+result.bundle.entities[0].revision;
      document.querySelector('#decision-preview-content').innerHTML=reviewTable(result.review)+`<p>${esc(result.bundle.entities[0].reason)}</p><details><summary>Exact new Decision ID, chosen subset, timestamp and frozen originals</summary><pre>${cfg.pretty(result.bundle)}</pre></details>`;
      document.querySelector('#save-decision').disabled=false;document.querySelector('#save-decision').hidden=false;document.querySelector('#decision-preview-dialog').showModal();
    }catch(error){if(scope===intent()&&revision===d.revision&&ticket===previewRequest)cfg.notify(error.message,true);}
    finally{if(button?.isConnected)button.disabled=false;}
  });
  document.addEventListener('click',async(event)=>{
    const b=event.target.closest('button');if(!cfg||!cfg.bundle()||!b||b.disabled)return;
    if(b.dataset.researchTask){invalidate();state().researchTask=b.dataset.researchTask;cfg.render();}
    else if(b.id==='decision-add-criterion'){
      const anchor=document.querySelector('#decision-add-context').value,e=find(anchor);if(!e){cfg.notify('Choose an actual source-bearing observation context first.',true);return;}
      const d=draft();d.definition.criteria.push({key:'criterion-'+crypto.randomUUID(),name:e.metric,weight:'',required:false,preference:'',anchor_evidence_id:e.id,evidence_choices:Object.fromEntries(state().selected.map((id)=>[id,null]))});d.revision++;
      document.querySelector('#decision-criteria').innerHTML=d.definition.criteria.map(criterionPanel).join('');
    }else if(b.dataset.removeCriterion!==undefined){const d=draft();d.definition.criteria.splice(Number(b.dataset.removeCriterion),1);d.revision++;document.querySelector('#decision-criteria').innerHTML=d.definition.criteria.map(criterionPanel).join('');}
    else if(b.id==='decision-new'){invalidate();state().decisionBase=null;state().decisionEditorOpen=true;drafts.delete(draftKey());cfg.render();}
    else if(b.dataset.decisionSource){const e=find(b.dataset.decisionSource),m=cfg.subjectPath(e).find((p)=>p.type==='molecule');state().focus=m.id;state().screen='W';cfg.render();}
    else if(b.dataset.reviseDecision){const record=find(b.dataset.reviseDecision);invalidate();state().selected=[...record.candidate_ids];state().decisionBase=record.id;state().decisionEditorOpen=true;state().researchTask='decision';state().screen='R';drafts.set(draftKey(),{revision:0,definition:{candidate_ids:[...record.candidate_ids],chosen_candidate_ids:[...(record.chosen_candidate_ids||[])],criteria:structuredClone(record.criteria),hypothesis_ids:[...(record.hypothesis_ids||[])],supporting_evidence_ids:record.evidence_snapshot.map((e)=>e.id),reason:'',status:'draft',supersedes:record.id}});cfg.render();}
    else if(b.dataset.viewDecision){ensureDialog();invalidate();const record=find(b.dataset.viewDecision);document.querySelector('#decision-preview-title').textContent='Frozen '+record.status+' revision '+record.revision;document.querySelector('#decision-preview-content').innerHTML=`<p>Original saved record. Later observations do not replace this snapshot. Use Export JSON for the complete project and revision dependencies.</p><pre>${cfg.pretty(record)}</pre>`;document.querySelector('#save-decision').hidden=true;document.querySelector('#decision-preview-dialog').showModal();}
    else if(b.hasAttribute('data-decision-back'))document.querySelector('#decision-preview-dialog').close();
    else if(b.id==='save-decision'){
      const p=activePreview;if(!p)return;b.disabled=true;
      const owns=()=>activePreview===p&&p.ticket===previewRequest&&p.scope===intent()&&p.draft.revision===p.revision;
      let saved=false;
      try{await cfg.api('/api/import',p.bundle);saved=true;if(owns()){const record=p.bundle.entities[0];drafts.delete(draftKey());state().decisionBase=record.id;state().decisionEditorOpen=false;document.querySelector('#decision-preview-dialog').close();await cfg.reload();cfg.notify('Saved immutable '+record.status+' Decision revision '+record.revision+'. Original subjects and frozen evidence were retained.');}else cfg.notify('Submitted Decision saved. The newer project, selection and draft were retained.');}
      catch(error){if(saved)cfg.notify('Decision saved; reload the workspace to refresh the view.');else if(owns()){cfg.notify(error.message,true);b.disabled=false;}}
    }
  });
  return {configure(options){cfg=options;},panel,mount,invalidate};
})();
