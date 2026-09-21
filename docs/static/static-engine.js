(function(root,factory){
  const api=factory();
  root.DecisionLabStatic=api;
  if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const REPLICATIONS=30,T29=2.045229642132703,MAX_JOBS=2000;
  const METRICS=['completed','unfinished','sla_fraction','completed_cycle_mean','completed_cycle_p95','throughput_per_hour','pick_utilization','pack_utilization','pick_mean_queue','pack_mean_queue'];
  const LIMITATIONS=[
    'Hypothetical research prototype. No externally validated prediction or staffing recommendation.',
    'Poisson arrivals; independent lognormal service; homogeneous dedicated workers; FIFO; no batching or sharing.',
    'One shift only. Work pauses over the common midpoint break. No overtime or queue drain.',
    'Initial backlog is queued at the stated stage at time zero; prior age and in-service work are unsupported.',
    'Service target uses only new orders whose SLA deadline falls within the shift. Younger orders are excluded.',
    'Completed-only cycle statistics exclude unfinished work and can look optimistic under overload.',
    'Nominal capacity is a necessary sustained-load screen, not evidence of long-run or real-world performance.',
    'Payroll covers every scheduled worker-hour, including breaks/idle time, in user-defined currency units.',
    'No overtime, revenue, penalties or causal savings are calculated. Marginal payroll is relative to the baseline.',
    'Confidence intervals describe replication means conditional on assumptions; sensitivity is not validation.',
    'Exports contain the exact input CSV. Review before sharing; uploaded data remains in this browser session.'
  ];

  const average=values=>values.length?values.reduce((sum,value)=>sum+value,0)/values.length:null;
  const finite=value=>typeof value==='number'&&Number.isFinite(value);
  function stable(value){
    if(Array.isArray(value))return value.map(stable);
    if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(key=>[key,stable(value[key])]));
    return value;
  }
  const stableJson=value=>JSON.stringify(stable(value),null,2)+'\n';
  async function sha256(text){
    const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
    return Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
  }

  function parseCsv(text){
    const rows=[];let row=[],field='',quoted=false;
    for(let index=0;index<text.length;index++){
      const character=text[index];
      if(quoted){
        if(character==='"'&&text[index+1]==='"'){field+='"';index++;}
        else if(character==='"')quoted=false;
        else field+=character;
      }else if(character==='"'&&!field){quoted=true;
      }else if(character===','){row.push(field);field='';
      }else if(character==='\n'){row.push(field.replace(/\r$/,''));rows.push(row);row=[];field='';
      }else field+=character;
    }
    if(quoted)throw Error('Malformed CSV: unclosed quoted field.');
    if(field||row.length){row.push(field.replace(/\r$/,''));rows.push(row);}
    return rows.filter((item,index)=>item.some(value=>value.trim())||index===0);
  }
  function timestamp(value){
    if(typeof value!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(value.trim()))throw Error('Use ISO 8601 timestamps with a UTC offset.');
    const result=new Date(value.trim());if(Number.isNaN(result.getTime()))throw Error('Use ISO 8601 timestamps with a UTC offset.');return result;
  }
  async function inspectCsv(text,windowStart,windowEnd){
    if(typeof text!=='string'||new TextEncoder().encode(text).length>2000000)throw Error('CSV must be UTF-8 text, at most 2 MB.');
    const start=timestamp(windowStart),end=timestamp(windowEnd),hours=(end-start)/3600000;
    if(!(hours>0&&hours<=24*366))throw Error('Observation window must be positive and at most 366 days.');
    const parsed=parseCsv(text.replace(/^\uFEFF/,''));if(!parsed.length)throw Error('CSV contains no orders.');
    const names=parsed[0].map(name=>name.trim()),required=['order_id','arrival_time','pick_start','pick_end','pack_start','pack_end'],allowed=new Set([...required,'picker','packer']);
    if(new Set(names).size!==names.length||required.some(name=>!names.includes(name)))throw Error(`CSV needs unique headers: ${required.slice().sort().join(', ')}`);
    if(names.some(name=>!allowed.has(name)))throw Error('Unsupported CSV columns. Use only the documented schema.');
    if(parsed.length===1)throw Error('CSV contains no orders.');if(parsed.length-1>5000)throw Error('CSV exceeds the 5,000-order limit.');
    const seen=new Set(),rows=[];let missingStarts=0,censoredEvents=0;
    for(let index=1;index<parsed.length;index++){
      const values=parsed[index];if(values.length!==names.length)throw Error('CSV row has the wrong number of fields.');
      const raw=Object.fromEntries(names.map((name,column)=>[name,values[column]])),identifier=raw.order_id.trim();
      if(!identifier||identifier.length>128||seen.has(identifier))throw Error(`Row ${index+1}: order_id must be unique, nonempty and <=128 characters.`);seen.add(identifier);
      const times={};for(const key of required.slice(1))times[key]=raw[key].trim()?timestamp(raw[key]):null;
      if(!times.arrival_time||times.arrival_time>=end)throw Error(`Row ${index+1}: arrival_time is required and must precede window end.`);
      const known=required.slice(1).map(key=>times[key]).filter(Boolean);if(known.some((value,position)=>position&&known[position-1]>value))throw Error(`Row ${index+1}: timestamps are out of process order.`);
      for(const stage of ['pick','pack']){const a=times[`${stage}_start`],b=times[`${stage}_end`];if(a&&b&&a.getTime()===b.getTime())throw Error(`Row ${index+1}: recorded stage durations must be positive.`);if(b&&!a)missingStarts++;}
      if((times.pack_start||times.pack_end)&&!times.pick_end)throw Error(`Row ${index+1}: packing requires a recorded picking completion.`);
      for(const key of required.slice(2)){if(times[key]&&times[key]>end){times[key]=null;censoredEvents++;}}
      rows.push({...times,picker:(raw.picker||'').trim(),packer:(raw.packer||'').trim()});
    }
    const cohort=rows.filter(row=>row.arrival_time>=start),completed=cohort.filter(row=>row.pack_end),backlog=rows.filter(row=>row.arrival_time<start&&(!row.pack_end||row.pack_end>start));
    const completions=rows.filter(row=>row.pack_end&&row.pack_end>=start&&row.pack_end<=end).length,means={},resources=new Map(),workers={pick:new Set(),pack:new Set()};let missingResources=0,overlaps=0;
    for(const [stage,resource] of [['pick','picker'],['pack','packer']]){
      const intervals=rows.filter(row=>row[`${stage}_start`]&&row[`${stage}_end`]&&row[`${stage}_start`]>=start).map(row=>[row[`${stage}_start`],row[`${stage}_end`],row[resource]]);
      means[stage]=average(intervals.map(([a,b])=>(b-a)/60000));
      for(const [a,b,who] of intervals){if(!who)missingResources++;else{if(!resources.has(who))resources.set(who,[]);resources.get(who).push([a,b]);workers[stage].add(who);}}
    }
    for(const spans of resources.values()){let latest=null;for(const [a,b] of spans.sort((left,right)=>left[0]-right[0])){if(latest&&a<latest)overlaps++;if(!latest||b>latest)latest=b;}}
    const sharedWorkers=[...workers.pick].filter(worker=>workers.pack.has(worker)).length,unfinished=cohort.length-completed.length;
    const warnings=['Observed intervals are elapsed processing time, not proven active labor.','Calendars, pauses, task mix and dedicated staffing are not established by this CSV.','Cycle statistics use completed arrival-cohort orders and can be biased by censoring.'];
    if(missingStarts)warnings.push('Completion-only stages: service time is unknown. Supply explicit assumptions.');if(unfinished||censoredEvents)warnings.push('Incomplete or future stages are censored at observation end; no duration imputation.');if(overlaps)warnings.push('Overlapping work for a worker conflicts with the dedicated single-task model.');if(backlog.length)warnings.push('Pre-window work exists. Enter initial stage queues explicitly; ages are not reconstructed.');if(sharedWorkers)warnings.push('Workers appear in both roles; the dedicated staffing model is unsupported.');if(missingResources)warnings.push('Missing worker IDs prevent a complete overlap audit.');
    const cycles=completed.map(row=>(row.pack_end-row.arrival_time)/60000),eligible=cohort.length>=10&&completed.length===cohort.length&&!backlog.length&&!missingStarts&&!overlaps&&!sharedWorkers&&!censoredEvents&&!missingResources&&means.pick!==null&&means.pack!==null;
    return{sha256:await sha256(text),rows:rows.length,window_hours:hours,arrivals_in_window:cohort.length,initial_wip:backlog.length,completions_in_window:completions,unfinished_arrival_cohort:unfinished,arrival_rate_observed:cohort.length/hours,throughput_observed:completions/hours,completed_cycle_mean:average(cycles),elapsed_interval_means:means,missing_starts:missingStarts,overlap_count:overlaps,shared_workers:sharedWorkers,missing_resources:missingResources,future_endpoints_censored:censoredEvents,eligible_for_attested_intervals:eligible,warnings};
  }

  function rng(seed){let state=(seed>>>0)||1;return()=>{state|=0;state=state+0x6D2B79F5|0;let value=Math.imul(state^state>>>15,1|state);value=value+Math.imul(value^value>>>7,61|value)^value;return((value^value>>>14)>>>0)/4294967296;};}
  const exponential=(random,rate)=>-Math.log(Math.max(Number.EPSILON,1-random()))/rate;
  function normal(random){const a=Math.max(Number.EPSILON,random()),b=random();return Math.sqrt(-2*Math.log(a))*Math.cos(2*Math.PI*b);}
  function workload(config,seed){
    const arrivals=rng(seed),picking=rng(seed+10000019),packing=rng(seed+20000033),sigma=Math.sqrt(Math.log1p(config.service_cv**2));
    const duration=(random,avg)=>sigma===0?avg:Math.exp(Math.log(avg)-sigma*sigma/2+sigma*normal(random));const jobs=[];
    for(const [stage,count] of [['pick',config.initial_pick],['pack',config.initial_pack]])for(let index=0;index<count;index++)jobs.push({arrival:0,pick:duration(picking,config.pick_minutes),pack:duration(packing,config.pack_minutes),initial_stage:stage});
    let at=exponential(arrivals,config.arrival_rate/60),cutoff=config.shift_hours*60;while(at<cutoff){if(jobs.length>=MAX_JOBS)throw Error('Generated workload exceeds the 2,000-job limit; reduce demand.');jobs.push({arrival:at,pick:duration(picking,config.pick_minutes),pack:duration(packing,config.pack_minutes),initial_stage:'new'});at+=exponential(arrivals,config.arrival_rate/60);}return jobs;
  }
  function scheduleStage(items,staff,stage,config){
    const available=Array(staff).fill(0),cutoff=config.shift_hours*60,b0=cutoff/2,b1=b0+config.break_minutes;
    for(const item of items.sort((a,b)=>a.ready-b.ready||a.id-b.id)){
      let worker=0;for(let index=1;index<available.length;index++)if(available[index]<available[worker])worker=index;
      let start=Math.max(item.ready,available[worker]);if(start>=b0&&start<b1)start=b1;let finish=start+item.duration;if(start<b0&&finish>b0)finish+=config.break_minutes;
      item.row[`${stage}_ready`]=item.ready;item.row[`${stage}_start`]=start;item.row[`${stage}_planned_end`]=finish;if(finish<=cutoff)item.row[`${stage}_end`]=finish;available[worker]=finish;
    }
  }
  function activeTime(start,end,config){const cutoff=config.shift_hours*60,b0=cutoff/2,b1=b0+config.break_minutes,stop=Math.min(end,cutoff);if(stop<=start)return 0;return stop-start-Math.max(0,Math.min(stop,b1)-Math.max(start,b0));}
  function simulate(config,pickers,packers,jobs){
    const cutoff=config.shift_hours*60,rows=jobs.slice().sort((a,b)=>a.arrival-b.arrival).map((job,id)=>({id,arrival:job.arrival,initial_stage:job.initial_stage,job}));
    const picking=rows.filter(row=>row.initial_stage!=='pack').map(row=>({id:row.id,ready:row.arrival,duration:row.job.pick,row}));scheduleStage(picking,pickers,'pick',config);
    const packing=rows.filter(row=>row.initial_stage==='pack'||row.pick_end!==undefined).map(row=>({id:row.id,ready:row.initial_stage==='pack'?0:row.pick_end,duration:row.job.pack,row}));scheduleStage(packing,packers,'pack',config);
    const completed=rows.filter(row=>row.pack_end!==undefined),fresh=rows.filter(row=>row.initial_stage==='new'),due=fresh.filter(row=>row.arrival+config.sla_minutes<=cutoff),onTime=due.filter(row=>(row.pack_end??Infinity)<=row.arrival+config.sla_minutes),cycles=completed.filter(row=>row.initial_stage==='new').map(row=>row.pack_end-row.arrival).sort((a,b)=>a-b);
    const result={arrivals:fresh.length,initial_backlog:rows.length-fresh.length,completed:completed.length,unfinished:rows.length-completed.length,due_orders:due.length,on_time_due:onTime.length,sla_fraction:due.length?onTime.length/due.length:null,completed_cycle_mean:average(cycles),completed_cycle_p95:cycles.length?cycles[Math.ceil(.95*cycles.length)-1]:null,throughput_per_hour:completed.length/config.shift_hours};
    for(const [stage,staff] of [['pick',pickers],['pack',packers]]){result[`${stage}_utilization`]=rows.filter(row=>row[`${stage}_start`]!==undefined&&row[`${stage}_start`]<=cutoff).reduce((sum,row)=>sum+activeTime(row[`${stage}_start`],row[`${stage}_planned_end`],config),0)/(staff*(cutoff-config.break_minutes));result[`${stage}_mean_queue`]=rows.filter(row=>row[`${stage}_ready`]!==undefined).reduce((sum,row)=>sum+Math.min(row[`${stage}_start`]??cutoff,cutoff)-row[`${stage}_ready`],0)/cutoff;}
    return result;
  }
  function capacity(config,pickers,packers){const fraction=1-config.break_minutes/(config.shift_hours*60),pickCapacity=pickers*60/config.pick_minutes*fraction,packCapacity=packers*60/config.pack_minutes*fraction,rho=Math.max(config.arrival_rate/pickCapacity,config.arrival_rate/packCapacity),payroll=(pickers+packers)*config.shift_hours*config.hourly_wage;return{pick_capacity:pickCapacity,pack_capacity:packCapacity,capacity_per_hour:Math.min(pickCapacity,packCapacity),max_nominal_utilization:rho,stable:rho<1,capacity_pass:rho<1&&rho<=config.utilization_ceiling,bottleneck:pickCapacity<packCapacity?'picking':packCapacity<pickCapacity?'packing':'balanced',payroll,budget_pass:payroll<=config.payroll_budget,marginal_payroll:payroll-(config.baseline_pickers+config.baseline_packers)*config.shift_hours*config.hourly_wage};}
  function interval(values){const numeric=values.filter(finite);if(!numeric.length)return{mean:null,low:null,high:null,n:0};const mean=average(numeric);if(numeric.length!==REPLICATIONS)return{mean,low:null,high:null,n:numeric.length};const variance=numeric.reduce((sum,value)=>sum+(value-mean)**2,0)/(numeric.length-1),half=T29*Math.sqrt(variance)/Math.sqrt(numeric.length);return{mean,low:mean-half,high:mean+half,n:numeric.length};}
  function evaluate(config,pickers,packers,seeds){const runs=seeds.map(seed=>({seed,...simulate(config,pickers,packers,workload(config,seed))})),stats=Object.fromEntries(METRICS.map(key=>[key,interval(runs.map(run=>run[key]))])),screen=capacity(config,pickers,packers),low=stats.sla_fraction.low,servicePass=low!==null&&low>=config.target_fraction,reasons=[];if(!screen.stable)reasons.push('Demand meets or exceeds nominal capacity.');else if(!screen.capacity_pass)reasons.push('Utilization exceeds the chosen safety ceiling.');if(!screen.budget_pass)reasons.push('Scheduled payroll exceeds budget.');if(!servicePass)reasons.push('Due-cohort service target not supported by the lower confidence bound.');return{pickers,packers,...screen,stats,feasible:!reasons.length,reasons,runs};}
  function validateConfig(config){const limits={arrival_rate:[.1,60],pick_minutes:[.1,60],pack_minutes:[.1,60],service_cv:[0,2],shift_hours:[2,12],break_minutes:[0,60],initial_pick:[0,100],initial_pack:[0,100],max_workers:[2,6],baseline_pickers:[1,6],baseline_packers:[1,6],hourly_wage:[0,10000],payroll_budget:[0,1000000],sla_minutes:[1,240],target_fraction:[.5,1],utilization_ceiling:[.1,1],seed:[0,1000000]},integers=new Set(['initial_pick','initial_pack','max_workers','baseline_pickers','baseline_packers','seed']);for(const [name,[low,high]] of Object.entries(limits)){const value=config[name];if(!finite(value)||value<low||value>high)throw Error(`${name} must be a finite number from ${low} to ${high}.`);if(integers.has(name)&&!Number.isInteger(value))throw Error(`${name} must be an integer.`);}if(config.sla_minutes>=config.shift_hours*60)throw Error('SLA must be shorter than the shift, so a due cohort exists.');if(config.baseline_pickers+config.baseline_packers>6)throw Error('Baseline may use at most six workers.');}
  function compare(config){
    validateConfig(config);const selectionSeeds=Array.from({length:REPLICATIONS},(_,index)=>config.seed+index),evaluationSeeds=Array.from({length:REPLICATIONS},(_,index)=>config.seed+1000000+index),scenarios=[];
    for(let total=2;total<=config.max_workers;total++)for(let pickers=1;pickers<total;pickers++)scenarios.push(evaluate(config,pickers,total-pickers,selectionSeeds));
    const feasible=scenarios.filter(scenario=>scenario.feasible),selected=feasible.length?feasible.slice().sort((a,b)=>a.payroll-b.payroll||(b.stats.sla_fraction.mean??0)-(a.stats.sla_fraction.mean??0)||a.pickers-b.pickers)[0]:scenarios.slice().sort((a,b)=>(b.stats.sla_fraction.mean??0)-(a.stats.sla_fraction.mean??0)||a.stats.unfinished.mean-b.stats.unfinished.mean||a.payroll-b.payroll)[0],checked=evaluate(config,selected.pickers,selected.packers,evaluationSeeds),baseline=evaluate(config,config.baseline_pickers,config.baseline_packers,evaluationSeeds);
    const changes=[['Arrivals +20%',{...config,arrival_rate:Math.min(60,config.arrival_rate*1.2)}],['Service means +20%',{...config,pick_minutes:Math.min(60,config.pick_minutes*1.2),pack_minutes:Math.min(60,config.pack_minutes*1.2)}],['Service CV at least 1',{...config,service_cv:Math.max(1,config.service_cv)}]],stressSeeds=Array.from({length:REPLICATIONS},(_,index)=>config.seed+2000000+index),sensitivity=changes.map(([label,changed])=>({label:`${label} (capped at supported limits)`,arrival_rate:changed.arrival_rate,pick_minutes:changed.pick_minutes,pack_minutes:changed.pack_minutes,service_cv:changed.service_cv,...evaluate(changed,selected.pickers,selected.packers,stressSeeds)}));
    const confirmed=Boolean(feasible.length)&&checked.feasible;return{status:confirmed?'CONDITIONALLY FEASIBLE':'NO CONFIRMED FEASIBLE OPTION',selection_status:feasible.length?'candidate passed selection':'no feasible option in selection',selected_allocation:{pickers:selected.pickers,packers:selected.packers},confirmed_feasible:confirmed,selection_seeds:selectionSeeds,evaluation_seeds:evaluationSeeds,scenarios,evaluation:checked,baseline,sensitivity,interval_method:'95% Student-t interval for a replication mean, df=29, n=30. Approximate Monte Carlo uncertainty only; not a prediction interval or input/model uncertainty. Missing due cohorts suppress the SLA confidence interval and cannot pass the target.'};
  }
  function escapeHtml(value){return String(value).replace(/[&<>"']/g,character=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));}
  function reportHtml(report){const rows=report.results.scenarios.map(item=>`<tr><td>${item.pickers} / ${item.packers}</td><td>${item.capacity_per_hour.toFixed(2)}</td><td>${item.payroll.toFixed(2)}</td><td>${item.stats.sla_fraction.mean===null?'n/a':(item.stats.sla_fraction.mean*100).toFixed(1)+'%'}</td><td>${item.stats.unfinished.mean.toFixed(1)}</td><td>${item.feasible?'Pass':escapeHtml(item.reasons.join(' '))}</td></tr>`).join(''),limits=report.limitations.map(item=>`<li>${escapeHtml(item)}</li>`).join('');return`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Operations Decision Lab — report</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:24px;color:#15342e}table{border-collapse:collapse;width:100%}td,th{padding:12px;border-bottom:1px solid #ccd8d3;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f4f1;padding:20px}.flag{padding:16px;background:#fff0cf}</style><h1>Operations Decision Lab</h1><p class="flag">${escapeHtml(report.evidence_class)}</p><h2>${escapeHtml(report.results.status)}</h2><p>Selected allocation: ${report.results.selected_allocation.pickers} picking / ${report.results.selected_allocation.packers} packing.</p><h2>Selection results</h2><table><thead><tr><th>Pick / pack</th><th>Capacity / h</th><th>Payroll</th><th>Due SLA</th><th>Unfinished</th><th>Screen</th></tr></thead><tbody>${rows}</tbody></table><h2>Interpretation and limits</h2><ul>${limits}</ul><h2>Complete reproducibility record</h2><pre>${escapeHtml(stableJson(report))}</pre></html>`;}
  async function makeReport(request){if(request.assumptions_confirmed!==true)throw Error('Confirm the hypothetical model assumptions before comparing.');validateConfig(request.config);const quality=await inspectCsv(request.csv,request.window_start,request.window_end);if(request.service_source==='attested_intervals'){if(request.active_service_confirmed!==true||!quality.eligible_for_attested_intervals)throw Error('Observed interval adoption requires complete eligible data and active-service confirmation.');for(const stage of ['pick','pack'])if(Math.abs(request.config[`${stage}_minutes`]-quality.elapsed_interval_means[stage])>1e-6)throw Error('Adopted service means must match the inspected intervals exactly.');}
    const inputs={csv:request.csv,window_start:request.window_start,window_end:request.window_end,config:request.config,assumptions_confirmed:true,service_source:request.service_source||'manual',active_service_confirmed:request.active_service_confirmed===true,data_origin:request.data_origin},report={schema_version:1,model_version:'0.1.0-web',evidence_class:'HYPOTHETICAL — NOT EXTERNALLY VALIDATED',inputs,data_quality:quality,results:compare(request.config),limitations:LIMITATIONS,environment:{runtime:'browser',engine:'Operations Decision Lab static engine'}};report.input_sha256=await sha256(stableJson(inputs));return report;}
  async function compareRequest(request){const report=await makeReport(request),json=stableJson(report),html=reportHtml(report);return{report,json,html,downloads:{json:URL.createObjectURL(new Blob([json],{type:'application/json'})),html:URL.createObjectURL(new Blob([html],{type:'text/html'}))}};}
  return{inspectCsv,compare,makeReport,compareRequest,stableJson};
});
