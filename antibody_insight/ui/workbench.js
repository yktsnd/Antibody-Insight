"use strict";
const by = id => document.getElementById(id);
const api = () => window.pywebview.api;
const node = (tag, text) => {
  const el = document.createElement(tag);
  if (text != null) el.textContent = text;
  return el;
};
const opt = (label, value) => new Option(label, value);
const safeLabel = text => String(text).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
let project, view, detail, reference, coordinates, viewer, structureScript, packet;
let alignment=null, aligning=false;
let ticket = 0, modelTicket = 0, refTicket = 0, pendingSave = Promise.resolve();
let queuedView = null, saving = false;
let metricGroups = [], plotDraw = Promise.resolve();
let comparison=null, comparisonTicket=0;
let plotTicket=0, renderedPlot=null;
let fixedModel, movingModel, overlayFit, overlayTicket=0;
let parallelViewer, movingViewer, syncingCamera=false;
const seriesKey=r=>JSON.stringify([r.metric,r.unit,r.kind,r.conditions,r.source,...(r.region?[r.region]:[])]);
const msg = text => { by("status").textContent = text; };
const report = error => {
  const message = error?.message || String(error);
  msg(message);
  if (by("importDialog").open) by("importError").textContent = message;
};
function action(id, fn, event="click") {
  by(id).addEventListener(event, e => Promise.resolve().then(() => fn(e)).catch(report));
}
function save() {
  if (!project) return Promise.resolve();
  queuedView = {session:project.session, snapshot:structuredClone(view)};
  if (!saving) {
    saving = true;
    pendingSave = (async () => {
      try {
        while (queuedView) {
          const write = queuedView;
          queuedView = null;
          await api().save_view(write.session, write.snapshot);
        }
      } finally { saving = false; }
    })();
  }
  return pendingSave;
}
function selectedComponent() {return project?.components.find(r => r.id === view.component);}
function owner(id) {return project.candidates.find(c => c.id === id)?.label || "";}
function setProject(data) {
  ticket++; refTicket++; modelTicket++;
  project = data; detail = reference = coordinates = alignment = null;
  aligning=false;
  view = {component:null, position:1, reference:"", metric:"", model:"", style:"Stick", cameras:{}, note:"", ...data?.state};
  by("projectTitle").textContent = data?.title || "No project open";
  by("import").disabled = by("note").disabled = by("bookmarks").disabled = !data;
  by("export").disabled = true;
  by("filter").value = ""; by("count").textContent = data ? String(data.candidates.length) : "";
  prepareMetric(); drawTree(); drawSequence(); clearModel(); drawPlot();
  if (data && selectedComponent()) return select(view.component, true);
  msg(data ? "Choose a component or import local data." : "Open a project or explore the synthetic example.");
}
async function openProject(mode) {
  await pendingSave;
  const data = await api().open_project(mode);
  if (data) await setProject(data);
}
function drawTree() {
  const tree = by("tree");
  const open = new Set([...tree.querySelectorAll("details[open]")].map(r => r.dataset.key));
  tree.replaceChildren();
  if (!project) return;
  const needle = by("filter").value.toLowerCase();
  const groups = new Map();
  for (const component of project.components) {
    if (!groups.has(component.candidate)) groups.set(component.candidate,[]);
    groups.get(component.candidate).push(component);
  }
  const means=new Map();
  for(const summary of selectedSummaries()){
    if(!means.has(summary.candidate))means.set(summary.candidate,[]);
    means.get(summary.candidate).push(summary);
  }
  for (const c of project.candidates) {
    const parts = groups.get(c.id) || [];
    if (![c.label,...parts.map(x=>x.label)].some(s => s.toLowerCase().includes(needle))) continue;
    const group = node("details"), head = node("summary");
    group.className = "candidate"; group.dataset.key = c.id;
    group.open = open.has(c.id) || parts.some(p=>p.id===view.component) || project.candidates.length <= 5;
    head.textContent = c.label; group.append(head);
    for (const summary of means.get(c.id)||[]){
      const label=node("small"," · "+(summary.value??"Missing")+" "+summary.unit);
      const basis=summary.origin?summary.origin+" mean":summary.sample;
      label.title=[summary.metric,basis,summary.replicate_set,summary.conditions].filter(Boolean).join(" · ");
      head.append(label);
    }
    for (const part of parts) {
      const btn = node("button",part.label); btn.className="part"; btn.dataset.key=part.id;
      btn.setAttribute("aria-current",String(part.id===view.component));
      btn.append(node("small",part.size+" "+(part.kind==="DNA"?"nt":"aa")));
      btn.onclick = () => select(part.id).catch(report); group.append(btn);
    }
    tree.append(group);
  }
}
async function select(id, restore=false, position=1, feature=null, compareWith="", referenceSource=null) {
  const item = project.components.find(c=>c.id===id);
  if (!item) return;
  const token = ++ticket; refTicket++; modelTicket++;
  const previous = view.component;
  view.component = id;
  if (!restore && previous !== id) {
    view.position=position;view.model="";view.reference=compareWith;view.cdsFeature=feature;
    view.alignRecords=Boolean(compareWith);view.alignmentWindow=null;view.referenceSource=referenceSource;
  }
  reference = detail = coordinates = alignment = null;aligning=false;
  drawTree(); clearModel(); drawSequence(); drawPlot(); by("export").disabled=true;
  const result = await api().inspect(project.session,id);
  if (token!==ticket) return;
  detail = result;
  view.position = Math.max(1,Math.min(detail.seq.length,parseInt(view.position)||1));
  const candidates = project.components.filter(c => c.id !== id && c.kind === item.kind);
  by("reference").replaceChildren(opt("None",""),...candidates.map(c=>opt(owner(c.candidate)+" / "+c.label,c.id)));
  if (!candidates.some(c=>c.id===view.reference)) view.reference="";
  by("reference").value=view.reference;
  const files=detail.structures;
  if (!files.some(r=>r.id===view.model)) view.model=files[0]?.id || "";
  by("model").replaceChildren(...files.map(r=>opt([r.filename,r.origin,r.chain?"Chain "+r.chain:"Unmapped"].join(" · "),r.id)));
  by("model").value=view.model; by("style").value=view.style;
  by("export").disabled=false;
  drawSequence(); msg(owner(item.candidate)+" / "+item.label);
  await Promise.all([readReference(),readModel(),save()]);
}
async function readReference() {
  const version=++refTicket, key=view.reference;
  reference=alignment=null;aligning=false;
  if(key) {
    const result=await api().inspect(project.session,key);
    if(version!==refTicket) return;
    reference=result;
  }
  drawSequence();
  if(reference && view.alignRecords)await alignRecords();
}
async function alignRecords() {
  const version=refTicket, session=project.session, query=detail.id, ref=reference.id;
  aligning=true;drawSequence();
  try {
    const result=await api().align(session,query,ref);
    if(version!==refTicket)return;
    alignment=result;view.alignRecords=true;
    await save();
  } finally {
    if(version===refTicket){aligning=false;drawSequence();}
  }
}
function at(position) {
  if (!detail || !Number.isInteger(position) || position<1 || position>detail.seq.length) return;
  view.position=position;view.alignmentWindow=null;drawSequence();highlight();save().catch(report);
}
function sequenceWindow(){
  const length=detail.seq.length;
  const requested=view.windowSpans?.[detail.id];
  const width=Math.min(length,Math.max(1,Math.round(requested)||96));
  const centered=view.position-1-Math.floor((width-1)/2);
  const start=requested?Math.max(0,Math.min(length-width,centered)):Math.floor((view.position-1)/width)*width;
  return {width,start,end:Math.min(length,start+width)};
}
function setWindow(width){
  if(!detail)return;
  view.windowSpans??={};
  view.windowSpans[detail.id]=Math.max(1,Math.min(detail.seq.length,width));
  drawSequence();
  save().catch(report);
}
function drawFeatureScale(body,start,end){
  const pane=node("div");pane.className="feature-scale";
  const ruler=node("button");ruler.type="button";ruler.className="coordinate-ruler";
  ruler.title="Choose a position on the sequence";ruler.setAttribute("aria-label","Select a position on the visible sequence");
  const marker=node("i");
  marker.style.left=(100*(view.position-start-.5)/(end-start))+"%";ruler.append(marker);
  ruler.onclick=event=>{
    const rect=ruler.getBoundingClientRect();
    if(event.detail)at(start+1+Math.max(0,Math.min(end-start-1,Math.floor((event.clientX-rect.left)*(end-start)/rect.width))));
    else by("pos").focus();
  };
  pane.append(ruler);
  for(const [index,feature] of detail.features.entries()){
    const parts=feature.parts.filter(([low,high])=>high>start && low<=end);
    if(!parts.length)continue;
    const label=feature.label===feature.type?feature.type:feature.label+" · "+feature.type;
    const row=node("div"), title=node("span",label);row.className="feature-row";
    title.title=feature.type;row.append(title);
    for(const [low,high,strand] of parts){
      const left=Math.max(start,low-1),right=Math.min(end,high);
      const bar=node("button");bar.className="feature-bar";bar.dataset.feature=index;bar.dataset.low=low;
      bar.title=feature.label+" · "+low+"–"+high+(strand===1?" (+)":strand===-1?" (−)":"");
      bar.setAttribute("aria-label",bar.title);
      bar.style.left=100*(left-start)/(end-start)+"%";bar.style.width=100*(right-left)/(end-start)+"%";
      if(feature.type==="CDS")bar.classList.add("cds-bar");
      if(view.position>=low && view.position<=high)bar.classList.add("at-position");
      bar.onclick=()=>{if(feature.type==="CDS")view.cdsFeature=index;at(strand===-1?right:left+1);};
      row.append(bar);
    }
    pane.append(row);
  }
  body.append(pane);
}
function drawSequence() {
  const body=by("sequenceBody"); body.replaceChildren();
  updateNumbering();
  by("identity").textContent=detail ? owner(detail.candidate)+" / "+detail.label : "";
  by("pos").disabled=by("reference").disabled=by("prev").disabled=by("next").disabled=!detail;
  by("seqScale").hidden=!detail||Boolean(alignment)||(detail.kind==="AA"&&view.numberingOpen);
  if(!detail) {body.append(node("p","Select a component to inspect its sequence."));return;}
  const seq=detail.seq, pos=view.position;
  const {start,end,width}=sequenceWindow();
  by("sequenceZoom").value=seq.length===1?1000:Math.round(1000*(1-Math.log(width)/Math.log(seq.length)));
  const rangeText=(start+1)+"–"+end+(detail.kind==="DNA"?" nt":" aa");
  by("sequenceZoom").setAttribute("aria-valuetext",rangeText);
  by("visibleRange").textContent=rangeText;
  const positionField=by("pos"), positionKey=detail.id+"|"+pos;
  if(positionField.dataset.position!==positionKey || document.activeElement!==positionField){
    positionField.value=pos;positionField.dataset.position=positionKey;
  }
  positionField.max=seq.length;
  by("prev").disabled=start===0;by("next").disabled=end>=seq.length;
  const meta=node("div",detail.kind+" · "+seq.length+(detail.kind==="DNA"?" nt":" aa")+
    (detail.topology?" · "+detail.topology:"")+(reference && !alignment?" · differences at unaligned record positions":""));
  meta.className="sequence-meta";body.append(meta);
  const codingFeatures=detail.features.map((f,index)=>({f,index})).filter(({f})=>f.type==="CDS");
  if(!alignment && width>96)drawFeatureScale(body,start,end);
  const zoomedLetters=!alignment && width<=96 && Boolean(view.windowSpans?.[detail.id]);
  if(codingFeatures.length && !zoomedLetters && (alignment||width<=96))drawCoding(body,codingFeatures);
  const row=(s,offset,other,isReference)=>{
    const line=node("div"); line.className="sequence-line";
    line.append(node("span",isReference?"Ref":String(offset+1)));
    for(let i=offset;i<Math.min(offset+24,end);i++){
      const base=node("button",s[i] || "–");base.className="base";
      if(!isReference)base.dataset.base=i+1;
      if(other && s[i]!==other[i]) base.classList.add("diff");
      base.setAttribute("aria-pressed",String(i+1===pos));
      base.title=(isReference?"Reference":"Selected")+" position "+(i+1);
      base.onclick=()=>at(i+1);line.append(base);
    }
    body.append(line);
  };
  if(alignment && reference) drawAlignment(body);
  else {
    for(let i=start;width<=96 && i<end;i+=24){
      row(seq,i,reference?.seq,false); if(reference) row(reference.seq,i,seq,true);
    }
    if(codingFeatures.length && zoomedLetters)drawCoding(body,codingFeatures);
    if(reference){
      const align=node("button",aligning?"Aligning…":"Align sequences");
      align.disabled=aligning;align.onclick=()=>alignRecords().catch(report);
      body.append(align,node("small"," Reference · "+owner(reference.candidate)+" / "+reference.label));
    }
  }
  if(view.referenceSource && view.referenceSource.reference===detail.id){
    const link=view.referenceSource, other=project.components.find(c=>c.id===link.query);
    if(other){
      const back=node("button","Return to aligned candidate");
      back.onclick=async()=>{
        const version=ticket, position=view.position;
        try{
          const a=await api().align(project.session,other.id,detail.id);
          if(version!==ticket || position!==view.position)return;
          const q=a.unique && a.columns.find(([,r])=>r===position)?.[0];
          if(!q){msg("This reference position has no unique aligned candidate residue.");return;}
          await select(other.id,false,q,null,detail.id);
        }catch(error){report(error);}
      };
      body.append(node("p","Reference for "+owner(other.candidate)+" / "+other.label),back);
    }
  }
  if(detail.kind==="AA" && view.codingLink?.protein===detail.id){
    const back=node("button","Go to source codon");
    back.onclick=async()=>{
      const link=view.codingLink, active=ticket, position=view.position, session=project.session;
      try {
        const targets=await api().protein_targets(session,link.dna,link.feature);
        if(active!==ticket || view.position!==position)return;
        const target=targets.find(c=>c.id===detail.id && c.region===(link.region??null));
        if(!target)throw new Error("The saved CDS correspondence is unavailable.");
        const precursor=target.start+position-1;
        const ctx=await api().codons(session,link.dna,link.feature,null,precursor);
        if(active!==ticket || view.position!==position)return;
        const row=ctx.rows.find(r=>r.index===precursor);
        await select(link.dna,false,row.bases[0],link.feature);
      } catch(error){report(error);}
    };
    body.append(back);
  }
  if(detail.features.length){
    const list=node("details"), title=node("summary","Annotations ("+detail.features.length+")");
    list.append(title);
    for(const f of detail.features){
      const line=node("div"), go=node("button",f.label+" · "+f.type);
      go.disabled=!f.parts.length; go.onclick=()=>at(f.parts[0][2]===-1?f.parts[0][1]:f.parts[0][0]);
      line.append(go,node("small"," "+(featureSpans(f).join(", ")||f.location)));
      if(f.open_peptide_end)line.append(node("small"," · annotated peptide extends beyond this span"));
      if(f.translation_issue) line.append(node("p",f.translation_issue));
      list.append(line);
    }
    body.append(list);
  }
  const info=node("details");info.append(node("summary","Source"),node("p",detail.filename+" · SHA-256 "+detail.hash),node("p","Imported "+detail.imported));body.append(info);
}
function drawAlignment(body) {
  const a=alignment, index=a.columns.findIndex(([q])=>q===view.position);
  const width=24;
  const start=Math.max(0,Math.min(a.columns.length-1,view.alignmentWindow??(Math.floor(Math.max(0,index)/width)*width)));
  const stop=Math.min(a.columns.length,start+width);
  const strip=node("div");strip.className="strip";
  const identity=a.paired?(100*a.matches/a.paired).toFixed(1)+"%":"Unavailable";
  strip.append(node("strong",identity+" letter identity"),
    node("small",a.matches+"/"+a.paired+" paired columns · "+(a.columns.length-a.paired)+" gap columns"));
  const raw=node("button","Raw positions");
  raw.onclick=()=>{alignment=null;view.alignRecords=false;drawSequence();save().catch(report);};
  strip.append(raw);body.append(strip);
  for(const [label,n,record] of [["Query",0,detail],["Ref",1,reference]]){
    const line=node("div");line.className="sequence-line";line.append(node("span",label));
    for(let i=start;i<stop;i++){
      const pair=a.columns[i], p=pair[n], q=pair[0], r=pair[1];
      const btn=node("button",p===null?"–":record.seq[p-1]);btn.className="base";
      if(q===null || r===null || detail.seq[q-1]!==reference.seq[r-1])btn.classList.add("diff");
      btn.disabled=q===null;btn.setAttribute("aria-pressed",String(q===view.position));
      btn.title="Column "+(i+1)+" · query "+(q??"gap")+" · reference "+(r??"gap");
      if(q!==null)btn.onclick=()=>at(q);
      line.append(btn);
    }
    body.append(line);
  }
  const nav=node("div");nav.className="strip";
  for(const [name,offset] of [["Previous columns",-width],["Next columns",width]]){
    const b=node("button",name);b.disabled=offset<0?start===0:stop===a.columns.length;
    b.onclick=()=>{view.alignmentWindow=Math.max(0,start+offset);drawSequence();save().catch(report);};nav.append(b);
  }
  nav.append(node("small","Columns "+(start+1)+"–"+stop+" of "+a.columns.length));body.append(nav);
  const r=a.columns[index]?.[1];
  if(!a.unique)body.append(node("p","Multiple optimal alignments · one displayed. Residue transfer unavailable."));
  else if(r==null)body.append(node("p","Selected query residue aligns to a gap in the reference."));
  else {
    const inspect=node("button","Inspect aligned reference");
    inspect.onclick=()=>select(reference.id,false,r,null,"",{query:detail.id,reference:reference.id}).catch(report);
    body.append(node("span","Query "+view.position+" "+detail.seq[view.position-1]+" → reference "+r+" "+reference.seq[r-1]+" "),inspect);
  }
  const methods=node("details");methods.append(node("summary","Alignment method"),node("p",a.method),
    node("p","Identity counts exact letter matches in columns containing two letters. Ambiguous letters retain their input symbols."));
  body.append(methods);
}
function drawCoding(body, features) {
  const strip=node("div"), label=node("label","CDS "), choose=node("select");
  strip.className="strip coding-controls";choose.id="cdsFeature";
  choose.append(opt("Select an annotation",""),...features.map(({f,index})=>{
    const spans=featureSpans(f);
    return opt(f.label+" · "+(spans.join(", ")||"coordinates unavailable"),index);
  }));
  const current=features.find(({index})=>index===view.cdsFeature) || (features.length===1?features[0]:null);
  choose.value=current ? String(current.index) : "";
  choose.onchange=()=>{view.cdsFeature=choose.value===""?null:Number(choose.value);drawSequence();save().catch(report);};
  label.append(choose);strip.append(label);body.append(strip);
  if(!current)return;
  if(!current.f.coding){body.append(node("small",current.f.translation_issue||"Codon correspondence unavailable for this CDS."));return;}
  const pane=node("div");pane.className="coding-track";body.append(pane);
  const jump=node("input"), jumpLabel=node("label","Translation position ");
  jump.type="number";jump.min=1;jump.max=current.f.translation.length+(current.f.coding.terminal_stop===false?0:1);jump.id="translationPosition";
  jumpLabel.append(jump);strip.append(jumpLabel);
  const request = async (residue=null) => {
    const context=await api().codons(project.session,detail.id,current.index,view.position,residue);
    if(!pane.isConnected)return;
    if(residue!==null) {
      const row=context.rows.find(r=>r.index===residue);
      if(row)at(row.bases[0]);
      return;
    }
    jump.value=context.selected??"";
    const active=context.rows.find(r=>r.index===context.selected);
    const summary=node("p",active?
      (active.aa==="*"?"Stop codon":"Translation "+active.index+" · "+active.aa)+" · "+active.codon+" · DNA ":
      "Selected base is outside the translated codons.");
    if(active) active.bases.forEach((base,index)=>{
      if(index)summary.append(", ");
      const jumpBase=node("button",base);jumpBase.className="base-link";
      jumpBase.title="Go to DNA base "+base;jumpBase.onclick=()=>at(base);summary.append(jumpBase);
    });
    summary.id="codonIdentity";pane.append(summary);
    if(active)for(const n of active.bases)body.querySelector('[data-base="'+n+'"]')?.classList.add("in-codon");
    const track=node("div");track.className="codons";
    for(const row of context.rows) {
      const btn=node("button");btn.type="button";btn.dataset.codon=row.index;
      btn.setAttribute("aria-pressed",String(row.index===context.selected));
      btn.setAttribute("aria-label",(row.aa==="*"?"Stop":"Residue "+row.index+" "+row.aa)+" · "+row.codon+" · DNA "+row.bases.join(", "));
      btn.append(node("small",row.index),node("strong",row.aa),node("code",row.codon));
      btn.onclick=()=>at(row.bases[0]);track.append(btn);
    }
    pane.append(track,node("small","Coding strand "+(current.f.parts[0][2]===1?"+":"−")+" · codon_start "+
      (current.f.coding.frame_offset+1)+" · translation table "+current.f.coding.table+
      (current.f.coding.terminal_stop===false?" · deposited segment "+current.f.coding.protein_id+" · no terminal stop":"")));
    if(!active || active.aa==="*")return;
    for(const region of current.f.mature_fragments||[]){
      if(active.index>=region.start && active.index<=region.end){
        const fragment=node("p","Mature peptide · position "+(active.index-region.start+1)+" · annotated end unresolved");
        fragment.className="mature-fragment";pane.append(fragment);
      }
    }
    for(const region of current.f.mature_regions||[]){
      if(active.index<region.start || active.index>region.end)continue;
      const f=detail.features[region.feature_index], info=node("div");info.className="strip mature-region";
      info.append(node("span","Annotated mature peptide · "+f.label+" · position "+(active.index-region.start+1)));
      const button=node("button","Export mature FASTA…");
      button.onclick=async()=>{
        try{if(await api().export_peptide(project.session,detail.id,current.index,region.feature_index))msg("Annotated mature peptide exported.");}
        catch(error){report(error);}
      };
      info.append(button);pane.append(info);
    }
    detail.proteinTargets ??= new Map();
    if(!detail.proteinTargets.has(current.index)){
      detail.proteinTargets.set(current.index,api().protein_targets(project.session,detail.id,current.index));
    }
    const targets=await detail.proteinTargets.get(current.index);
    const applicable=targets.filter(c=>active.index>=c.start && active.index<=c.end);
    if(!pane.isConnected || !applicable.length)return;
    const links=node("div");links.className="strip";
    links.append(node("small","Matching protein in this candidate"));
    for(const c of applicable){
      const position=active.index-c.start+1;
      const btn=node("button","Inspect "+c.label+(c.region===null?"":" · mature "+position));
      btn.onclick=()=>{
        view.codingLink={dna:detail.id,feature:current.index,protein:c.id,region:c.region};
        select(c.id,false,position).catch(report);
      };
      links.append(btn);
    }
    pane.append(links);
  };
  jump.onchange=()=>{if(jump.checkValidity() && jump.value)request(Number(jump.value)).catch(report);};
  request().catch(error=>{if(pane.isConnected)report(error);});
}
function clearModel() {
  ++modelTicket; coordinates=null;
  ++overlayTicket;overlayFit=movingModel=fixedModel=null;
  resetParallel();
  by("overlayControls").hidden=true;by("focusResidue").disabled=true;
  by("structureMetrics").disabled=true;
  by("exportStructure").disabled=true;
  const query=project?.components.find(c=>c.id===view.referenceSource?.query);
  const showingReference=query && view.component===view.referenceSource.reference;
  by("referenceScope").hidden=!showingReference;
  by("referenceScope").textContent=showingReference?"Reference coordinates for "+owner(query.candidate)+" / "+query.label:"";
  if(viewer){viewer.setViewChangeCallback(null);viewer.clear();viewer.render();}
  by("coordinate").textContent="";by("model").replaceChildren();by("fit").disabled=by("style").disabled=true;
  if(!viewer) by("molecule").replaceChildren(node("span","No coordinates selected."));
}
function library() {
  if(!structureScript) structureScript=new Promise((resolve,reject)=>{
    const script=node("script");script.src="vendor/3dmol/3Dmol-min.js";
    script.onload=resolve;script.onerror=()=>reject(new Error("The local structure viewer could not load."));document.head.append(script);
  });
  return structureScript;
}
async function readModel(){
  const key=view.model, token=++modelTicket;coordinates=null;
  ++overlayTicket;overlayFit=movingModel=fixedModel=null;
  resetParallel();
  by("overlayControls").hidden=true;by("focusResidue").disabled=true;
  by("structureMetrics").disabled=true;
  by("exportStructure").disabled=true;
  if(viewer){viewer.setViewChangeCallback(null);viewer.clear();viewer.render();}
  by("fit").disabled=by("style").disabled=true;
  if(!key){by("coordinate").textContent="No coordinates registered";return;}
  by("coordinate").textContent="Loading coordinates…";
  const [data,,catalog]=await Promise.all([
    api().coordinates(project.session,view.component,key),library(),api().model_catalog(project.session)]);
  if(token!==modelTicket)return;
  const holder=by("molecule");
  if(!viewer){holder.replaceChildren();viewer=$3Dmol.createViewer(holder,{backgroundColor:"#f4f8f7"});}
  const model=viewer.addModel(data.display_pdb,"pdb");coordinates=data;fixedModel=model;
  if(data.mapping.length){
    model.setClickable({chain:data.chain,hetflag:false},true,atom=>{
      if(atom.hetflag)return;
      const index=data.mapping.findIndex(r=>r && r[0]===atom.resi && r[1]===(atom.icode||"").trim());
      if(index>=0) at(index+1);
    });
  }
  by("fit").disabled=by("style").disabled=by("structureMetrics").disabled=false;
  if(view.cameras[key])viewer.setView(view.cameras[key]);
  else{
    viewer.setView([0,0,0,0,0,0,0,1]);
    viewer.zoomTo();
  }
  highlight();
  by("exportStructure").disabled=false;
  let observedCamera=viewer.getView();
  viewer.setViewChangeCallback(camera=>{
    if(token!==modelTicket || !camera.every(Number.isFinite))return;
    if(camera.every((value,i)=>value===observedCamera[i]))return;
    observedCamera=camera.slice();
    view.cameras[key]=camera.slice();
    syncStructureCamera(viewer,parallelViewer,camera);
    save().catch(report);
  });
  const choices=catalog.filter(row=>row.id!==key);
  if(data.mapping.length && choices.length){
    by("movingModel").replaceChildren(opt("Overlay structure…",""),...choices.map(row=>{
      const part=project.components.find(c=>c.id===row.component);
      return opt(owner(part.candidate)+" / "+part.label+" · "+row.filename+" · "+row.origin+" · "+(row.chain.trim()||"Blank chain"),
                 JSON.stringify([row.component,row.id]));
    }));
    by("overlayControls").hidden=false;
    const saved=view.overlays?.[key];
    by("movingModel").value=choices.some(row=>JSON.stringify([row.component,row.id])===saved?.target)?saved.target:"";
    by("fitFirst").value=saved?.bounds?.[0]??"";
    by("fitLast").value=saved?.bounds?.[1]??"";
    by("fitSummary").textContent="";
    by("toggleOverlay").hidden=!by("movingModel").value;
    await readOverlay();
  }
}
async function readOverlay(){
  const version=++overlayTicket, key=view.model, target=by("movingModel").value;
  if(movingModel)movingViewer.removeModel(movingModel);
  movingModel=overlayFit=null;
  resetParallel();
  by("toggleOverlay").hidden=true;
  by("structureLayout").hidden=true;
  by("overlayRange").hidden=!target;
  by("fitSummary").textContent=target?"Fitting matched Cα atoms…":"";
  highlight();
  if(!target || !fixedModel)return;
  let fit;
  try{
    const [component,id]=JSON.parse(target);
    fit=await api().overlay(project.session,view.component,key,component,id,view.overlays?.[key]?.bounds??null);
  }catch(error){
    if(version===overlayTicket)by("fitSummary").textContent=error.message||String(error);
    return;
  }
  if(version!==overlayTicket)return;
  overlayFit=fit;
  by("toggleOverlay").hidden=false;
  by("structureLayout").hidden=false;
  by("structureLayout").value=view.overlays[key].layout||"overlay";
  mountOverlay();
}
function resetParallel(){
  by("overlayMolecule").hidden=true;
  if(parallelViewer){
    parallelViewer.setViewChangeCallback(null);
    parallelViewer.clear();
    parallelViewer.render();
  }
}
function syncStructureCamera(source,target,camera){
  if(!target || syncingCamera || by("overlayMolecule").hidden)return;
  const current=target.getView();
  if(camera.every((v,i)=>current[i]===v))return;
  syncingCamera=true;
  try{
    target.setView(camera);
    target.render();
    if(source===parallelViewer){
      view.cameras[view.model]=camera.slice();
      save().catch(report);
    }
  }finally{syncingCamera=false;}
}
function mountOverlay(){
  if(!overlayFit)return;
  if(movingModel)movingViewer.removeModel(movingModel);
  const state=view.overlays[view.model],fit=overlayFit;
  resetParallel();
  movingViewer=viewer;
  if(state.layout==="parallel" && state.shown!==false){
    by("overlayMolecule").hidden=false;
    parallelViewer??=$3Dmol.createViewer(by("overlayMolecule"),{backgroundColor:"#f4f8f7"});
    parallelViewer.resize();
    parallelViewer.setView(viewer.getView());
    parallelViewer.setViewChangeCallback(camera=>syncStructureCamera(parallelViewer,viewer,camera));
    movingViewer=parallelViewer;
  }
  movingModel=movingViewer.addModel(fit.moving.display_pdb,"pdb");
  const matrix=fit.rotation, offset=fit.translation;
  for(const atom of movingModel.selectedAtoms({})){
    const point=[atom.x,atom.y,atom.z];
    [atom.x,atom.y,atom.z]=offset.map((value,j)=>value+point.reduce((sum,v,i)=>sum+v*matrix[i][j],0));
  }
  movingModel.setClickable({chain:fit.moving.chain,hetflag:false},true,atom=>{
    if(atom.hetflag)return;
    const moving=fit.moving.mapping.findIndex(r=>r && r[0]===atom.resi && r[1]===(atom.icode||"").trim())+1;
    const pair=fit.correspondence.find(([,b])=>b===moving);
    if(pair)at(pair[0]);
  });
  highlight();
}
function atomSelection(data,position){
  const key=data.mapping[position-1];
  return key && {chain:data.chain,resi:key[0],icode:key[1]||" ",hetflag:false};
}
function highlight(){
  if(!viewer || !fixedModel || !coordinates)return;
  const data=coordinates, mode=by("style").value.toLowerCase();
  const overlayShown=Boolean(movingModel && view.overlays?.[view.model]?.shown!==false);
  fixedModel.setStyle({},overlayShown?{}:{[mode]:{colorscheme:"Jmol"}});
  if(overlayShown)fixedModel.setStyle({chain:data.chain,hetflag:false},{[mode]:{color:"#398172"}});
  const r=data.mapping[view.position-1];
  if(r) fixedModel.setStyle(atomSelection(data,view.position),{stick:{color:"#d77217"},sphere:{scale:.3,color:"#d77217"}});
  by("focusResidue").disabled=!r;
  by("coordinate").textContent=r ? "Chain "+data.chain+" · "+r[0]+r[1]+" · sequence "+view.position :
    data.mapping.length ? "Chain "+data.chain+" · sequence "+view.position+" · no observed coordinates" : "Sequence correspondence unavailable";
  if(movingModel){
    const moving=overlayFit.moving, shown=view.overlays?.[view.model]?.shown!==false;
    const position=overlayFit.correspondence.find(([a])=>a===view.position)?.[1];
    const match=moving.mapping[position-1];
    movingModel.setStyle({},{});
    movingModel.setStyle({chain:moving.chain,hetflag:false},{[mode]:{color:"#4772b3",opacity:movingViewer===viewer ? .55 : 1}});
    if(match)movingModel.setStyle(atomSelection(moving,position),{stick:{color:"#235ac5"},sphere:{scale:.33,color:"#235ac5"}});
    if(shown)movingModel.show();else movingModel.hide();
    by("toggleOverlay").setAttribute("aria-pressed",String(shown));
    by("fitSummary").textContent=overlayFit.pairs.length+"/"+overlayFit.fit_positions+" paired positions with Cα · RMSD "+overlayFit.rmsd.toFixed(3)+" Å · "+
      (match?"Overlay "+moving.chain+" "+match[0]+match[1]:"No overlay coordinates at this position");
  }
  viewer.render();
  if(!by("overlayMolecule").hidden && parallelViewer)parallelViewer.render();
}
async function saveStructureImage(){
  if(!coordinates)return;
  const session=project.session,version=modelTicket;
  const caption=[owner(detail.candidate)+" / "+detail.label,coordinates.filename+" · "+coordinates.origin,
    by("coordinate").textContent,by("referenceScope").textContent].filter(Boolean);
  if(overlayFit && by("toggleOverlay").getAttribute("aria-pressed")==="true"){
    const bounds=overlayFit.bounds?overlayFit.bounds.join("–"):"all paired positions";
    caption.push("Overlay "+overlayFit.moving.filename+" · fit range "+bounds,by("fitSummary").textContent);
  }
  const images=await Promise.all((by("overlayMolecule").hidden?[viewer]:[viewer,parallelViewer]).map(async option=>{
    const image=new Image();
    image.src=option.pngURI();
    await image.decode();
    return image;
  }));
  if(version!==modelTicket)throw new Error("The displayed structure changed.");
  const canvas=node("canvas"),context=canvas.getContext("2d");
  context.font="16px Segoe UI, sans-serif";
  const width=images.reduce((sum,image)=>sum+image.width,0);
  const height=Math.max(...images.map(image=>image.height));
  canvas.width=Math.ceil(Math.max(width,...caption.map(s=>context.measureText(s).width+36)));
  canvas.height=height+26*caption.length+24;
  context.fillStyle="#f4f8f7";context.fillRect(0,0,canvas.width,canvas.height);
  let x=(canvas.width-width)/2;
  for(const image of images){
    context.drawImage(image,x,canvas.height-height);
    x+=image.width;
  }
  context.font="16px Segoe UI, sans-serif";context.fillStyle="#18383a";
  caption.forEach((line,i)=>context.fillText(line,18,26+i*26));
  if(await api().export_structure_image(session,canvas.toDataURL()))msg("Structure image saved.");
}
function bookmarkList(names){
  by("bookmarkList").replaceChildren(...names.map(n=>opt(n,n)));
  by("openBookmark").disabled=!names.length;
}
function prepareMetric(){
  const groups=new Map();
  for(const r of project?.observations||[]){
    const key=seriesKey(r);
    if(!groups.has(key))groups.set(key,[]); groups.get(key).push(r);
  }
  metricGroups=[...groups];const select=by("metric");
  select.replaceChildren(...metricGroups.map(([key,[r]])=>opt([r.metric,r.unit,r.kind,r.conditions||"conditions unknown",r.source,r.region].filter(Boolean).join(" · "),key)));
  select.append(opt("Component length · amino acids","AA"),opt("Component length · nucleotides","DNA"));
  if(![...select.options].some(o=>o.value===view.metric))view.metric=select.options[0].value;
  select.value=view.metric;
  prepareAxes();
}
function prepareAxes(){
  const x=by("xMetric"), y=by("metric");
  const options=[...y.options].filter(o=>metricGroups.some(([key])=>key===o.value)&&o.value!==view.metric);
  x.replaceChildren(opt("X · Candidate",""),...options.map(o=>opt("X · "+o.text,o.value)));
  if(!metricGroups.some(([key])=>key===view.metric)||!options.some(o=>o.value===view.xMetric))view.xMetric="";
  x.value=view.xMetric;x.hidden=!options.length;
  refreshComparison().catch(report);
}
async function refreshComparison(){
  const version=++comparisonTicket;
  comparison=null;
  if(!view.xMetric)return;
  const result=await api().compare_metrics(project.session,JSON.parse(view.xMetric),JSON.parse(view.metric));
  if(version!==comparisonTicket)return;
  comparison=result;drawPlot();
}
function selectedSummaries(){
  const rows=metricGroups.find(([key])=>key===view.metric)?.[1];
  if(!rows?.length)return [];
  return [...project.summaries.filter(s=>seriesKey(s)===view.metric),
    ...rows.filter(r=>r.kind==="Structure computed")];
}
async function showStructureValues(){
  const token=modelTicket, model=view.model, component=view.component;
  const records=await api().structure_values(project.session,component,model);
  if(token!==modelTicket)return;
  const target=coordinates;
  by("structureTarget").textContent=target.filename+" · "+target.origin+" · "+(target.chain?"Chain "+target.chain:"Unmapped");
  const representative=project.representatives?.[selectedComponent().candidate];
  const active=representative===model;
  by("representativeStatus").textContent=active?"This structure supplies candidate metrics.":
    representative?"A different structure supplies candidate metrics.":"Choose a representative to include its values in candidate comparisons.";
  by("setRepresentative").disabled=active;
  const table=node("table"), head=node("tr");
  for(const text of ["Metric","Value","Unit","Region","Conditions","Source","File"])head.append(node("th",text));
  table.append(head);
  for(const row of records){
    const tr=node("tr");
    for(const key of ["metric","value","unit","region","conditions","source","filename"])tr.append(node("td",row[key]));
    table.append(tr);
  }
  by("structureRows").replaceChildren(records.length?table:node("p","No values registered. Use Import with the structure selected."));
  if(!by("structureDialog").open)by("structureDialog").showModal();
}
function showMeasurementRecords(){
  const rows=metricGroups.find(([key])=>key===view.metric)?.[1]||[];
  const selected=selectedComponent()?.candidate;
  const box=by("recordRows");
  box.replaceChildren();
  const first=rows[0];
  if(first)box.append(node("p",[selected?owner(selected):"All candidates",first.metric,first.unit,first.conditions||"Conditions unknown",first.source].join(" · ")));
  function table(title,headers,data){
    if(!data.length)return;
    const t=node("table"), head=node("tr");
    for(const name of headers)head.append(node("th",name));
    t.append(head);
    for(const row of data){
      const tr=node("tr");
      for(const value of row)tr.append(node("td",value==null||value===""?"—":value));
      t.append(tr);
    }
    box.append(node("h3",title),t);
  }
  if(comparison){
    table("Candidate pairs",["Candidate","X","X basis","Y","Y basis"],comparison.pairs
      .map(p=>[p.label,p.x,p.x_basis,p.y,p.y_basis]));
    for(const [axis,key] of [["X",view.xMetric],["Y",view.metric]]){
      const source=metricGroups.find(([k])=>k===key)[1];
      table(axis+" · "+source[0].metric,["Candidate","Sample","Value","Unit","Record","Set","Conditions","Source","File"],
        source.filter(r=>!selected||r.candidate===selected).map(r=>[owner(r.candidate),r.sample,r.value,r.unit,r.statistic,r.replicate_set,r.conditions,r.source,r.filename]));
    }
    by("recordsDialog").showModal();
    return;
  }
  const matching=rows.filter(r=>!selected||r.candidate===selected);
  table("Means",["Candidate","Replicate set","Origin","Mean","SD","SEM","n"],selectedSummaries()
    .filter(r=>r.origin&&(!selected||r.candidate===selected)).map(r=>[owner(r.candidate),r.replicate_set,r.origin,r.value,r.sd,r.sem,r.n]));
  if(first?.kind==="Structure computed"){
    table("Representative structures",["Candidate","Component","Coordinate file","Chain","Region","Value","Source file"],
      matching.map(r=>[owner(r.candidate),r.coordinate_component,r.coordinate_file,r.chain,r.region,r.value,r.filename]));
  }else{
    table("Imported records",["Candidate","Replicate set","Record","Value","Sample","Event time","Source file"],matching
      .map(r=>[owner(r.candidate),r.replicate_set,r.statistic,r.value,r.sample,r.event_time,r.filename]));
  }
  if(!matching.length)box.append(node("p","No records for this candidate and metric."));
  by("recordsDialog").showModal();
}
function drawPlot(){
  const version=++plotTicket;
  renderedPlot=null;
  by("exportPlot").disabled=true;
  by("exportComparison").disabled=true;
  const item=selectedComponent(), selected=item?.candidate;
  const metric=metricGroups.find(([key])=>key===view.metric);
  let points=[],axis="",missing=0;
  const summaries=selectedSummaries();
  const hasMeans=summaries.some(r=>r.origin);
  const display=hasMeans ? (view.measureView||"SD") : "individual";
  by("measurementControls").hidden=!metric;
  by("measureView").hidden=Boolean(view.xMetric || metric?.[1][0].kind==="Structure computed");
  by("exportComparison").hidden=!comparison;
  by("measureView").value=display;
  by("measureView").disabled=!hasMeans;
  if(metric && view.xMetric){
    points=(comparison?.pairs||[]).filter(p=>p.included).map(p=>({key:p.candidate,name:p.label,x:p.x,y:p.y,label:p.x_basis+" / "+p.y_basis}));
    axis=metric[1][0].metric+" ("+metric[1][0].unit+")";
  }else if(metric){
    const rows=metric[1];
    if(display==="individual"){
      points=rows.filter(r=>r.statistic==="Individual"&&r.value!==null)
        .map(r=>({key:r.candidate,name:owner(r.candidate),y:r.value,label:r.sample||r.kind}));
    }else{
      points=summaries.filter(r=>r.value!==null).map(r=>{
        const err=display==="SD"?r.sd:r.sem;
        const label=[r.origin+" mean",r.replicate_set,"n="+(r.n??"unknown"),display+" "+(err??"unknown")].filter(Boolean).join(" · ");
        return {key:r.candidate,name:owner(r.candidate),y:r.value,error:err,label};
      });
    }
    missing=(project?.candidates||[]).filter(c=>!points.some(p=>p.key===c.id)).length;
    axis=rows[0].metric+" ("+rows[0].unit+")";
  }else{
    const kind=view.metric;
    points=(project?.components||[]).filter(c=>c.kind===kind).map(c=>({key:c.candidate,component:c.id,name:owner(c.candidate),y:c.size,label:c.label}));
    axis=kind==="DNA"?"Length (nt)":"Length (aa)";
  }
  const box=by("plot"), session=project?.session;
  const plotted=new Set(points.map(p=>p.key));
  const labels=(project?.candidates||[]).filter(c=>plotted.has(c.id)).map(c=>c.id);
  const trace={type:"scatter",mode:"markers",x:points.map(p=>p.key),y:points.map(p=>p.y),
    customdata:points.map(p=>[p.key,p.component||"",safeLabel(p.name),safeLabel(p.label)]),
    marker:{size:points.map(p=>(p.component?p.component===item?.id:p.key===selected)?12:8),
      color:points.map(p=>(p.component?p.component===item?.id:p.key===selected)?"#c96a19":"#26776f")},
    hovertemplate:"%{customdata[2]} · %{customdata[3]}<br>%{y}<extra></extra>"};
  if(metric && !view.xMetric && display!=="individual")trace.error_y={type:"data",array:points.map(p=>p.error),visible:true};
  const layout={margin:{l:52,r:12,t:12,b:45},xaxis:{type:"category",categoryorder:"array",categoryarray:labels,tickmode:"array",tickvals:labels,ticktext:labels.map(k=>safeLabel(owner(k))),automargin:true},
    yaxis:{title:{text:safeLabel(axis)},automargin:true},showlegend:false,dragmode:false,paper_bgcolor:"white",plot_bgcolor:"#f5f8f6"};
  const valueLabel=metric?.[1][0].kind==="Structure computed"?" structure values":display==="individual"?" observations":" means";
  by("plotInfo").textContent=metric?points.length+valueLabel+" · "+missing+" candidates without a plotted value":"";
  if(metric && view.xMetric){
    const [name,unit]=JSON.parse(view.xMetric);
    trace.x=points.map(p=>p.x);
    trace.hovertemplate="%{customdata[2]}<br>X %{x} · Y %{y}<br>%{customdata[3]}<extra></extra>";
    layout.xaxis={title:{text:safeLabel(name+" ("+unit+")")},automargin:true};
    by("plotInfo").textContent=comparison?"Pearson r "+(comparison.r==null?"undefined":comparison.r.toFixed(3))+
      " · "+comparison.n+" paired candidates · "+(comparison.pairs.length-comparison.n)+" excluded":"Comparing candidates…";
  }
  plotDraw=plotDraw.catch(report).then(async()=>{
    if(project?.session!==session || version!==plotTicket)return;
    await Plotly.react(box,points.length?[trace]:[],layout,{displayModeBar:false,responsive:true});
    if(version!==plotTicket)return;
    if(points.length){
      const description=[by("metric").selectedOptions[0].text];
      if(view.xMetric)description.push(by("xMetric").selectedOptions[0].text);
      else if(metric)description.push(by("measureView").selectedOptions[0].text);
      description.push(by("plotInfo").textContent);
      if(selected)description.push("Selected candidate · "+owner(selected));
      renderedPlot={trace,layout,session,version,description:description.filter(Boolean)};
      by("exportPlot").disabled=false;
    }
    by("exportComparison").disabled=!comparison;
    box.removeAllListeners("plotly_click");
    box.on("plotly_click",e=>{
      if(project?.session!==session || version!==plotTicket)return;
      const [candidate,component]=e.points[0].customdata;
      const id=component||(selectedComponent()?.candidate===candidate?view.component:project.components.find(c=>c.candidate===candidate)?.id);
      if(id) select(id).catch(report);
    });
  });
}
async function savePlot(){
  const snapshot=renderedPlot;
  if(!snapshot)return;
  const lines=snapshot.description.map(s=>safeLabel(s));
  const layout={...snapshot.layout,margin:{...snapshot.layout.margin,t:35+20*lines.length},
    title:{text:lines.join("<br>"),font:{size:14},x:0.04,xanchor:"left"}};
  const png=await Plotly.toImage({data:[snapshot.trace],layout},{format:"png",width:960,height:600,scale:2});
  if(snapshot.version!==plotTicket)throw new Error("The plot changed. Save the current view again.");
  if(await api().export_plot(snapshot.session,png))msg("Plot image saved.");
}
function resetPreview(){
  packet=null;by("preview").replaceChildren();by("confirm").hidden=true;by("importError").textContent="";
}
function featureSpans(feature){
  return feature.parts.map(([start,end,strand])=>{
    const direction=strand===1?" (+)":strand===-1?" (−)":
      feature.snapgene_direction==="both"?" (both directions)":
      feature.snapgene_direction==="unspecified"?" (direction unspecified)":"";
    return start+"–"+end+direction;
  });
}
function entryFields(){
  const fields=by("measurementFields");
  fields.replaceChildren();
  const selected=selectedComponent()?.candidate;
  for(const [key,title,choices] of [
    ["candidate","Candidate",project.candidates.map(c=>c.label)],["metric","Metric"],["value","Value"],
    ["unit","Unit"],["kind","Kind",["Measured","Reference measured"]],["sample","Sample"],["conditions","Conditions"],
    ["source","Source"],["event_time","Event time with UTC offset"],["replicate_set","Replicate set"],
    ["statistic","Record",["Individual","Mean"]],["error_type","Error definition",["","SD","SEM"]],["error","Error"],["n","Count (n)"]]){
    const label=node("label",title), control=node(choices?"select":"input");
    if(choices)for(const x of choices)control.append(opt(x||"Unknown",x));
    if(key==="candidate"&&selected)control.value=owner(selected);
    control.name=key;label.append(control);fields.append(label);
  }
}
async function chooseFile(){
  resetPreview();
  const result=await api().preview(project.session,by("inputKind").value,view.component,view.model);
  renderPreview(result);
}
async function reviewMeasurement(paste){
  resetPreview();
  const content=paste?by("measurementText").value:Object.fromEntries(
    [...by("measurementFields").querySelectorAll("[name]")].map(el=>[el.name,el.value]));
  const result=await api().preview_measurements(project.session,content);
  by("manualEntry").open=false;
  renderPreview(result);
}
function renderPreview(result){
  if(!result)return;
  packet=result;const box=by("preview");box.append(node("h3",result.filename));
  if(result.mode==="structure"){
    const chains=node("select");chains.id="assignChain";chains.append(opt("Unmapped coordinates",""),...result.chains.map(c=>opt("Confirm exact sequence · chain "+c,c)));
    const origin=node("select");origin.id="origin";for(const s of ["Unknown","Experimental","Predicted","Reference"])origin.append(opt(s,s));
    box.append(node("label","Sequence mapping "),chains,node("label"," Origin "),origin);
  }else{
    const table=node("table"),head=node("tr");
    const seq=result.mode==="sequence";
    const obsKeys=result.mode==="structure_metrics"?["metric","value","unit","region","conditions","source"]:
      ["candidate","metric","value","unit","kind","sample","conditions","source","event_time"];
    if(result.target)box.append(node("p",owner(selectedComponent().candidate)+" / "+selectedComponent().label+
      " · "+result.target.filename+" · "+result.target.origin+" · "+(result.target.chain?"Chain "+result.target.chain:"Unmapped")));
    if(!seq&&result.records.some(r=>"statistic" in r))obsKeys.push("replicate_set","statistic","error_type","error","n");
    for(const label of seq?["Candidate key","Component label","Type","Length","Sequence / annotations"]:obsKeys.map(k=>k[0].toUpperCase()+k.slice(1).replaceAll("_"," ")))head.append(node("th",label));
    table.append(head);
    for(const r of result.records){
      const tr=node("tr");
      if(seq){
        for(const k of ["candidate","component"]){const td=node("td"),input=node("input");input.value=r[k];input.dataset.field=k;input.setAttribute("aria-label",k);td.append(input);tr.append(td);}
        tr.append(node("td",r.kind),node("td",r.size));const td=node("td"),details=node("details");
        details.append(node("summary","Sequence · "+r.features+" features"),node("pre",r.sequence));
        for(const f of r.annotations){
          const spans=featureSpans(f);
          details.append(node("p",f.type+" · "+f.label+" · "+(spans.join(", ")||"coordinates unavailable")));
          if(f.type==="CDS")details.append(node("p",f.issue||(f.translation?
            "Translation · "+f.translation.length+" aa · "+f.translation:"Codon correspondence unavailable.")));
        }
        td.append(details);tr.append(td);
      }else for(const k of obsKeys)tr.append(node("td",r[k]??"Missing"));
      table.append(tr);
    }
    box.append(table);
  }
  by("confirm").hidden=false;
}
action("newProject",()=>openProject("new"));action("openProject",()=>openProject("open"));action("example",()=>openProject("example"));
action("filter",drawTree,"input");action("metric",()=>{view.metric=by("metric").value;prepareAxes();drawTree();drawPlot();return save();},"change");
action("xMetric",()=>{view.xMetric=by("xMetric").value;const result=refreshComparison();drawPlot();return Promise.all([result,save()]);},"change");
action("exportComparison",async()=>{if(comparison && await api().export_comparison(project.session,comparison.token))msg("Comparison workbook exported.");});
action("exportPlot",savePlot);
action("measureView",()=>{view.measureView=by("measureView").value;drawPlot();return save();},"change");
action("measurementDetails",showMeasurementRecords);
action("pos",()=>at(Number(by("pos").value)),"change");action("prev",()=>at(Math.max(1,view.position-sequenceWindow().width)));action("next",()=>at(Math.min(detail.seq.length,view.position+sequenceWindow().width)));
action("wholeRecord",()=>setWindow(detail.seq.length));
action("sequenceZoom",()=>setWindow(Math.round(detail.seq.length**(1-Number(by("sequenceZoom").value)/1000))),"input");
action("reference",async()=>{view.reference=by("reference").value;view.alignRecords=false;view.alignmentWindow=null;await Promise.all([readReference(),save()]);},"change");
action("model",async()=>{view.model=by("model").value;await Promise.all([readModel(),save()]);},"change");
action("movingModel",async()=>{
  view.overlays??={};
  view.overlays[view.model]={target:by("movingModel").value,shown:true};
  by("fitFirst").value=by("fitLast").value="";
  await Promise.all([readOverlay(),save()]);
},"change");
by("overlayRange").addEventListener("submit",event=>{
  event.preventDefault();
  const low=by("fitFirst").value,high=by("fitLast").value;
  if(Boolean(low)!==Boolean(high)){
    by("fitSummary").textContent="Enter both endpoints, or clear both to fit all paired positions.";
    return;
  }
  view.overlays[view.model].bounds=low?[Number(low),Number(high)]:null;
  Promise.all([readOverlay(),save()]).catch(report);
});
action("toggleOverlay",()=>{
  const state=view.overlays[view.model];
  state.shown=!state.shown;mountOverlay();return save();
});
action("structureLayout",()=>{
  view.overlays[view.model].layout=by("structureLayout").value;
  mountOverlay();return save();
},"change");
action("focusResidue",()=>{
  const selection=atomSelection(coordinates,view.position);
  if(selection){viewer.zoomTo({...selection,model:fixedModel});viewer.render();}
});
action("structureMetrics",showStructureValues);
action("exportStructure",saveStructureImage);
action("setRepresentative",async()=>{
  const session=project.session;
  const change=await api().select_representative(session,view.component,view.model);
  if(project.session!==session)return;
  project=change;
  prepareMetric();drawTree();drawPlot();
  await showStructureValues();
});
action("style",()=>{view.style=by("style").value;highlight();return save();},"change");action("fit",()=>{viewer.zoomTo();viewer.render();});
action("note",()=>{by("noteText").value=view.note;by("noteDialog").showModal();});
action("bookmarks",async()=>{
  bookmarkList(await api().bookmarks(project.session));
  by("bookmarkName").value=by("bookmarkStatus").textContent="";
  by("bookmarkDialog").showModal();
});
action("addBookmark",async()=>{
  try{
    const state=structuredClone(view);
    if(viewer && coordinates)state.cameras[view.model]=viewer.getView().slice();
    bookmarkList(await api().add_bookmark(project.session,by("bookmarkName").value,state));
    by("bookmarkStatus").textContent="Observation saved.";
  }catch(error){by("bookmarkStatus").textContent=error.message||String(error);}
});
action("openBookmark",async()=>{
  await pendingSave;
  const state=await api().open_bookmark(project.session,by("bookmarkList").value);
  by("bookmarkDialog").close();
  await setProject(state);
});
action("saveNote",async()=>{view.note=by("noteText").value;await save();by("noteDialog").close();msg("Project note saved.");});
action("import",()=>{resetPreview();entryFields();by("manualEntry").open=false;by("measurementText").value="";by("importDialog").showModal();});
action("reviewEntry",()=>reviewMeasurement(false));action("reviewPaste",()=>reviewMeasurement(true));
action("manualEntry",resetPreview,"input");
action("chooseFile",chooseFile);
action("confirm",async()=>{
  if(!packet)return;
  const options={};
  if(packet.mode==="sequence")options.bindings=[...by("preview").querySelectorAll("tr")].slice(1).map(tr=>Object.fromEntries([...tr.querySelectorAll("input")].map(el=>[el.dataset.field,el.value])));
  if(packet.mode==="structure"){options.chain=by("assignChain").value||null;options.origin=by("origin").value;}
  await pendingSave;
  const data=await api().accept(project.session,packet.token,options);
  by("importDialog").close();packet=null;await setProject(data);msg("Reviewed records saved.");
});
action("export",async()=>{if(detail && await api().export_fasta(project.session,[detail.id]))msg("Selected component exported as FASTA.");});
new ResizeObserver(()=>{if(viewer)viewer.resize();}).observe(by("molecule"));
new ResizeObserver(()=>{if(parallelViewer&&!by("overlayMolecule").hidden)parallelViewer.resize();}).observe(by("overlayMolecule"));
window.addEventListener("pywebviewready",()=>api().current().then(setProject).catch(report));
