"use strict";

let numberingSession, numberedCache = new Map(), cohortKey = "", cohortColumns;
let cohortWarning = "", cohortGeneration = 0;

function numberingCaption(domain) {
  return domain.chain+" · "+domain.start+"–"+domain.end+
    (domain.complete?"":" · partial or atypical");
}

function componentLabel(id) {
  const component=project.components.find(c=>c.id===id);
  return component ? owner(component.candidate)+" / "+component.label : "Unavailable component";
}

function loadNumbering(id,scheme) {
  const key=scheme+"|"+id;
  if(numberedCache.has(key))return;
  const cache=numberedCache, session=project.session;
  cache.set(key,{loading:true});
  api().numbered_domains(session,id,scheme).then(
    value=>cache.set(key,value), error=>cache.set(key,{error:error.message||String(error)})
  ).finally(()=>{if(numberedCache===cache)updateNumbering();});
}

function updateNumbering() {
  if(numberingSession!==project?.session) {
    numberingSession=project?.session;
    numberedCache=new Map();
    cohortKey="";cohortColumns=null;cohortWarning="";cohortGeneration++;
  }
  const panel=by("numberingPanel"), available=detail?.kind==="AA", opened=Boolean(available && view.numberingOpen);
  by("numberingToggle").hidden=!available;
  by("numberingToggle").setAttribute("aria-expanded",String(opened));
  panel.hidden=!opened;
  by("numberedPosition").textContent="";
  if(!opened)return;
  const current=detail.id, scheme=view.numberingScheme||"imgt";
  const schemeLabel=scheme==="imgt"?"IMGT":"Kabat";
  const cohort=scheme==="imgt"?"numberingCohort":"kabatCohort";
  loadNumbering(current,scheme);
  const numbered=numberedCache.get(scheme+"|"+current);
  const active=numbered.domains?.flatMap(d=>d.residues).find(r=>r.position===view.position);
  if(active)by("numberedPosition").textContent=schemeLabel+" "+active.label+" · "+active.region+" · sequence "+active.position;
  panel.replaceChildren();
  const controls=node("div");
  controls.className="strip";
  const switcher=node("select");
  switcher.setAttribute("aria-label","Numbering scheme");
  switcher.append(opt("IMGT","imgt"),opt("Kabat","kabat"));
  switcher.value=scheme;
  switcher.onchange=()=>{view.numberingScheme=switcher.value;updateNumbering();save().catch(report);};
  controls.append(switcher);
  if(numbered.loading){panel.append(controls,node("small","Numbering variable domains…"));return;}
  if(numbered.error){panel.append(controls,node("small",numbered.error));return;}
  const domains=node("select");
  domains.setAttribute("aria-label","Current variable domain");
  domains.id="domainChoice";
  const currentDomain=numbered.domains.findIndex(d=>view.position>=d.start && view.position<=d.end);
  numbered.domains.forEach((domain,i)=>domains.append(opt("Domain "+(i+1)+" · "+numberingCaption(domain),i)));
  if(currentDomain>=0)domains.value=currentDomain;
  if(!numbered.domains.length){
    controls.append(node("small","No antibody variable domain assigned."));
  }else{
    const region=node("select");
    region.setAttribute("aria-label","Numbered region");
    region.append(...["FR1","CDR1","FR2","CDR2","FR3","CDR3","FR4"].map(r=>opt(r,r)));
    region.value=view.numberingRegion||"CDR1";
    const jump=node("button","Go to region");
    jump.onclick=()=>{
      const residue=numbered.domains[Number(domains.value)].residues.find(r=>r.region===region.value);
      if(residue)at(residue.position);
      else msg("This region is unavailable in the selected domain.");
    };
    const add=node("button","Add to comparison");
    function updateButtons(){
      const index=Number(domains.value);
      add.disabled=!numbered.domains[index].complete ||
        (view[cohort]||[]).some(c=>c.component===current && c.domain===index);
    }
    domains.onchange=updateButtons;
    updateButtons();
    add.onclick=()=>{
      view[cohort]??=[];
      view[cohort].push({component:current,domain:Number(domains.value)});
      updateNumbering();save().catch(report);
    };
    region.onchange=()=>{
      view.numberingRegion=region.value;
      updateNumbering();save().catch(report);
    };
    controls.append(domains,region,jump,add);
  }
  panel.append(controls,node("small",numbered.method));
  drawNumberedComparison(panel,view[cohort]||[],scheme,schemeLabel);
}

function drawNumberedComparison(panel,choices,scheme,schemeLabel) {
  const list=node("div");
  list.className="numbered-cohort";
  choices.forEach(({component,domain},i)=>{
    const button=node("button","Remove "+componentLabel(component)+" · domain "+(domain+1));
    button.onclick=()=>{
      choices.splice(i,1);updateNumbering();save().catch(report);
    };
    list.append(button);
  });
  if(choices.length<2){panel.append(list);return;}
  const key=scheme+"|"+JSON.stringify(choices);
  if(cohortKey!==key){
    cohortKey=key;cohortColumns=null;cohortWarning="";
    const request=++cohortGeneration;
    api().compare_domains(project.session,choices,scheme).then(
      columns=>{if(request===cohortGeneration)cohortColumns=columns;},
      error=>{if(request===cohortGeneration)cohortWarning=error.message||String(error);}
    ).finally(()=>{if(request===cohortGeneration)updateNumbering();});
  }
  if(!cohortColumns){
    panel.append(node("small",cohortWarning||"Comparing selected domains…"));
    panel.append(list);
    return;
  }
  const region=view.numberingRegion||"CDR1", cols=cohortColumns.filter(c=>c.region===region);
  const table=node("table"), headings=node("tr"), scroller=node("div");
  table.id="numberedComparison";
  scroller.className="numbered-scroll";
  headings.append(node("th",region+" · "+schemeLabel),...cols.map(c=>node("th",c.label)));
  table.append(headings);
  choices.forEach(({component,domain},i)=>{
    const row=node("tr");
    const name=node("th",componentLabel(component)+" · "+(domain+1));
    if(i){
      const known=r=>r&&"ACDEFGHIKLMNOPQRSTUVWY".includes(r.aa);
      const paired=cols.filter(c=>known(c.residues[0])&&known(c.residues[i]));
      const equal=paired.filter(c=>c.residues[0].aa===c.residues[i].aa).length;
      const identity=node("small",equal+"/"+paired.length);
      identity.title=paired.length?"Equal known residues over paired known residues":"No paired known residues in this region";
      identity.className="regional-identity";
      name.append(" ",identity);
    }
    row.append(name);
    for(const column of cols){
      const cell=node("td"), r=column.residues[i];
      if(!r){cell.textContent="—";row.append(cell);continue;}
      const button=node("button",r.aa);
      button.className="base";
      button.dataset.imgt=r.label;
      button.dataset.component=component;
      button.title=schemeLabel+" "+r.label+" · sequence "+r.position;
      button.setAttribute("aria-pressed",String(component===detail.id && r.position===view.position));
      button.onclick=()=>{if(component===detail.id)at(r.position);else select(component,false,r.position).catch(report);};
      cell.append(button);row.append(cell);
    }
    table.append(row);
  });
  const frequency=node("tr");
  frequency.append(node("th","Residue frequency"));
  for(const column of cols){
    const counts=new Map();
    let covered=0;
    for(const residue of column.residues){
      if(residue){counts.set(residue.aa,(counts.get(residue.aa)||0)+1);covered++;}
    }
    const cell=node("td"), stack=node("div");
    stack.className="frequency-logo";
    stack.title=[...counts].map(([aa,count])=>aa+" "+count+"/"+covered).join(" · ")+" · "+covered+"/"+choices.length+" occupied";
    stack.setAttribute("aria-label",stack.title);
    for(const [aa,count] of [...counts].sort((a,b)=>a[1]-b[1]||a[0].localeCompare(b[0]))) {
      const segment=node("span",aa);
      segment.style.height=(100*count/covered)+"%";
      stack.append(segment);
    }
    cell.append(stack,node("small",covered+"/"+choices.length));
    frequency.append(cell);
  }
  table.append(frequency);
  scroller.append(table);panel.append(scroller);
  const edit=node("details");
  edit.append(node("summary","Comparison domains"),list);
  panel.append(edit);
}

action("numberingToggle",()=>{
  view.numberingOpen=!view.numberingOpen;
  if(view.numberingOpen)view.regionsOpen=false;
  drawSequence();return save();
});
