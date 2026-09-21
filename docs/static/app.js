'use strict';

const $ = id => document.getElementById(id);
const specs = [
  {group:'Demand & resources',id:'arrival_rate',label:'Arrivals / hour',value:18,min:.1,max:60,step:.1,help:'New orders released to picking'},
  {group:'Demand & resources',id:'max_workers',label:'Maximum workers',value:4,min:2,max:6,step:1,help:'Enumerate every valid allocation'},
  {group:'Service model',id:'pick_minutes',label:'Mean picking / min',value:6,min:.1,max:60,step:.1,help:'Active time per order'},
  {group:'Service model',id:'pack_minutes',label:'Mean packing / min',value:7,min:.1,max:60,step:.1,help:'Active time per order'},
  {group:'Service model',id:'service_cv',label:'Service CV',value:.5,min:0,max:2,step:.1,help:'Standard deviation ÷ mean'},
  {group:'Shift & queues',id:'shift_hours',label:'Shift length / hours',value:8,min:2,max:12,step:.5,help:'One bounded shift'},
  {group:'Shift & queues',id:'break_minutes',label:'Midpoint break / min',value:0,min:0,max:60,step:1,help:'Pauses all active service'},
  {group:'Shift & queues',id:'initial_pick',label:'Initial picking queue',value:0,min:0,max:100,step:1,help:'Orders waiting at open'},
  {group:'Shift & queues',id:'initial_pack',label:'Initial packing queue',value:0,min:0,max:100,step:1,help:'Orders ready to pack at open'},
  {group:'Decision screens',id:'sla_minutes',label:'Order SLA / min',value:60,min:1,max:240,step:1,help:'Deadline for due cohorts'},
  {group:'Decision screens',id:'target_fraction',label:'SLA target',value:.9,min:.5,max:1,step:.01,help:'Lower confidence bound must pass'},
  {group:'Decision screens',id:'utilization_ceiling',label:'Utilization ceiling',value:.9,min:.1,max:1,step:.01,help:'Applied to both stages'},
  {group:'Cost & baseline',id:'baseline_pickers',label:'Baseline pickers',value:2,min:1,max:6,step:1,help:'Current-state comparison'},
  {group:'Cost & baseline',id:'baseline_packers',label:'Baseline packers',value:2,min:1,max:6,step:1,help:'Current-state comparison'},
  {group:'Cost & baseline',id:'hourly_wage',label:'Wage / worker-hour (CU)',value:100,min:0,max:10000,step:1,help:'Scheduled labor cost'},
  {group:'Cost & baseline',id:'payroll_budget',label:'Shift payroll budget (CU)',value:4800,min:0,max:1000000,step:1,help:'Maximum screen value'},
  {group:'Reproducibility',id:'seed',label:'Reproducible seed',value:42,min:0,max:1000000,step:1,help:'Controls generated workloads'}
];

function buildFields(){
  const groups=new Map();
  for(const spec of specs){
    if(!groups.has(spec.group)){
      const fieldset=document.createElement('fieldset');
      fieldset.className='assumption-group';
      const legend=document.createElement('legend');
      legend.textContent=spec.group.toUpperCase();
      fieldset.append(legend);
      groups.set(spec.group,fieldset);
      $('fields').append(fieldset);
    }
    const box=document.createElement('div');
    const label=document.createElement('label');
    const input=document.createElement('input');
    const help=document.createElement('p');
    label.htmlFor=spec.id;label.textContent=spec.label;
    Object.assign(input,{id:spec.id,type:'number',value:spec.value,min:spec.min,max:spec.max,step:spec.step,required:true});
    help.className='field-help';help.textContent=spec.help;
    box.append(label,input,help);groups.get(spec.group).append(box);
  }
}
buildFields();

let origin='user-provided; provenance unverified',quality=null,serviceSource='manual',exports=null;
const staticMode=location.hostname.endsWith('.github.io')||location.pathname.includes('/operations-decision-lab/')||location.protocol==='file:'||new URLSearchParams(location.search).has('static');
const number=(value,digits=1)=>value===null||value===undefined?'n/a':Number(value).toFixed(digits);
const percent=value=>value===null||value===undefined?'n/a':`${(value*100).toFixed(1)}%`;

function setProgress(stage){
  const order=['evidence','assumptions','decision'],activeIndex=order.indexOf(stage);
  for(const [index,name] of order.entries()){
    const item=$(`progress-${name}`);
    item.classList.toggle('active',index===activeIndex);item.classList.toggle('complete',index<activeIndex);
  }
}
function message(text,type='progress'){const box=$('message');box.hidden=!text;box.className=type;box.textContent=text;}
function detailLine(parent,label,value){const row=document.createElement('div'),name=document.createElement('span'),content=document.createElement('strong');row.className='detail-row';name.textContent=label;content.textContent=value;row.append(name,content);parent.append(row);}
async function api(path,body){
  if(staticMode){
    if(!window.DecisionLabStatic)throw Error('The browser analysis engine did not load. Refresh the page.');
    if(path==='/api/inspect')return window.DecisionLabStatic.inspectCsv(body.csv,body.window_start,body.window_end);
    if(path==='/api/compare')return window.DecisionLabStatic.compareRequest(body);
    throw Error('Unsupported browser operation.');
  }
  const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const raw=await response.text();let data;try{data=JSON.parse(raw);}catch{data={};}
  if(!response.ok)throw Error(data.error||`Request failed (${response.status}).`);return data;
}
function clearResults(){if(exports&&staticMode)for(const url of Object.values(exports.downloads||{}))URL.revokeObjectURL(url);exports=null;$('results').hidden=true;$('empty').hidden=false;setProgress(quality?'assumptions':'evidence');}
function resetSource(){serviceSource='manual';$('service-source').innerHTML='<span aria-hidden="true">◇</span> Service source: explicit manual assumptions';}
function dataChanged(){quality=null;resetSource();clearResults();$('quality').replaceChildren();$('active').checked=false;$('evidence-state').textContent='Not inspected';$('evidence-state').classList.remove('success');}

for(const id of ['csv','window_start','window_end'])$(id).addEventListener('input',()=>{origin='user-provided; provenance unverified';$('origin').lastChild.textContent=' User-provided CSV · provenance unverified';$('origin').classList.toggle('loaded',Boolean($('csv').value));dataChanged();});
for(const spec of specs)$(spec.id).addEventListener('input',()=>{clearResults();if(['pick_minutes','pack_minutes'].includes(spec.id))resetSource();});
$('confirm').addEventListener('change',clearResults);
$('active').addEventListener('change',()=>{resetSource();clearResults();});

async function loadSample(){
  const buttons=[$('sample'),$('hero-sample'),$('empty-sample')];buttons.forEach(button=>{button.disabled=true;});
  try{
    let sample;
    if(staticMode){const response=await fetch('static/synthetic.csv');if(!response.ok)throw Error(`Sample could not be loaded (${response.status}).`);sample={csv:await response.text(),window_start:'2026-01-05T08:00:00+00:00',window_end:'2026-01-05T16:00:00+00:00',data_origin:'synthetic demo'};
    }else{const response=await fetch('/api/sample');if(!response.ok)throw Error(`Sample could not be loaded (${response.status}).`);sample=await response.json();}
    dataChanged();$('csv').value=sample.csv;$('window_start').value=sample.window_start;$('window_end').value=sample.window_end;origin=sample.data_origin;
    $('origin').lastChild.textContent=' Synthetic · original generated demonstration data';$('origin').classList.add('loaded');message('Synthetic sample loaded. Inspect the evidence before comparing.');$('evidence').scrollIntoView({block:'start'});
  }catch(error){message(error.message,'error');}finally{buttons.forEach(button=>{button.disabled=false;});}
}
for(const id of ['sample','hero-sample','empty-sample'])$(id).addEventListener('click',loadSample);

$('file').addEventListener('change',async event=>{
  try{const file=event.target.files[0];if(!file)return;if(file.size>2000000)throw Error('CSV exceeds the 2 MB limit.');const bytes=await file.arrayBuffer();$('csv').value=new TextDecoder('utf-8',{fatal:true}).decode(bytes);dataChanged();origin='user-provided; provenance unverified';$('origin').lastChild.textContent=` ${file.name} · provenance unverified`;$('origin').classList.add('loaded');message('CSV loaded locally. Set its observation window and inspect.');}catch(error){message(error.message,'error');}
});
function dataInput(){return{csv:$('csv').value,window_start:$('window_start').value,window_end:$('window_end').value};}
function qualityStat(parent,label,value){const card=document.createElement('div'),name=document.createElement('span'),content=document.createElement('strong');card.className='quality-stat';name.textContent=label;content.textContent=value;card.append(name,content);parent.append(card);}
async function inspect(){
  quality=await api('/api/inspect',dataInput());const report=$('quality');report.replaceChildren();const heading=document.createElement('h3'),grid=document.createElement('div');heading.textContent='Evidence summary';grid.className='quality-grid';
  qualityStat(grid,'Orders / initial WIP',`${quality.arrivals_in_window} / ${quality.initial_wip}`);qualityStat(grid,'Observed arrivals / hour',number(quality.arrival_rate_observed));qualityStat(grid,'Completed / unfinished',`${quality.completions_in_window} / ${quality.unfinished_arrival_cohort}`);qualityStat(grid,'Pick / pack means (min)',`${number(quality.elapsed_interval_means.pick)} / ${number(quality.elapsed_interval_means.pack)}`);report.append(heading,grid);
  if(quality.warnings.length){const warnings=document.createElement('ul');for(const warning of quality.warnings){const item=document.createElement('li');item.textContent=warning;warnings.append(item);}report.append(warnings);}
  $('evidence-state').textContent='Inspected';$('evidence-state').classList.add('success');setProgress('assumptions');return quality;
}
$('inspect').addEventListener('click',async()=>{const button=$('inspect');button.disabled=true;message('Inspecting schema, time window, and service intervals…','progress busy');try{await inspect();message('Evidence inspected. Service inputs remain explicit assumptions.');}catch(error){quality=null;$('quality').replaceChildren();clearResults();message(error.message,'error');}finally{button.disabled=false;}});
$('adopt').addEventListener('click',()=>{if(!quality||!quality.eligible_for_attested_intervals||!$('active').checked){message('Inspect eligible complete data and confirm uninterrupted active service before adopting means.','error');return;}clearResults();for(const stage of ['pick','pack']){$(`${stage}_minutes`).value=quality.elapsed_interval_means[stage];$(`${stage}_minutes`).step='any';}serviceSource='attested_intervals';$('service-source').innerHTML='<span aria-hidden="true">◆</span> Service source: observed intervals, explicitly attested as active service';message('Service means adopted. Review demand, variability, backlog, and calendar assumptions separately.');});

function renderMetrics(report){
  const evaluation=report.results.evaluation,metrics=$('metrics');metrics.replaceChildren();
  for(const [label,value] of [['Selected allocation',`${evaluation.pickers} pick / ${evaluation.packers} pack`],['Nominal capacity',`${number(evaluation.capacity_per_hour,2)} / h`],['Due-cohort SLA',percent(evaluation.stats.sla_fraction.mean)],['Unfinished at close',number(evaluation.stats.unfinished.mean)]]){const card=document.createElement('div'),content=document.createElement('b'),name=document.createElement('span');card.className='metric';content.textContent=value;name.textContent=label;card.append(content,name);metrics.append(card);}
}
function renderScenarios(report){
  const results=report.results,selected=results.selected_allocation,visual=$('scenario-visual'),body=$('scenario-table').querySelector('tbody'),maxCapacity=Math.max(report.inputs.config.arrival_rate,...results.scenarios.map(item=>item.capacity_per_hour));visual.replaceChildren();body.replaceChildren();
  for(const scenario of results.scenarios){
    const chosen=scenario.pickers===selected.pickers&&scenario.packers===selected.packers,bar=document.createElement('div'),name=document.createElement('strong'),meter=document.createElement('meter'),value=document.createElement('span');bar.className=`scenario-bar${chosen?' selected':''}`;name.textContent=`${scenario.pickers} / ${scenario.packers}${chosen?' ★':''}`;meter.min=0;meter.max=maxCapacity;meter.value=scenario.capacity_per_hour;meter.setAttribute('aria-label',`${scenario.pickers} pickers and ${scenario.packers} packers nominal capacity`);value.textContent=`${number(scenario.capacity_per_hour,2)} / h`;bar.append(name,meter,value);visual.append(bar);
    const row=document.createElement('tr');for(const text of [`${scenario.pickers} / ${scenario.packers}`,number(scenario.capacity_per_hour,2),number(scenario.payroll,0),percent(scenario.stats.sla_fraction.mean),number(scenario.stats.unfinished.mean)]){const cell=document.createElement('td');cell.textContent=text;row.append(cell);}const screenCell=document.createElement('td'),badge=document.createElement('span');badge.className=`screen-badge ${scenario.feasible?'pass':'fail'}`;badge.textContent=scenario.feasible?'Pass':'Fails';badge.title=scenario.feasible?'All conditional screens passed':scenario.reasons.join(' ');screenCell.append(badge);row.append(screenCell);body.append(row);
  }
}
function render(report){
  const results=report.results,evaluation=results.evaluation;$('empty').hidden=true;$('results').hidden=false;$('decision').textContent=results.confirmed_feasible?'A conditional option worth investigating.':'No confirmed feasible option.';$('decision-status').textContent=results.confirmed_feasible?'CONDITIONAL PASS':'NO CONFIRMED OPTION';$('decision-status').classList.toggle('negative',!results.confirmed_feasible);$('decision-detail').textContent=`${results.selected_allocation.pickers} picking / ${results.selected_allocation.packers} packing is ${results.confirmed_feasible?'the lowest-payroll candidate that also passed independent evaluation':'the selected candidate—not a sufficient staffing recommendation'}. ${report.inputs.data_origin}. Hypothetical results only.`;renderMetrics(report);renderScenarios(report);
  $('evaluation-copy').textContent=`30 new seeds, separate from selection. ${evaluation.feasible?'This allocation passes the conditional screens on this evaluation set.':`This allocation fails one or more screens: ${evaluation.reasons.join(' ')}`}`;const evaluationDetail=$('evaluation');evaluationDetail.replaceChildren();for(const [label,key,format] of [['Due-cohort SLA','sla_fraction',percent],['Throughput / hour','throughput_per_hour',number],['Unfinished orders','unfinished',number],['Completed-only cycle / min','completed_cycle_mean',number]]){const stats=evaluation.stats[key];detailLine(evaluationDetail,label,`${format(stats.mean)} · ${format(stats.low)} to ${format(stats.high)}`);}detailLine(evaluationDetail,'Scheduled / marginal payroll',`${number(evaluation.payroll,0)} / ${number(evaluation.marginal_payroll,0)} CU`);$('interval-copy').textContent=results.interval_method;
  const baseline=results.baseline;$('baseline-copy').textContent=`${baseline.pickers} picking → ${baseline.packers} packing. ${baseline.bottleneck} is the nominal bottleneck at ${number(report.inputs.config.arrival_rate)} orders/hour demand.`;const baselineDetail=$('baseline');baselineDetail.replaceChildren();for(const stage of ['pick','pack'])detailLine(baselineDetail,`${stage==='pick'?'Picking':'Packing'} utilization / queue`,`${percent(baseline.stats[`${stage}_utilization`].mean)} / ${number(baseline.stats[`${stage}_mean_queue`].mean)} orders`);detailLine(baselineDetail,'Unfinished at close',number(baseline.stats.unfinished.mean));
  const sensitivity=$('sensitivity');sensitivity.replaceChildren();for(const scenario of results.sensitivity){const card=document.createElement('div'),title=document.createElement('strong'),sla=document.createElement('span'),unfinished=document.createElement('span'),state=document.createElement('em');card.className='sensitivity-card';title.textContent=scenario.label;sla.textContent=`${percent(scenario.stats.sla_fraction.mean)} due SLA`;unfinished.textContent=`${number(scenario.stats.unfinished.mean)} unfinished`;state.textContent=scenario.feasible?'Conditional pass':'Fails screen';state.className=scenario.feasible?'pass':'';card.append(title,sla,unfinished,state);sensitivity.append(card);}
  $('limits').replaceChildren();for(const text of report.limitations){const item=document.createElement('li');item.textContent=text;$('limits').append(item);}$('hash').textContent=`Input SHA-256 ${report.input_sha256}`;setProgress('decision');
}
$('assumptions').addEventListener('submit',async event=>{
  event.preventDefault();const button=$('compare');button.disabled=true;clearResults();message('Running bounded experiments and independent evaluation…','progress busy');
  try{await inspect();const config=Object.fromEntries(specs.map(spec=>[spec.id,Number($(spec.id).value)]));const payload={...dataInput(),config,assumptions_confirmed:$('confirm').checked,service_source:serviceSource,active_service_confirmed:$('active').checked,data_origin:origin};const result=await api('/api/compare',payload);exports=result;render(result.report);message('Comparison complete. Review the independent evaluation and model boundaries.');$('decision-output').scrollIntoView({block:'start'});}catch(error){message(error.message,'error');}finally{button.disabled=false;}
});
function download(format){if(!exports)return;const link=document.createElement('a');link.href=exports.downloads[format];link.download=`operations-decision-report.${format}`;document.body.append(link);link.click();link.remove();}
$('export-json').addEventListener('click',()=>download('json'));$('export-html').addEventListener('click',()=>download('html'));
