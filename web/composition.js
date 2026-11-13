"use strict";

// Explicit declared recipes; scientific identities and all saves are validated locally by Python.
window.CompositionUI = (() => {
  let cfg, generation=0, previewRequest=0, contextRequest=0, activePreview=null;
  const drafts=new Map();
  const state=()=>cfg.state(), records=()=>cfg.bundle()?.entities||[], units=()=>records().filter((e)=>e.type==='binding_unit');
  const find=(id)=>records().find((e)=>e.id===id), esc=(v)=>cfg.esc(v);
  const option=(value,label,current)=>`<option value="${esc(value)}" ${value===current?'selected':''}>${esc(label)}</option>`;
  const empty=()=>({revision:0,issuedComponentIds:new Set(),definition:{name:'',external_id:'',format:'',parent_id:null,reason:null,note:null,chains:[],connections:[]}});
  function draft(){const key=cfg.bundle().project.id;if(!drafts.has(key))drafts.set(key,empty());return drafts.get(key);}
  function intent(){const s=state();return JSON.stringify([cfg.bundle().project.id,s.screen,s.designTask,s.selected,s.selectedUnits,s.compositionParent]);}
  function invalidate(){generation++;previewRequest++;contextRequest++;activePreview=null;document.querySelector('#composition-preview-dialog')?.close();}
  function explorer(){
    if(!units().length)return '';
    return `<section class="panel"><div class="panel-head"><h2>Binding unit sources</h2><button class="secondary" data-composition-start>Design an explicit composition</button></div><div class="panel-body"><p class="muted">Select actual source IDs. Topology and roles are supplied declarations; pairing and function are not validated.</p>${units().map((u)=>`<details><summary><label><input type="checkbox" data-unit-select="${u.id}" ${state().selectedUnits.includes(u.id)?'checked':''}> ${esc(u.name)} / ${esc(u.topology)}</label></summary><p class="mono">${u.id}</p><p>${esc(u.source.name)} / ${esc(u.source.version||'version unknown')}</p><pre>${cfg.pretty(u)}</pre></details>`).join('')}<p>${state().selectedUnits.length} source IDs selected; source selection does not imply complete use or valency.</p></div></section>`;
  }
  function componentRow(part,i,j){
    const source=part.source, unit=find(source.binding_unit_id), chain=unit?.chains.find((c)=>c.id===source.chain_id);
    return `<div class="composition-part" data-recipe-chain="${i}" data-recipe-part="${j}"><div class="form-row"><label class="field">Component ID<input data-part-field="id" value="${esc(part.id)}" required></label><label class="field">Declared part role<input data-part-field="role" value="${esc(part.role)}" required></label><label class="field">Part source<select data-part-source-kind>${option('binding_unit','BindingUnit interval',source.kind)}${option('sequence','Independent sequence / linker',source.kind)}</select></label></div>${source.kind==='binding_unit'?`<div class="form-row"><label class="field">Actual BindingUnit<select data-part-unit>${option('','Choose source explicitly',source.binding_unit_id)}${units().filter((u)=>state().selectedUnits.includes(u.id)||u.id===source.binding_unit_id).map((u)=>option(u.id,`${u.name} / ${u.id}`,source.binding_unit_id)).join('')}</select></label><label class="field">Source chain<select data-part-source-chain>${option('','Choose source chain',source.chain_id)}${(unit?.chains||[]).map((c)=>option(c.id,`${c.id} / ${c.role} / ${c.sequence.length} aa`,source.chain_id)).join('')}</select></label></div><div class="form-row"><label class="field">First raw index<input type="number" min="1" data-source-start value="${esc(source.start)}" required></label><label class="field">Last raw index (inclusive)<input type="number" min="1" data-source-end value="${esc(source.end)}" required></label><button type="button" class="secondary" data-source-full ${chain?'':'disabled'}>Use full declared source chain</button></div>`:`<label class="field">Explicit amino-acid sequence<textarea data-part-sequence rows="2" required spellcheck="false">${esc(source.sequence)}</textarea></label><p class="muted">Literal sequence required; no default linker or shorthand is inserted.</p>`}<div class="dialog-actions"><button type="button" class="secondary" data-part-up ${j===0?'disabled':''}>Move up</button><button type="button" class="secondary" data-part-down ${j===draft().definition.chains[i].components.length-1?'disabled':''}>Move down</button><button type="button" class="secondary" data-part-remove>Remove part (connections must be reviewed)</button></div></div>`;
  }
  function endpointOptions(current){
    const values=draft().definition.chains.flatMap((c)=>c.components.map((p)=>JSON.stringify({chain_id:c.id,component_id:p.id})));
    const missing=current&&!values.includes(current)&&Object.values(JSON.parse(current)).some(Boolean);
    return option('','Choose exact endpoint',current)+(missing?option(current,'Missing endpoint: '+current,current):'')+draft().definition.chains.flatMap((c)=>c.components.map((p)=>{
      const value=JSON.stringify({chain_id:c.id,component_id:p.id});return option(value,`${c.id||'(chain ID required)'} / ${p.id}`,current);
    })).join('');
  }
  function panel(){
    const composed=records().filter((e)=>e.type==='molecule');
    if(!units().length&&!composed.some((m)=>m.component_graph))return '';
    const d=draft().definition;
    const previewable=d.chains.length>0;
    const chainRows=d.chains.map((c,i)=>`<fieldset data-recipe-chain="${i}"><legend>Declared chain ${i+1}</legend><div class="form-row"><label class="field">Chain ID<input data-chain-field="id" value="${esc(c.id)}" required></label><label class="field">Declared chain role<input data-chain-field="role" value="${esc(c.role)}" required></label><label class="field">Declared copies<input type="number" min="1" max="100" data-chain-field="copies" value="${esc(c.copies)}" required></label></div>${c.components.map((p,j)=>componentRow(p,i,j)).join('')}<div class="dialog-actions"><button type="button" class="secondary" data-part-add="${i}">Add ordered part</button><button type="button" class="secondary" data-chain-remove="${i}">Remove chain (review connections)</button></div></fieldset>`).join('');
    return `<details class="panel" id="composition-design" ${state().compositionOpen?'open':''}><summary class="panel-head"><h2>Explicit molecular composition</h2></summary><div class="panel-body"><p class="muted">Declare the chains and exact source parts. No pairing, missing chain, linker, copy count or biological format is inferred. Connections are declarations between component definitions, not individual-copy contacts.</p><p>Source IDs selected in E: ${state().selectedUnits.map((id)=>esc(find(id)?.name||id)).join(', ')||'none; select BindingUnits in E, or enter an independent sequence explicitly'}</p><form id="composition-form"><div class="form-row"><label class="field">Molecule name<input id="composition-name" value="${esc(d.name)}" required></label><label class="field">External ID<input id="composition-external" value="${esc(d.external_id)}" required></label><label class="field">Declared format<input id="composition-format" value="${esc(d.format)}" required></label></div>${d.parent_id?`<p>Explicit parent: ${esc(find(d.parent_id)?.name)} / ${d.parent_id}</p><label class="field">Reason for composition change<textarea id="composition-reason" required>${esc(d.reason)}</textarea></label>`:'<p class="muted">New independent composition. No parent is invented.</p>'}<label class="field">Optional researcher design note (annotation)<textarea id="composition-note" rows="2">${esc(d.note)}</textarea></label>${chainRows}<button type="button" class="secondary" data-chain-add>Add an explicit chain</button><h3>Declared connections</h3><p class="muted">Endpoints keep their exact IDs when parts move. Deleted or renamed endpoints must be reviewed; they are not silently retargeted. Connection cycles do not establish chemical validity.</p>${d.connections.map((c,i)=>`<div class="form-row" data-recipe-connection="${i}"><label class="field">Left endpoint<select data-connection-side="left">${endpointOptions(JSON.stringify(c.left))}</select></label><label class="field">Right endpoint<select data-connection-side="right">${endpointOptions(JSON.stringify(c.right))}</select></label><label class="field">Declared connection kind<select data-connection-kind required>${option('','Choose declared kind',c.kind)}${['declared_pairing','noncovalent','disulfide','covalent'].map((k)=>option(k,k,c.kind)).join('')}</select></label><button type="button" class="secondary" data-connection-remove="${i}">Remove connection</button></div>${(!d.chains.some((g)=>g.id===c.left.chain_id&&g.components.some((p)=>p.id===c.left.component_id))||!d.chains.some((g)=>g.id===c.right.chain_id&&g.components.some((p)=>p.id===c.right.component_id)))?'<p class="warning">Endpoint missing or renamed. Choose both intended endpoints before previewing.</p>':''}`).join('')}<button type="button" class="secondary" data-connection-add>Add an explicit connection</button><div class="dialog-actions"><button type="submit" ${previewable?'':'disabled'}>Review new composition before saving</button></div></form><p class="muted">Unsaved recipes and notes remain in memory, scoped to this project.</p></div></details>${state().compositionCurrent?`<p><button class="secondary" data-inspect-composition="${state().compositionCurrent}">Inspect saved composition in W</button> <button class="secondary" data-copy-composition="${state().compositionCurrent}">Use saved composition as parent recipe</button></p>`:''}<section class="panel" id="composition-compare"><div class="panel-head"><h2>Compare declared compositions</h2></div><div class="panel-body"><p class="muted">Each column retains its actual chain/component identities. Matching order or sequence is not an alignment or proof of pairing.</p><div class="form-row">${[['left','compositionCompareLeft'],['right','compositionCompareRight']].map(([side,key])=>`<label class="field">${side==='left'?'First':'Second'} saved composition<select data-composition-compare="${side}">${option('','Choose a saved composition',state()[key])}${composed.map((m)=>option(m.id,`${m.external_id} / ${m.name}${m.component_graph?'':' / composition undefined'}`,state()[key])).join('')}</select></label>`).join('')}</div><div class="two-columns" id="composition-contexts">Choose actual saved IDs; no first-match fallback.</div></div></section>`;
  }
  function declaredConnections(graph){
    const {connections}=graph;
    const title='<h4>Declared component connections</h4>';
    if(!connections.length)return title+'<p class="muted">No connections declared.</p>';
    const rows=connections.map(({left,right,kind})=>`<tr><td>${esc(left.chain_id)} / ${esc(left.component_id)}</td><td>${esc(kind)}</td><td>${esc(right.chain_id)} / ${esc(right.component_id)}</td></tr>`).join('');
    return title+`<table class="composition-connections" aria-label="Declared component connections"><thead><tr><th scope="col">First chain / part</th><th scope="col">Kind</th><th scope="col">Second chain / part</th></tr></thead><tbody>${rows}</tbody></table>`;
  }
  function contextPanel(context,actions=true){
    const m=context.molecule,g=m.component_graph;
    return `<article><h3>${esc(m.external_id)} / ${esc(m.name)}</h3><p class="mono">${m.id}</p><p>Declared format: ${esc(m.format)}</p>${g?declaredConnections(g):''}${!g?'<p>Composition undefined; nothing was completed from the format.</p>':g.chains.map((c)=>`<h4>${esc(c.chain_id)} / ${esc(m.chains.find((chain)=>chain.id===c.chain_id)?.role)} / ${c.copies} declared copies</h4><ol>${c.components.map((p)=>`<li>${esc(p.id)} / ${esc(p.role)} / ${p.sequence.length} aa${p.origin?`<br>Source ${esc(p.origin.binding_unit_id)} / ${esc(p.origin.chain_id)} raw ${p.origin.start}–${p.origin.end}`:'<br>Independent sequence declaration'}</li>`).join('')}</ol>`).join('')}<h4>Actual source-chain usage</h4><p class="muted">Occurrences describe declared source-chain intervals, not complete functional BindingUnits or valency. No partner is added automatically.</p>${context.source_units.map((u)=>`<details open><summary>${esc(u.unit.name)} / ${esc(u.unit.topology)}</summary>${u.chains.map((c)=>`<p>${esc(c.chain_id)} / ${c.source_length} aa source / ${c.full_source_chain_occurrences} full-source-chain occurrences</p>${c.usages.length?c.usages.map((r)=>`<p class="muted">${esc(r.molecule_chain_id)} / ${esc(r.component_id)}: raw ${r.start}–${r.end}, ${r.copies} declared copies / ${r.is_full_source_chain?'full source-chain interval':'partial interval; no intact unit asserted'}</p>`).join(''):'<p class="warning">Source chain not used; no missing partner is inferred or completed.</p>'}`).join('')}${u.unit.topology==='paired'&&new Set(u.chains.map((c)=>c.full_source_chain_occurrences)).size>1?'<p class="warning">Full source-chain occurrence counts differ. Pairing and valency are not established.</p>':''}</details>`).join('')}<p>Whole-molecule structure prediction: unsupported — no validated local adapter is registered. Imported maps and structures retain only their actual source scope.</p>${actions?`<button class="secondary" data-inspect-composition="${m.id}">Inspect this design in W</button> <button class="secondary" data-copy-composition="${m.id}" ${g?'':'disabled'}>Use this design as parent recipe</button>`:''}<details><summary>Exact graph, declared connections and source usage</summary><pre>${cfg.pretty(context)}</pre></details></article>`;
  }
  async function mount(){
    const host=document.querySelector('#composition-contexts');if(!host)return;
    const ids=[state().compositionCompareLeft,state().compositionCompareRight],project=cfg.bundle().project.id,ticket=++contextRequest;
    if(!ids.some(Boolean))return;
    try{const contexts=await Promise.all(ids.map((id)=>id?cfg.api('/api/composition-context?project_id='+encodeURIComponent(project)+'&molecule_id='+encodeURIComponent(id)):null));
      if(ticket!==contextRequest||cfg.bundle().project.id!==project||JSON.stringify(ids)!==JSON.stringify([state().compositionCompareLeft,state().compositionCompareRight])||!host.isConnected)return;
      host.innerHTML=contexts.map((c)=>c?contextPanel(c):'<p class="muted">No composition chosen for this column.</p>').join('');
    }catch(error){if(ticket===contextRequest&&host.isConnected)host.textContent=error.message;}
  }
  function ensureDialog(){
    if(document.querySelector('#composition-preview-dialog'))return;
    const dialog=document.createElement('dialog');dialog.id='composition-preview-dialog';dialog.innerHTML='<div class="dialog-heading"><h2>Review explicit composition records</h2><button class="icon-button" data-composition-close aria-label="Close composition preview">×</button></div><div id="composition-preview-content"></div><div class="dialog-actions"><button id="save-composition">Save reviewed composition records</button></div>';
    dialog.addEventListener('close',()=>{if(!dialog.open)previewRequest++;});document.body.append(dialog);
  }
  document.addEventListener('input',(event)=>{
    if(!cfg||!event.target.closest('#composition-form'))return;
    const e=event.target,d=draft(),chainIndex=e.closest('[data-recipe-chain]')?.dataset.recipeChain,partIndex=e.closest('[data-recipe-part]')?.dataset.recipePart;
    const chain=d.definition.chains[chainIndex],part=chain?.components[partIndex];
    const top={'composition-name':'name','composition-external':'external_id','composition-format':'format','composition-note':'note','composition-reason':'reason'};
    if(top[e.id])d.definition[top[e.id]]=e.value||(['note','reason'].includes(top[e.id])?null:'');
    else if(e.dataset.chainField)chain[e.dataset.chainField]=e.dataset.chainField==='copies'&&e.value!==''?Number(e.value):e.value;
    else if(e.dataset.partField){if(e.dataset.partField==='id'){d.issuedComponentIds.add(part.id);d.issuedComponentIds.add(e.value);}part[e.dataset.partField]=e.value;}
    else if(e.hasAttribute('data-source-start'))part.source.start=e.value===''?'':Number(e.value);
    else if(e.hasAttribute('data-source-end'))part.source.end=e.value===''?'':Number(e.value);
    else if(e.hasAttribute('data-part-sequence'))part.source.sequence=e.value;
    else return;
    d.revision++;
  });
  document.addEventListener('toggle',(event)=>{if(cfg&&event.target.id==='composition-design'&&event.target.isConnected){state().compositionOpen=event.target.open;cfg.remember();}},true);
  document.addEventListener('change',(event)=>{
    if(!cfg||!cfg.bundle())return;const e=event.target,d=draft();
    if(e.dataset.unitSelect){state().selectedUnits=e.checked?[...new Set([...state().selectedUnits,e.dataset.unitSelect])]:state().selectedUnits.filter((id)=>id!==e.dataset.unitSelect);cfg.render();return;}
    if(e.dataset.compositionCompare){state()[e.dataset.compositionCompare==='left'?'compositionCompareLeft':'compositionCompareRight']=e.value;cfg.render();return;}
    if(!e.closest('#composition-form'))return;
    const i=e.closest('[data-recipe-chain]')?.dataset.recipeChain,j=e.closest('[data-recipe-part]')?.dataset.recipePart,p=d.definition.chains[i]?.components[j];
    if(e.hasAttribute('data-part-source-kind'))p.source=e.value==='sequence'?{kind:'sequence',sequence:''}:{kind:'binding_unit',binding_unit_id:'',chain_id:'',start:'',end:''};
    else if(e.hasAttribute('data-part-unit'))Object.assign(p.source,{binding_unit_id:e.value,chain_id:'',start:'',end:''});
    else if(e.hasAttribute('data-part-source-chain'))Object.assign(p.source,{chain_id:e.value,start:'',end:''});
    else if(e.dataset.connectionSide){if(e.value)d.definition.connections[e.closest('[data-recipe-connection]').dataset.recipeConnection][e.dataset.connectionSide]=JSON.parse(e.value);}
    else if(e.hasAttribute('data-connection-kind'))d.definition.connections[e.closest('[data-recipe-connection]').dataset.recipeConnection].kind=e.value;
    else if(e.dataset.chainField||e.dataset.partField){
      document.querySelectorAll('[data-connection-side]').forEach((select)=>{const connection=d.definition.connections[select.closest('[data-recipe-connection]').dataset.recipeConnection];select.innerHTML=endpointOptions(JSON.stringify(connection[select.dataset.connectionSide]));});return;
    }
    else return;
    d.revision++;cfg.render();
  });
  document.addEventListener('submit',async(event)=>{
    if(event.target.id!=='composition-form'||!cfg)return;event.preventDefault();ensureDialog();
    const d=draft(),project=cfg.bundle().project.id,revision=d.revision,ticket=++previewRequest,scope=intent(),gen=generation;
    const submit=event.submitter;if(submit)submit.disabled=true;
    try{const reviewed=await cfg.api('/api/composition-review',{project_id:project,definition:structuredClone(d.definition)}),result=reviewed.bundle;
      if(ticket!==previewRequest||gen!==generation||project!==cfg.bundle().project.id||d!==draft()||revision!==d.revision||scope!==intent())return;
      activePreview={bundle:result,project,draft:d,revision,ticket,scope};
      document.querySelector('#composition-preview-content').innerHTML=`<p>New distinct Molecule with ${result.entities[0].chains.length} chain definitions. Parent/source measurements, structures and numbering are not inherited. Connections are declarations; no physical assembly or chemical validity is established.</p>${contextPanel(reviewed.context,false)}<pre>${cfg.pretty(result)}</pre>`;
      document.querySelector('#save-composition').disabled=false;document.querySelector('#composition-preview-dialog').showModal();
    }catch(error){if(ticket===previewRequest&&scope===intent()&&d===draft()&&revision===d.revision)cfg.notify(error.message,true);}
    finally{if(submit?.isConnected)submit.disabled=false;}
  });
  document.addEventListener('click',async(event)=>{
    const b=event.target.closest('button');if(!cfg||!cfg.bundle()||!b||b.disabled)return;
    const holder=b.closest('[data-recipe-chain]'),i=Number(holder?.dataset.recipeChain),j=Number(b.closest('[data-recipe-part]')?.dataset.recipePart);let changed=false;
    let ownsError=()=>true,saveCommitted=false;
    try{
      if(b.dataset.designTask){DesignUI.invalidate();invalidate();state().designTask=b.dataset.designTask;cfg.render();}
      else if(b.hasAttribute('data-composition-start')){state().designTask='composition';state().compositionOpen=true;state().screen='D';cfg.render();}
      else if(b.hasAttribute('data-chain-add')){draft().definition.chains.push({id:'',role:'',copies:'',components:[]});changed=true;}
      else if(b.dataset.chainRemove!==undefined){draft().definition.chains.splice(Number(b.dataset.chainRemove),1);changed=true;}
      else if(b.dataset.partAdd!==undefined){const holder=draft(),d=holder.definition,used=new Set([...holder.issuedComponentIds,...d.chains.flatMap((c)=>c.components.map((p)=>p.id))]);let n=1;while(used.has('part-'+n))n++;holder.issuedComponentIds.add('part-'+n);d.chains[Number(b.dataset.partAdd)].components.push({id:'part-'+n,role:'',source:{kind:'binding_unit',binding_unit_id:'',chain_id:'',start:'',end:''}});changed=true;}
      else if(b.hasAttribute('data-source-full')){const p=draft().definition.chains[i].components[j],source=find(p.source.binding_unit_id)?.chains.find((c)=>c.id===p.source.chain_id);if(source){p.source.start=1;p.source.end=source.sequence.length;changed=true;}}
      else if(b.hasAttribute('data-part-up')||b.hasAttribute('data-part-down')){const parts=draft().definition.chains[i].components,k=j+(b.hasAttribute('data-part-up')?-1:1);if(k>=0&&k<parts.length){[parts[j],parts[k]]=[parts[k],parts[j]];changed=true;}}
      else if(b.hasAttribute('data-part-remove')){draft().definition.chains[i].components.splice(j,1);changed=true;}
      else if(b.hasAttribute('data-connection-add')){draft().definition.connections.push({left:{chain_id:'',component_id:''},right:{chain_id:'',component_id:''},kind:''});changed=true;}
      else if(b.dataset.connectionRemove!==undefined){draft().definition.connections.splice(Number(b.dataset.connectionRemove),1);changed=true;}
      else if(b.hasAttribute('data-composition-close')){previewRequest++;document.querySelector('#composition-preview-dialog').close();}
      else if(b.dataset.inspectComposition){const id=b.dataset.inspectComposition;if(!state().selected.includes(id))state().selected.push(id);state().focus=id;state().screen='W';cfg.render();}
      else if(b.dataset.copyComposition){
        const m=find(b.dataset.copyComposition);if(!m?.component_graph)throw Error('Composition undefined; no recipe is inferred.');
        const chains=m.component_graph.chains.map((c)=>({id:c.chain_id,role:m.chains.find((x)=>x.id===c.chain_id).role,copies:c.copies,components:c.components.map((p)=>({id:p.id,role:p.role,source:p.origin?{kind:'binding_unit',...structuredClone(p.origin)}:{kind:'sequence',sequence:p.sequence}}))}));
        drafts.set(cfg.bundle().project.id,{revision:0,issuedComponentIds:new Set(chains.flatMap((c)=>c.components.map((p)=>p.id))),definition:{name:'',external_id:'',format:m.format,parent_id:m.id,reason:null,note:null,chains,connections:structuredClone(m.component_graph.connections)}});state().compositionParent=m.id;state().designTask='composition';state().compositionOpen=true;state().screen='D';cfg.render();
      } else if(b.id==='save-composition'){
        const pending=activePreview;if(!pending)throw Error('Review a composition before saving.');b.disabled=true;
        ownsError=()=>pending.project===cfg.bundle()?.project.id&&activePreview===pending&&pending.ticket===previewRequest&&pending.draft===draft()&&pending.revision===draft().revision&&pending.scope===intent();
        await cfg.api('/api/import',pending.bundle);
        saveCommitted=true;
        const same=pending.project===cfg.bundle().project.id,owned=same&&activePreview===pending&&pending.ticket===previewRequest&&pending.draft===draft()&&pending.revision===draft().revision&&pending.scope===intent();
        if(owned){const id=pending.bundle.entities[0].id;drafts.set(pending.project,empty());state().compositionParent=null;state().compositionCurrent=id;state().compositionOpen=false;state().compositionCompareRight=id;if(pending.bundle.entities.some((e)=>e.type==='lineage'))state().compositionCompareLeft=pending.bundle.entities.find((e)=>e.type==='lineage').parent_id;if(!state().selected.includes(id))state().selected.push(id);activePreview=null;document.querySelector('#composition-preview-dialog').close();}
        if(same)await cfg.reload();cfg.notify(owned?'Saved distinct composition and explicit source origins. No measurements or physical assembly are inferred.':'Submitted composition saved; the newer selection and draft were retained.');
      }
      if(changed){draft().revision++;cfg.render();}
    }catch(error){if(saveCommitted)cfg.notify('Composition saved; reload the workspace to refresh the view.');else if(ownsError()){cfg.notify(error.message,true);if(b.isConnected)b.disabled=false;}}
  });
  return {configure(options){cfg=options;},available(){return units().length>0||records().some((e)=>e.type==='molecule'&&e.component_graph);},explorer,panel,mount,invalidate};
})();
