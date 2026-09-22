'use strict';
const $ = id => document.getElementById(id);
const specs = [
  ['arrival_rate','Arrivals / hour',18,.1,60,.1],['max_workers','Maximum workers',4,2,6,1],
  ['pick_minutes','Mean picking / min',6,.1,60,.1],['pack_minutes','Mean packing / min',7,.1,60,.1],
  ['service_cv','Service CV (SD / mean)',.5,0,2,.1],['shift_hours','Shift length / hours',8,2,12,.5],
  ['break_minutes','Common midpoint break / min',0,0,60,1],['sla_minutes','Order SLA / min',60,1,240,1],
  ['initial_pick','Initial picking queue',0,0,100,1],['initial_pack','Initial packing queue',0,0,100,1],
  ['baseline_pickers','Baseline pickers',2,1,6,1],['baseline_packers','Baseline packers',2,1,6,1],
  ['hourly_wage','Wage / worker-hour (CU)',100,0,10000,1],['payroll_budget','Shift payroll budget (CU)',4800,0,1000000,1],
  ['target_fraction','Due-cohort SLA target',.9,.5,1,.01],['utilization_ceiling','Utilization ceiling',.9,.1,1,.01],
  ['seed','Reproducible seed',42,0,1000000,1]
];
const frictionSpecs = [
  ['travel_congestion_minutes','Travel / congestion delay per picked order (min)',0,0,30,.1],
  ['replenishment_delay_minutes','Replenishment wait per picked order (min)',0,0,30,.1],
  ['inventory_exception_rate','Inventory exception rate (share of orders)',0,0,1,.01],
  ['inventory_exception_recovery_minutes','Exception recovery time (min)',0,0,60,.1],
  ['packing_rework_rate','Packing rework rate (share of orders)',0,0,1,.01],
  ['packing_rework_minutes','Packing rework time (min)',0,0,60,.1]
];
for (const [id,label,value,min,max,step] of specs) {
  const box=document.createElement('div'), l=document.createElement('label'), input=document.createElement('input');
  l.htmlFor=id;l.textContent=label;input.id=id;input.type='number';input.value=value;
  input.min=min;input.max=max;input.step=step;input.required=true;box.append(l,input);$('fields').append(box);
}
for (const [id,label,value,min,max,step] of frictionSpecs) {
  const box=document.createElement('div'), l=document.createElement('label'), input=document.createElement('input');
  l.htmlFor=id;l.textContent=label;input.id=id;input.type='number';input.value=value;
  input.min=min;input.max=max;input.step=step;input.required=true;box.append(l,input);$('friction-fields').append(box);
}
let origin='user-provided; provenance unverified', quality=null, serviceSource='manual', exports=null;
const number=(v,d=1)=>v===null||v===undefined?'n/a':Number(v).toFixed(d);
const percent=v=>v===null||v===undefined?'n/a':`${(v*100).toFixed(1)}%`;
function message(text,error=false){$('message').className=error?'error':'progress';$('message').textContent=text;}
function line(parent,label,value){const row=document.createElement('div');row.className='detail-row';const l=document.createElement('span'),v=document.createElement('strong');l.textContent=label;v.textContent=value;row.append(l,v);parent.append(row);}
async function api(path,body){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw Error(data.error||'Request failed.');return data;}
function clearResults(){exports=null;$('results').hidden=true;$('empty').hidden=false;}
function resetSource(){serviceSource='manual';$('service-source').textContent='Service source: explicit manual assumptions';}
function dataChanged(){quality=null;resetSource();clearResults();$('quality').replaceChildren();$('active').checked=false;}
for(const id of ['csv','window_start','window_end']) $(id).addEventListener('input',()=>{origin='user-provided; provenance unverified';$('origin').textContent=origin;dataChanged();});
for(const [id] of specs) $(id).addEventListener('input',()=>{clearResults();if(['pick_minutes','pack_minutes'].includes(id))resetSource();});
for(const [id] of frictionSpecs) $(id).addEventListener('input',clearResults);
for(const id of ['manual_handling_risk','vehicle_pedestrian_interaction','aisle_or_storage_obstruction','friction-confirm']) $(id).addEventListener('change',clearResults);
$('confirm').addEventListener('change',clearResults);
$('active').addEventListener('change',()=>{resetSource();clearResults();});
$('sample').addEventListener('click',async()=>{try{const s=await(await fetch('/api/sample')).json();dataChanged();$('csv').value=s.csv;$('window_start').value=s.window_start;$('window_end').value=s.window_end;origin=s.data_origin;$('origin').textContent='SYNTHETIC · original generated demonstration data';message('Synthetic sample loaded. Inspect the evidence before comparing.');}catch(e){message(e.message,true);}});
$('file').addEventListener('change',async e=>{try{const f=e.target.files[0];if(!f)return;if(f.size>2000000)throw Error('CSV exceeds the 2 MB limit.');const bytes=await f.arrayBuffer();$('csv').value=new TextDecoder('utf-8',{fatal:true}).decode(bytes);dataChanged();origin='user-provided; provenance unverified';$('origin').textContent='User-provided CSV · provenance unverified';message('CSV loaded locally. Set its observation window and inspect.');}catch(e){message(e.message,true);}});
function dataInput(){return{csv:$('csv').value,window_start:$('window_start').value,window_end:$('window_end').value};}
function frictionInput(){return{friction:Object.fromEntries(frictionSpecs.map(([id])=>[id,Number($(id).value)]).concat([
  ['manual_handling_risk',$('manual_handling_risk').checked],
  ['vehicle_pedestrian_interaction',$('vehicle_pedestrian_interaction').checked],
  ['aisle_or_storage_obstruction',$('aisle_or_storage_obstruction').checked]
])),friction_confirmed:$('friction-confirm').checked};}
async function inspect(){quality=await api('/api/inspect',dataInput());const q=$('quality');q.replaceChildren();const h=document.createElement('h3');h.textContent='Descriptive evidence · observed window';q.append(h);line(q,'Orders / initial WIP',`${quality.arrivals_in_window} / ${quality.initial_wip}`);line(q,'Observed arrivals / hour',number(quality.arrival_rate_observed));line(q,'Completed / unfinished cohort',`${quality.completions_in_window} / ${quality.unfinished_arrival_cohort}`);line(q,'Elapsed pick / pack means (min)',`${number(quality.elapsed_interval_means.pick)} / ${number(quality.elapsed_interval_means.pack)}`);line(q,'Completed-only cycle mean (min)',number(quality.completed_cycle_mean));const ul=document.createElement('ul');for(const w of quality.warnings){const li=document.createElement('li');li.textContent=w;ul.append(li);}q.append(ul);return quality;}
$('inspect').addEventListener('click',async()=>{try{await inspect();message('Data inspected. Service inputs remain explicit assumptions.');}catch(e){quality=null;$('quality').replaceChildren();clearResults();message(e.message,true);}});
$('adopt').addEventListener('click',()=>{if(!quality||!quality.eligible_for_attested_intervals||!$('active').checked){message('Inspect eligible complete data and confirm uninterrupted active service before adopting means.',true);return;}clearResults();for(const s of ['pick','pack']){$(`${s}_minutes`).value=quality.elapsed_interval_means[s];$(`${s}_minutes`).step='any';}serviceSource='attested_intervals';$('service-source').textContent='Service source: observed intervals, explicitly attested as active service';message('Service means adopted. Check demand, variability, backlog and calendar assumptions separately.');});
function metrics(report){const r=report.results,e=r.evaluation,m=$('metrics');m.replaceChildren();for(const[label,value]of[['Selected pick / pack',`${e.pickers} / ${e.packers}`],['Nominal capacity / h',number(e.capacity_per_hour,2)],['Unfinished at close · mean',number(e.stats.unfinished.mean)]]){const card=document.createElement('div');card.className='metric';const v=document.createElement('b'),l=document.createElement('span');v.textContent=value;l.textContent=label;card.append(v,l);m.append(card);}}
function renderFriction(friction){
  $('friction-method').textContent=friction.method_note;
  const summary=$('friction-summary');summary.replaceChildren();
  if(friction.active){
    const adjusted=friction.comparison,e=adjusted.evaluation;
    line(summary,'Adjusted pick / pack service',`${number(friction.base_service_minutes.pick,2)} → ${number(friction.adjusted_service_minutes.pick,2)} / ${number(friction.base_service_minutes.pack,2)} → ${number(friction.adjusted_service_minutes.pack,2)} min`);
    line(summary,'Friction-adjusted selected staff',`${e.pickers} picking / ${e.packers} packing`);
    line(summary,'Friction-adjusted capacity / h',number(e.capacity_per_hour,2));
    line(summary,'Friction-adjusted result',adjusted.status);
  }else{
    const p=document.createElement('p');p.className='small';p.textContent='No timed warehouse friction was applied to this comparison. Add documented local estimates to run a separate adjusted scenario.';summary.append(p);
  }
  const safety=$('friction-safety');safety.replaceChildren();
  if(friction.safety_flags.length){for(const flag of friction.safety_flags){const item=document.createElement('li');item.textContent=`${flag.issue}: ${flag.action}`;safety.append(item);}}
  else {const item=document.createElement('li');item.textContent='No qualitative safety flags were supplied.';safety.append(item);}
  const actions=$('friction-actions');actions.replaceChildren();for(const action of friction.actions){const item=document.createElement('li');item.textContent=action;actions.append(item);}
  const sources=$('friction-sources');sources.replaceChildren();friction.sources.forEach((source,index)=>{if(index)sources.append(' · ');const link=document.createElement('a');link.href=source.url;link.target='_blank';link.rel='noopener';link.textContent=source.title;sources.append(link);});
}
function render(report){const r=report.results,e=r.evaluation;$('empty').hidden=true;$('results').hidden=false;$('decision').textContent=r.confirmed_feasible?'A conditional option to investigate.':'No confirmed feasible option.';$('decision-detail').textContent=`${r.selected_allocation.pickers} picking / ${r.selected_allocation.packers} packing is ${r.confirmed_feasible?'the lowest-payroll selection candidate that also passed independent evaluation':'the selected candidate, not a sufficient staffing recommendation'}. ${report.inputs.data_origin}. Hypothetical results only.`;metrics(report);const tbody=$('scenario-table').querySelector('tbody');tbody.replaceChildren();for(const s of r.scenarios){const tr=document.createElement('tr');for(const value of[`${s.pickers} / ${s.packers}`,number(s.capacity_per_hour,2),number(s.payroll,0),percent(s.stats.sla_fraction.mean),number(s.stats.unfinished.mean),s.feasible?'Pass':s.reasons.join(' ')]){const td=document.createElement('td');td.textContent=value;tr.append(td);}tr.lastChild.className=s.feasible?'pass':'fail';tbody.append(tr);}
$('evaluation-copy').textContent=`30 new seeds, separate from selection. ${e.feasible?'This allocation passes the conditional screens on this evaluation set.':'This allocation fails one or more screens: '+e.reasons.join(' ')}`;const ev=$('evaluation');ev.replaceChildren();for(const[label,key,fmt]of[['Due-cohort SLA','sla_fraction',percent],['Throughput / hour','throughput_per_hour',number],['Unfinished orders','unfinished',number],['Completed-only cycle / min','completed_cycle_mean',number]]){const s=e.stats[key];line(ev,label,`${fmt(s.mean)} · mean interval ${fmt(s.low)} to ${fmt(s.high)}`);}line(ev,'Scheduled / marginal payroll',`${number(e.payroll,0)} / ${number(e.marginal_payroll,0)} CU`);$('interval-copy').textContent=r.interval_method;
const b=r.baseline;$('baseline-copy').textContent=`${b.pickers} picking → ${b.packers} packing. Nominal bottleneck: ${b.bottleneck}. Demand: ${number(report.inputs.config.arrival_rate)} orders/hour.`;const baseline=$('baseline');baseline.replaceChildren();for(const s of['pick','pack'])line(baseline,s==='pick'?'Picking: utilization / mean queue':'Packing: utilization / mean queue',`${percent(b.stats[s+'_utilization'].mean)} / ${number(b.stats[s+'_mean_queue'].mean)} orders`);line(baseline,'Baseline unfinished at close',number(b.stats.unfinished.mean));
const stress=$('sensitivity');stress.replaceChildren();for(const s of r.sensitivity)line(stress,s.label,`${percent(s.stats.sla_fraction.mean)} due SLA · ${number(s.stats.unfinished.mean)} unfinished · ${s.feasible?'conditional pass':'fails screen'}`);renderFriction(report.warehouse_friction);$('limits').replaceChildren();for(const text of report.limitations){const li=document.createElement('li');li.textContent=text;$('limits').append(li);}$('hash').textContent=`Input SHA-256 ${report.input_sha256}`;}
$('assumptions').addEventListener('submit',async event=>{event.preventDefault();$('compare').disabled=true;clearResults();message('Running bounded experiments and independent evaluation…');try{await inspect();const config=Object.fromEntries(specs.map(([id])=>[id,Number($(id).value)]));const payload={...dataInput(),config,...frictionInput(),assumptions_confirmed:$('confirm').checked,service_source:serviceSource,active_service_confirmed:$('active').checked,data_origin:origin};const result=await api('/api/compare',payload);exports=result;render(result.report);message('Comparison complete. Read the independent evaluation, friction screen and model limits before interpreting.');$('message').scrollIntoView({block:'start',behavior:'instant'});}catch(e){message(e.message,true);}finally{$('compare').disabled=false;}});
function download(format){if(!exports)return;const a=document.createElement("a");a.href=exports.downloads[format];a.download=`operations-decision-report.${format}`;document.body.append(a);a.click();a.remove();}
$('export-json').addEventListener('click',()=>download('json'));$('export-html').addEventListener('click',()=>download('html'));
