"use strict";

let regionSession, regionDrafts, comparisons, regionPages;
const REGION_PAGE=24;

function updateRegions(){
  if(regionSession!==project?.session){
    regionSession=project?.session;
    regionDrafts=new Map();comparisons=new Map();regionPages=new Map();
  }
  const panel=by("regionsPanel"), opened=Boolean(detail&&view.regionsOpen);
  by("regionsToggle").hidden=!detail;
  by("regionsToggle").setAttribute("aria-expanded",String(opened));
  panel.hidden=!opened;
  if(!opened)return;
  const component=detail.id, kind=detail.kind;
  view.regions??={AA:[],DNA:[]};
  const choices=view.regions[kind];
  const draft=regionDrafts.get(component)||{source:"",start:"1",end:String(detail.seq.length)};
  regionDrafts.set(component,draft);
  panel.replaceChildren();
  const form=node("form"), source=node("select"), first=node("input"), last=node("input");
  form.className="strip";
  source.id="regionSource";source.setAttribute("aria-label","Region source");
  source.append(opt("Enter sequence range",""),...detail.features.flatMap((feature,index)=>{
    if(!feature.parts.length || feature.open_peptide_end || feature.parts.some(p=>!p[2]))return [];
    return [opt(feature.label+" · "+feature.type,index)];
  }));
  source.value=draft.source;
  const limits=node("label","Positions ");
  for(const [control,id,property,label] of [[first,"regionFirst","start","First position"],[last,"regionLast","end","Last position"]]){
    control.type="number";control.min=1;control.max=detail.seq.length;control.required=true;
    control.id=id;control.value=draft[property];control.setAttribute("aria-label",label);
    control.oninput=()=>{draft[property]=control.value;};
  }
  limits.append(first,"–",last);
  function displaySource(){
    limits.hidden=source.value!=="";
    first.disabled=last.disabled=limits.hidden;
  }
  source.onchange=()=>{draft.source=source.value;displaySource();};
  displaySource();
  const add=node("button","Add region");
  form.append(source,limits,add);
  form.onsubmit=event=>{
    event.preventDefault();
    const choice=source.value===""?{component,start:Number(first.value),end:Number(last.value)}:
      {component,feature:Number(source.value),label:source.selectedOptions[0].text};
    if(choice.feature===undefined && choice.start>choice.end){msg("Start must be before or equal to end.");return;}
    if(!choices.some(c=>JSON.stringify(c)===JSON.stringify(choice)))choices.push(choice);
    updateRegions();save().catch(report);
  };
  panel.append(form);
  drawRegionComparison(panel,choices,kind);
}

function drawRegionComparison(panel,choices,kind){
  const list=node("div");
  list.className="numbered-cohort";
  choices.forEach((choice,index)=>{
    const label=choice.label||choice.start+"–"+choice.end;
    const remove=node("button",(index===0?"Reference · ":"")+componentLabel(choice.component)+" · "+label+" ×");
    remove.title="Remove this region";
    remove.onclick=()=>{choices.splice(index,1);updateRegions();save().catch(report);};
    list.append(remove);
  });
  if(choices.length<2){panel.append(list);return;}
  const key=JSON.stringify(choices);
  let status=comparisons.get(kind);
  if(status?.key!==key){
    status={key};comparisons.set(kind,status);
    const pending=status, cache=comparisons;
    api().compare_regions(project.session,structuredClone(choices)).then(
      result=>{pending.result=result;},error=>{pending.error=error.message||String(error);}
    ).finally(()=>{if(comparisons===cache && cache.get(kind)===pending)updateRegions();});
  }
  if(!status.result){
    panel.append(list,node("small",status.error||"Aligning selected regions…"));
    if(status.error){
      const retry=node("button","Retry");
      retry.onclick=()=>{comparisons.delete(kind);updateRegions();};
      panel.append(retry);
    }
    return;
  }
  const {rows,columns,identity,method,insertions,consensus,token}=status.result;
  const selectedRow=rows.findIndex(row=>row.component===detail.id && row.offsets.includes(view.position));
  const column=selectedRow<0?-1:columns.findIndex(col=>{
    const position=col[selectedRow];
    return position!=null&&rows[selectedRow].offsets[position-1]===view.position;
  });
  const start=Math.min(regionPages.get(kind)??(Math.floor(Math.max(0,column)/REGION_PAGE)*REGION_PAGE),
                       Math.floor((columns.length-1)/REGION_PAGE)*REGION_PAGE);
  const shown=columns.slice(start,start+REGION_PAGE);
  const table=node("table"), headings=node("tr"), scroller=node("div"), nav=node("div");
  nav.className="strip";
  const previous=node("button","←"), next=node("button","→");
  previous.setAttribute("aria-label","Previous alignment columns");
  next.setAttribute("aria-label","Next alignment columns");
  previous.disabled=start===0;next.disabled=start+shown.length===columns.length;
  previous.onclick=()=>{regionPages.set(kind,start-REGION_PAGE);updateRegions();};
  next.onclick=()=>{regionPages.set(kind,start+REGION_PAGE);updateRegions();};
  nav.append(previous,node("small",(start+1)+"–"+(start+shown.length)+" of "+columns.length+" columns"),next);
  const download=node("button","Export comparison…");
  download.onclick=async()=>{
    try{if(await api().export_regions(project.session,token))msg("Region comparison exported.");}
    catch(error){report(error);}
  };
  nav.append(download);
  panel.append(nav);
  table.id="regionComparison";scroller.className="numbered-scroll";
  headings.append(node("th","Region"),...shown.map((col,i)=>{
    const ref=col[0];
    const label=node("th",ref===null?"ins":rows[0].offsets[ref-1]);
    if(insertions[start+i])label.title="Unanchored insertion";
    return label;
  }));
  table.append(headings);
  rows.forEach((row,index)=>{
    const tr=node("tr"), name=node("th",componentLabel(row.component));
    name.title=componentLabel(row.component)+" · "+row.label;
    const stat=identity[0][index];
    const result=index===0?"Reference":stat?stat.join("/"):"Ambiguous";
    name.append(node("small",result+" · "+row.label));
    tr.append(name);
    for(const col of shown){
      const cell=node("td"), coord=col[index];
      if(coord==null){cell.textContent="—";tr.append(cell);continue;}
      const position=row.offsets[coord-1], aa=row.letters[coord-1];
      const button=node("button",aa);button.className="base";
      button.dataset.regionRow=index;button.dataset.sourcePosition=position;
      button.title=row.kind==="DNA"?"Source base "+position+" · "+(row.parts[0][2]===-1?"reverse strand":"forward strand"):
        "Source residue "+position;
      if(col[0] && aa!==rows[0].letters[col[0]-1])button.classList.add("diff");
      button.setAttribute("aria-pressed",String(row.component===detail.id&&position===view.position));
      button.onclick=()=>{if(row.component===detail.id)at(position);else select(row.component,false,position).catch(report);};
      cell.append(button);tr.append(cell);
    }
    table.append(tr);
  });
  const consensusRow=node("tr");
  consensusRow.append(node("th","Consensus"),...consensus.slice(start,start+shown.length).map(c=>node("td",c??"·")));
  consensusRow.title="Strict majority among observed letters in unambiguous, reference-anchored rows";
  table.append(consensusRow);
  scroller.append(table);panel.append(scroller);
  const summaries=node("details");
  summaries.append(node("summary","Identity matrix and method"),node("p",method),
                   node("p","Cross-region identity counts equal known letters over paired known letters on the reference. Tied alignments and unanchored insertions are excluded."));
  const matrix=node("table");
  matrix.id="regionIdentity";
  const header=node("tr");
  header.append(node("th","Region"),...rows.map((_,i)=>node("th",i+1)));
  matrix.append(header);
  rows.forEach((r,i)=>{
    const tr=node("tr");
    const label=node("th",(i+1)+" · "+componentLabel(r.component));
    label.title=r.label;
    tr.append(label,...identity[i].map(pair=>{
      if(!pair || !pair[1])return node("td","—");
      const fraction=pair[0]/pair[1], cell=node("td",pair.join("/")+" · "+(100*fraction).toFixed(1)+"%");
      cell.style.background="rgba(8,117,104,"+(fraction*.25)+")";
      return cell;
    }));
    matrix.append(tr);
  });
  summaries.append(matrix);
  const facts=node("ul");
  rows.forEach((r,i)=>facts.append(node("li",(i+1)+" · "+r.letters.length+(kind==="DNA"?" nt":" aa")+
    (r.gc?" · GC "+r.gc[0]+"/"+r.gc[1]+" known bases":"")+
    " · "+r.parts.map(([a,b,strand])=>a+"–"+b+(strand===-1?" (−)":"")).join(", "))));
  summaries.append(facts,list);
  panel.append(summaries);
}

action("regionsToggle",()=>{
  view.regionsOpen=!view.regionsOpen;
  if(view.regionsOpen)view.numberingOpen=false;
  drawSequence();return save();
});
