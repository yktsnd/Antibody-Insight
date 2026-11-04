"use strict";

// F21/F22: explicit local source import and inspection, no model execution.
const PredictionUI = (() => {
  let cfg, draft=null, epoch=0, targets=[];
  const q=(s)=>document.querySelector(s);
  const formats={prediction_json:'computed-evidence/1',af3_summary:'alphafold3-summary/1'};
  const active=()=>Object.hasOwn(formats,q('#import-format').value);
  function reset(){draft=null;}
  function fillModels(){
    const structure=targets.find((s)=>s.id===q('#prediction-structure').value);
    q('#prediction-model').innerHTML='<option value="">Choose the actual coordinate-model ID</option>'+(structure?.models||[]).map((m)=>`<option value="${m}">${m}</option>`).join('');
    q('#prediction-coordinate-source').textContent=structure?`${structure.name} / ${structure.id} / SHA-256 ${structure.sha256}${structure.unknown_model_present?' / source also contains an unspecified model':''}`:'No coordinate source selected.';
  }
  async function update(){
    const format=q('#import-format').value,project=q('#import-target').value,ticket=++epoch;
    q('#prediction-import-options').hidden=!active();
    q('#prediction-native-options').hidden=format!=='af3_summary';
    if(format!=='af3_summary')return;
    targets=[];q('#prediction-structure').innerHTML='<option value="">Choose an existing computed Structure</option>';fillModels();
    if(!project)return;
    try{
      const result=await cfg.api('/api/prediction-targets',{project_id:project});
      if(ticket!==epoch||!q('#import-dialog').open||q('#import-target').value!==project||q('#import-format').value!==format)return;
      targets=result.structures;
      q('#prediction-structure').innerHTML='<option value="">Choose an existing computed Structure</option>'+targets.map((s)=>`<option value="${s.id}" ${s.origin_kind==='computed'&&s.models.length?'':'disabled'}>${cfg.esc(s.name)} / ${s.id} / ${cfg.esc(s.origin_kind)} / models ${cfg.esc(s.models.join(', ')||'unavailable')}</option>`).join('');
    }catch(error){if(ticket===epoch&&q('#import-dialog').open)cfg.notify(error.message,true);}
  }
  async function preview(request,owns){
    if(!request.project_id)throw Error('Computed JSON requires an existing project with explicitly registered subjects.');
    const fileFormat=formats[request.format],ticket=epoch;
    const mapped=draft?.project===request.project_id&&draft.text===request.text&&draft.format===fileFormat;
    let options={};
    if(request.format==='af3_summary')options={structure_id:q('#prediction-structure').value,
      model:q('#prediction-model').value?Number(q('#prediction-model').value):null,
      source:{name:q('#prediction-source').value,version:q('#prediction-version').value||null},
      timestamp:q('#prediction-time').value,conditions:q('#prediction-conditions').value.trim()?q('#prediction-conditions').value:null};
    const result=await cfg.api('/api/prediction-preview',{project_id:request.project_id,text:request.text,filename:request.filename,file_format:fileFormat,
      bindings:mapped?Object.fromEntries(draft.choices):{},bindings_text_sha256:mapped?draft.sha:null,options});
    if(!owns()||ticket!==epoch)return null;
    const original=await cfg.api('/api/bundle?project_id='+encodeURIComponent(request.project_id));
    if(!owns()||ticket!==epoch)return null;
    draft={project:request.project_id,text:request.text,format:fileFormat,sha:result.report.text_utf8_sha256,
      refs:result.report.unresolved_refs,choices:new Map(Object.entries(result.report.bindings)),records:original.entities};
    return result;
  }
  function mappingPanel(report){
    if(report.kind!=='computed_json'||!draft)return '';
    const e=cfg.esc,byId=new Map(draft.records.map((r)=>[r.id,r]));
    function path(record){
      const labels=[];
      while(record){labels.push(`${record.type}: ${record.external_id||record.name||''}${record.type==='material'?' / lot '+record.lot:''} / ${record.id}`);
        record=byId.get(record.type==='material'?record.construct_id:['construct','structure'].includes(record.type)?record.molecule_id:null);}
      return labels.join(' → ');
    }
    return `<section id="prediction-mapping"><h3>Computed source review</h3><p>${report.valid_rows} extracted computed values · ${report.source_files_added} original JSON source file</p><p class="mono">${e(report.file_name)} / SHA-256 ${e(report.text_utf8_sha256)}</p><p class="muted">Original JSON is retained in full. Associations are recorded assertions, not authenticated model runs. Unmapped arrays and metadata are not interpreted as scalar or residue results.</p><details><summary>Retained but unmapped JSON paths (${report.retained_unmapped_paths.length})</summary><pre>${cfg.pretty(report.retained_unmapped_paths)}</pre></details>${draft.refs.length?'<h3>Actual computed subject mapping</h3><p>Choose the actual subject type and ID. Equal names or sequences do not establish identity. Quoted tokens show original whitespace and escapes.</p>':''}${draft.refs.map((ref,i)=>`<label class="field">Original token: ${e(JSON.stringify(ref))}<select data-prediction-map="${i}"><option value="">Unresolved — exclude these records</option>${draft.records.filter((r)=>['molecule','construct','material','structure'].includes(r.type)).map((r)=>`<option value="${r.id}" ${draft.choices.get(ref)===r.id?'selected':''}>${e(path(r))}</option>`).join('')}</select></label>`).join('')}${draft.refs.length?'<button id="apply-prediction-mappings" class="secondary">Apply mappings &amp; preview again</button>':''}<details><summary>Full computed import QC and provenance</summary><pre>${cfg.pretty(report)}</pre></details></section>`;
  }
  function change(el){
    if(el.id==='prediction-structure'){fillModels();return true;}
    if(!el.hasAttribute('data-prediction-map'))return false;
    if(!draft)return true;
    const ref=draft.refs[Number(el.dataset.predictionMap)];
    if(el.value)draft.choices.set(ref,el.value);else draft.choices.delete(ref);
    cfg.invalidate();return true;
  }
  function origin(evidence){
    if(!evidence.prediction_origin)return '';
    const origin=evidence.prediction_origin,file=cfg.find(origin.file_id);
    if(!file)return '<p class="error">Original computed source unavailable.</p>';
    const e=cfg.esc,structure=file.options.structure_id?cfg.find(file.options.structure_id):null;
    return `<details class="prediction-source"><summary>Original computed JSON source / ${e(file.name)} / ${e(origin.json_pointer)}</summary><p class="mono">${file.id}<br>SHA-256 ${e(file.sha256)}<br>Format: ${e(file.file_format)}</p><p>Imported by ${e(file.source.name)} / ${e(file.source.version||'version unknown')} at ${e(file.created_at)}. Computation source and event time are recorded separately on the evidence.</p>${structure?`<p>Declared coordinate association: ${e(structure.name)} / ${structure.id}<br>Coordinate SHA-256 ${e(structure.sha256)} / actual coordinate-model ID ${file.options.model}</p><p class="muted">Coordinate-model ID is distinct from an external seed, sample or run ID. This association is a recorded user assertion.</p>`:''}<p class="muted">The complete submitted UTF-8 JSON below includes uninterpreted fields and arrays. It is retained source content, not a new analysis or authenticated external run.</p><details data-prediction-metadata="${file.id}"><summary>Bindings, import options and allocations</summary><pre></pre></details><details data-prediction-content="${file.id}"><summary>Complete original submitted JSON</summary><pre></pre></details><button class="secondary" data-prediction-download="${file.id}">Download original submitted JSON</button></details>`;
  }
  function download(id){
    const file=cfg.find(id);if(!file||file.type!=='prediction_file')return;
    const url=URL.createObjectURL(new Blob([file.content],{type:'application/json;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=file.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  document.addEventListener('toggle',(event)=>{
    const details=event.target;if(!details.matches?.('[data-prediction-content],[data-prediction-metadata]')||!cfg)return;
    if(!details.open){details.querySelector('pre').textContent='';return;}
    const file=cfg.find(details.dataset.predictionContent||details.dataset.predictionMetadata);
    const text=file?(details.hasAttribute('data-prediction-content')?file.content:JSON.stringify({bindings:file.bindings,options:file.options,allocations:file.allocations},null,2)):'Source unavailable';
    details.querySelector('pre').textContent=text;
  },true);
  const guide={
    en:'<h3>Computed JSON sources and reproducibility</h3><p>In E, explicitly choose Computed evidence JSON or AlphaFold 3 summary JSON. Canonical computed-evidence/1 records declare the direct subject, original unit, source/version, event time and conditions. Map external tokens to actual subjects after preview. For a native summary, select an existing computed Structure and its actual coordinate-model ID, then enter the computation source, original event time and optional parameter JSON. No model ID, version or time is inferred. Only documented ptm, iptm, fraction_disordered and ranking_score scalars are extracted; other content remains in the original source with an unmapped-path list. These are model-internal outputs, not measured affinity or an application recommendation. In R, open Original computed JSON source to inspect the exact source text, hash and value pointer. Full workspace export retains all registered source files, kinds, IDs, correspondence, hypotheses and immutable decisions. Reimport reconstructs the recorded dataset; it does not rerun the external computation. Older FASTA/CSV imports retain their recorded provenance and derived records, not original raw files.</p>',
    ja:'<h3>予測結果JSONの出典と再利用</h3><p>Eで「Computed evidence JSON」または「AlphaFold 3 summary JSON」を明示的に選択します。computed-evidence/1形式では、結果が直接属する対象、元の単位、計算元とバージョン、計算日時、条件を指定します。外部の識別子は、プレビュー後に実際の対象へ対応付けます。AlphaFold 3のサマリーでは、登録済みの予測構造と座標ファイル内の実際のモデルIDを選び、計算元、元の計算日時、必要に応じて条件のJSONを入力します。モデルID・バージョン・日時を推測して補いません。ptm、iptm、fraction_disordered、ranking_scoreの対応するスカラー値のみを取り込み、それ以外は未解釈の項目として一覧に示し、元JSONに保持します。これらはモデル内部の指標であり、結合親和性の実測値や本ソフトウェアによる推奨ではありません。Rの「Original computed JSON source」で元のテキスト、ハッシュ値、値の位置を確認できます。プロジェクト全体の出力には、登録された元ファイル、根拠の種類、ID、対応関係、仮説、変更できない判断記録が含まれます。再取り込みは記録されたデータの復元であり、外部の計算を再実行するものではありません。従来のFASTA・CSV取込では、記録済みの来歴と変換後のレコードを保持しており、元ファイル自体を保持したとは扱いません。</p>'
  };
  return {configure(value){cfg=value;},reset,update,preview,mappingPanel,change,origin,download,guide};
})();
