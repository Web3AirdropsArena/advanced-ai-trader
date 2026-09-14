from __future__ import annotations

DASHBOARD_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Advanced AI Trader — Research Command Center</title>
<style>
:root{color-scheme:dark;--bg:#070a0f;--panel:#0d121a;--panel2:#111823;--line:#263241;--text:#e7edf5;--muted:#8190a3;--cyan:#4dd9ff;--green:#5ee68a;--amber:#f6c85f;--red:#ff6b78;--violet:#b58cff;--blue:#6fa8ff;--shadow:0 18px 50px rgba(0,0,0,.28)}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:radial-gradient(circle at 80% -10%,#142235 0,#070a0f 42%);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--text)}
body{padding:18px}.shell{max-width:1500px;margin:0 auto}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:16px}.eyebrow{font-size:11px;letter-spacing:.18em;color:var(--cyan);font-weight:800}.title{font-size:26px;font-weight:800;margin:4px 0}.sub{color:var(--muted);font-size:13px}.status{display:flex;align-items:center;gap:9px;border:1px solid var(--line);background:#0b1017;padding:9px 12px;border-radius:999px;font-size:12px;font-weight:700}.dot{width:8px;height:8px;border-radius:50%;background:var(--amber);box-shadow:0 0 12px currentColor}.dot.live{background:var(--green)}.dot.bad{background:var(--red)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}.card{background:linear-gradient(180deg,rgba(17,24,35,.96),rgba(10,15,22,.96));border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:15px;min-width:0}.span12{grid-column:span 12}.span8{grid-column:span 8}.span6{grid-column:span 6}.span4{grid-column:span 4}.span3{grid-column:span 3}.label{font-size:10px;letter-spacing:.12em;color:var(--muted);font-weight:800;text-transform:uppercase}.value{font-size:24px;font-weight:800;margin-top:5px}.small{font-size:12px;color:var(--muted)}
.progress-card{padding:14px 15px}.progress-head{display:flex;justify-content:space-between;gap:12px;align-items:baseline}.progress-name{font-weight:750}.percent{font-variant-numeric:tabular-nums;color:var(--text);font-weight:800}.bar{height:10px;background:#080c12;border:1px solid #1d2733;border-radius:999px;overflow:hidden;margin:9px 0 7px}.fill{height:100%;width:0;border-radius:999px;transition:width .45s ease;background:linear-gradient(90deg,var(--cyan),var(--blue))}.fill.stage{background:linear-gradient(90deg,var(--violet),var(--cyan))}.fill.exp{background:linear-gradient(90deg,var(--green),#b5f36d)}.progress-meta{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;gap:8px}.progress-meta b{color:var(--text)}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.metric{background:var(--panel);border:1px solid #202b38;border-radius:11px;padding:11px}.metric .n{font-size:19px;font-weight:800;font-variant-numeric:tabular-nums}.metric .k{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}
.roadmap{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}.stage{padding:10px;border:1px solid var(--line);border-radius:10px;background:#0a0f16;min-height:66px}.stage.active{border-color:#3b8192;background:#0c1920}.stage.done{border-color:#326b49}.stage-num{font-size:10px;color:var(--muted);font-weight:800}.stage-name{font-size:12px;font-weight:750;margin-top:5px}.stage-state{font-size:10px;color:var(--muted);margin-top:4px}
.log{height:390px;overflow:auto;background:#070b10;border:1px solid #202b38;border-radius:10px;padding:9px;font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}.log-row{display:grid;grid-template-columns:78px 150px 1fr;gap:10px;padding:4px 5px;border-bottom:1px solid rgba(38,50,65,.45)}.log-row:last-child{border-bottom:0}.ts{color:#66778d}.kind{color:var(--cyan);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.msg{color:#d5dde8;word-break:break-word}.sev-error .kind{color:var(--red)}.sev-warning .kind{color:var(--amber)}.sev-complete .kind{color:var(--green)}
.kv{display:grid;grid-template-columns:150px 1fr;gap:7px;font-size:12px}.kv span:nth-child(odd){color:var(--muted)}.kv span:nth-child(even){font-weight:700;text-align:right;overflow:hidden;text-overflow:ellipsis}.controls{display:flex;gap:8px;flex-wrap:wrap}.btn{border:1px solid var(--line);background:#111925;color:var(--text);border-radius:9px;padding:8px 11px;font-weight:750;font-size:12px;cursor:pointer}.btn:hover{border-color:#4d637a;background:#172130}.btn.stop{border-color:#71323c;color:#ff9aa3}.notice{padding:9px 11px;border-radius:9px;background:#0b121a;border:1px solid #202b38;color:var(--muted);font-size:11px;margin-top:10px}.notice strong{color:var(--text)}
@media(max-width:1000px){.span8,.span6,.span4{grid-column:span 12}.span3{grid-column:span 6}.metrics{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){body{padding:10px}.top{flex-direction:column}.span3{grid-column:span 12}.roadmap{grid-template-columns:1fr 1fr}.log-row{grid-template-columns:65px 110px 1fr}.log{height:330px}}
</style>
</head>
<body>
<div class="shell">
  <header class="top">
    <div><div class="eyebrow">AUTONOMOUS RESEARCH CONTROL PLANE</div><div class="title">Advanced AI Trader</div><div class="sub">Live research telemetry — no market execution is enabled by this dashboard.</div></div>
    <div class="status"><span id="dot" class="dot"></span><span id="connection">CONNECTING</span><span id="updated">—</span></div>
  </header>

  <section class="grid">
    <div class="card span12">
      <div class="label">Three independent progress meters</div>
      <div class="grid" style="margin-top:10px">
        <div class="card progress-card span4"><div class="progress-head"><span class="progress-name">1 · Research program</span><span id="programPct" class="percent">0.0%</span></div><div class="bar"><div id="programBar" class="fill"></div></div><div class="progress-meta"><span>Weighted across all research phases</span><b id="programMeta">Stage 1/4</b></div></div>
        <div class="card progress-card span4"><div class="progress-head"><span class="progress-name">2 · Current stage</span><span id="stagePct" class="percent">0.0%</span></div><div class="bar"><div id="stageBar" class="fill stage"></div></div><div class="progress-meta"><span id="stageName">Benchmark Research</span><b id="stageEta">ETA —</b></div></div>
        <div class="card progress-card span4"><div class="progress-head"><span class="progress-name">3 · Current experiment</span><span id="expPct" class="percent">0.0%</span></div><div class="bar"><div id="expBar" class="fill exp"></div></div><div class="progress-meta"><span id="expMeta">Epoch 0/0</span><b id="dataMeta">Data 0/0</b></div></div>
      </div>
      <div class="roadmap" id="roadmap"></div>
    </div>

    <div class="card span8"><div class="label">Runtime & training state</div><div class="metrics" style="margin-top:10px">
      <div class="metric"><div class="k">Runtime</div><div id="runtime" class="n">00:00:00</div></div>
      <div class="metric"><div class="k">Stage ETA</div><div id="eta" class="n">—</div></div>
      <div class="metric"><div class="k">Epoch</div><div id="epoch" class="n">0 / 0</div></div>
      <div class="metric"><div class="k">Validation loss</div><div id="loss" class="n">—</div></div>
    </div><div class="notice"><strong id="state">STARTING</strong> · <span id="message">Waiting for telemetry…</span></div></div>

    <div class="card span4"><div class="label">System resources</div><div class="kv" style="margin-top:11px">
      <span>CPU process</span><span id="cpu">—</span><span>RAM system</span><span id="ram">—</span><span>Process memory</span><span id="rss">—</span><span>System load</span><span id="load">—</span><span>Training speed</span><span id="speed">—</span>
    </div></div>

    <div class="card span4"><div class="label">Research context</div><div class="kv" style="margin-top:11px">
      <span>Model</span><span id="model">—</span><span>Dataset</span><span id="dataset">—</span><span>Data source</span><span id="dataSource">—</span><span>Latent points</span><span id="latent">0</span><span>Guardian</span><span id="guardian">—</span>
    </div></div>

    <div class="card span8"><div class="label">Live event stream — every event returned by the research API</div><div id="log" class="log" style="margin-top:10px"></div></div>

    <div class="card span12"><div class="label">Operator controls</div><div class="controls" style="margin-top:10px"><button class="btn" onclick="control('start')">Start research</button><button class="btn stop" onclick="control('stop')">Stop research</button><button class="btn" onclick="refresh(true)">Refresh now</button></div><div class="notice">Research is currently benchmark/local-data only. Live trading remains disabled. The dashboard polls automatically; no Enter key or manual refresh is required.</div></div>
  </section>
</div>
<script>
const phaseNames=['Benchmark Research','Historical Training','Walk-Forward Research','Stress & Robustness'];
const $=id=>document.getElementById(id);let lastLogKey='';let firstLogs=true;let timer=null;
function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function pct(v){return Math.max(0,Math.min(100,Number(v)||0));}
function dur(sec){if(sec==null||!isFinite(sec))return '—';sec=Math.max(0,Math.round(sec));let d=Math.floor(sec/86400);sec%=86400;let h=Math.floor(sec/3600);sec%=3600;let m=Math.floor(sec/60),s=sec%60;return d?`${d}d ${String(h).padStart(2,'0')}h`: `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;}
function stageEta(state){const p=pct(state.progress);const started=Date.parse(state.started_at||'');if(p<=0||p>=100||!started)return null;const elapsed=(Date.now()-started)/1000;return elapsed*(100-p)/p;}
function setBar(id,value){$(id).style.width=pct(value)+'%';$(id.replace('Bar','Pct')).textContent=pct(value).toFixed(1)+'%';}
function renderRoadmap(state){let idx=Number(state.program_stage_index||1);$('roadmap').innerHTML=phaseNames.map((name,i)=>{let n=i+1;let cls=n<idx?'stage done':n===idx?'stage active':'stage';let st=n<idx?'COMPLETE':n===idx?String(state.status||'ACTIVE').toUpperCase():'QUEUED';return `<div class="${cls}"><div class="stage-num">STAGE ${n}</div><div class="stage-name">${esc(name)}</div><div class="stage-state">${st}</div></div>`}).join('');}
function renderStatus(s){setBar('programBar',s.research_progress);setBar('stageBar',s.progress);const exp=s.epoch&&s.epochs?Number(s.epoch)/Number(s.epochs)*100:0;setBar('expBar',exp);$('programMeta').textContent=`Stage ${s.program_stage_index||1}/${s.program_stage_count||4}`;$('stageName').textContent=s.program_stage_name||'—';const eta=stageEta(s);$('stageEta').textContent='ETA '+dur(eta);$('eta').textContent=dur(eta);$('runtime').textContent=dur(s.started_at?(Date.now()-Date.parse(s.started_at))/1000:null);$('epoch').textContent=`${s.epoch||0} / ${s.epochs||0}`;$('expMeta').textContent=`Epoch ${s.epoch||0}/${s.epochs||0}`;$('dataMeta').textContent=`Data ${Number(s.samples_processed||0).toLocaleString()}/${Number(s.total_samples||3200).toLocaleString()}`;$('loss').textContent=s.validation_loss==null?'—':Number(s.validation_loss).toFixed(5);$('state').textContent=String(s.status||'unknown').toUpperCase();$('message').textContent=s.message||'—';$('model').textContent=s.model_id||'—';$('dataset').textContent=s.dataset||'—';$('dataSource').textContent=s.market_training?'external market feed':'synthetic/local benchmark';$('latent').textContent=Number(s.latent_points||0).toLocaleString();$('guardian').textContent=s.power_guard?.active?'ACTIVE':'OFF';renderRoadmap(s);}
function renderResources(r){$('cpu').textContent=r.process_cpu_percent==null?'—':Number(r.process_cpu_percent).toFixed(1)+'%';$('ram').textContent=r.ram_used_mb==null?'—':`${Number(r.ram_used_mb).toFixed(0)} / ${Number(r.ram_total_mb).toFixed(0)} MB (${Number(r.ram_percent||0).toFixed(1)}%)`;$('rss').textContent=r.rss_mb==null?'—':Number(r.rss_mb).toFixed(1)+' MB';$('load').textContent=r.load_1m==null?'—':Number(r.load_1m).toFixed(2);$('speed').textContent=r.training_speed==null?'—':Number(r.training_speed).toFixed(1)+'/s';}
function renderLogs(events){const rows=events.slice().reverse();$('log').innerHTML=rows.map(e=>{const type=String(e.type||'event');let sev=type.includes('error')?'sev-error':type.includes('warning')?'sev-warning':type.includes('complete')||type.includes('started')?'sev-complete':'';const ts=e.timestamp?new Date(e.timestamp).toLocaleTimeString():'—';const kind=e.data_kind?`DATA/${e.data_kind}`:type;let detail=Object.entries(e).filter(([k])=>!['timestamp','type','message','data_kind'].includes(k)).map(([k,v])=>`${k}=${typeof v==='object'?JSON.stringify(v):v}`).join(' ');return `<div class="log-row ${sev}"><span class="ts">${esc(ts)}</span><span class="kind">${esc(kind)}</span><span class="msg">${esc(e.message||'')}${detail?' · '+esc(detail):''}</span></div>`}).join('')||'<div class="small">Waiting for first event…</div>';if(firstLogs){$('log').scrollTop=$('log').scrollHeight;firstLogs=false;}}
async function json(url,opts){const r=await fetch(url,opts);if(!r.ok)throw new Error(`${r.status} ${r.statusText}`);return r.json();}
async function refresh(force=false){try{const [s,r,e]=await Promise.all([json('/api/v1/research/status'),json('/api/v1/research/resources'),json('/api/v1/research/events?limit=500')]);renderStatus(s);renderResources({...r,training_speed:s.training_speed});renderLogs(e);$('connection').textContent='LIVE';$('dot').className='dot live';$('updated').textContent=new Date().toLocaleTimeString();}catch(err){$('connection').textContent='OFFLINE';$('dot').className='dot bad';$('message').textContent=err.message;}}
async function control(action){try{await json(`/api/v1/research/control?action=${action}`,{method:'POST'});await refresh(true);}catch(err){$('message').textContent=`Control failed: ${err.message}`;}}
refresh(true);timer=setInterval(()=>refresh(false),750);window.addEventListener('beforeunload',()=>clearInterval(timer));
</script>
</body>
</html>'''
