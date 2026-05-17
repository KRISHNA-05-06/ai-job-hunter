
let apps=[], filter='all', search='';
const TKEY='jh_targets';

function loadTargets(){try{return JSON.parse(localStorage.getItem(TKEY)||'{"d":30,"w":200}');}catch{return{d:5,w:25};}}
function saveTarget(){const d=+document.getElementById('dTarget').value||5,w=+document.getElementById('wTarget').value||25;localStorage.setItem(TKEY,JSON.stringify({d,w}));updateTarget();}

function init(){
  const t=loadTargets();
  document.getElementById('dTarget').value=t.d;
  document.getElementById('wTarget').value=t.w;
  document.getElementById('f_date').value=new Date().toISOString().split('T')[0];

  // Load from chrome storage
  if(typeof chrome!=='undefined'&&chrome.storage){
    chrome.storage.local.get(['applications'],(r)=>{
      apps=r.applications||[];
      render();
    });
  } else {
    // Fallback to localStorage for standalone use
    try{apps=JSON.parse(localStorage.getItem('jh_apps')||'[]');}catch{apps=[];}
    render();
  }
}

function saveToStorage(){
  if(typeof chrome!=='undefined'&&chrome.storage){
    chrome.storage.local.set({applications:apps});
  } else {
    localStorage.setItem('jh_apps',JSON.stringify(apps));
  }
}

function render(){renderStats();updateTarget();renderCallbacks();renderApps();renderCharts();}

function todayStr(){return new Date().toISOString().split('T')[0];}
function todayCount(){return apps.filter(a=>a.date===todayStr()).length;}
function weekCount(){
  const now=new Date(),mon=new Date(now);
  mon.setDate(now.getDate()-now.getDay()+1);mon.setHours(0,0,0,0);
  return apps.filter(a=>new Date(a.date)>=mon).length;
}

function renderStats(){
  const total=apps.length,intr=apps.filter(a=>a.status==='interview').length;
  const offer=apps.filter(a=>a.status==='offer').length;
  const rate=total>0?Math.round((intr+offer)/total*100):0;
  const sc=[
    {n:total,l:'Total Applied',c:'var(--accent)'},
    {n:todayCount(),l:'Today',c:'var(--green)'},
    {n:weekCount(),l:'This Week',c:'var(--blue)'},
    {n:intr,l:'Interviews',c:'var(--yellow)'},
    {n:offer,l:'Offers 🎉',c:'var(--green)'},
    {n:rate+'%',l:'Response Rate',c:'var(--accent2)'},
  ];
  document.getElementById('statsBar').innerHTML=sc.map(s=>`
    <div class="stat-card" style="--c:${s.c}">
      <div class="stat-num">${s.n}</div>
      <div class="stat-label">${s.l}</div>
    </div>`).join('');
}

function updateTarget(){
  const t=loadTargets(),today=todayCount(),pct=Math.min(100,Math.round(today/t.d*100));
  document.getElementById('tFill').style.width=pct+'%';
  document.getElementById('tText').textContent=`${today} / ${t.d} today`;
}

function renderCallbacks(){
  const intr=apps.filter(a=>a.status==='interview');
  const el=document.getElementById('cbAlert'),list=document.getElementById('cbList');
  if(!intr.length){el.classList.remove('show');return;}
  el.classList.add('show');
  list.innerHTML=intr.map(a=>`
    <div class="cbi">
      <strong style="color:var(--text)">${a.title}</strong> @ ${a.company}
      · Applied: ${a.date} · Resume: <span style="color:var(--blue)">${a.resume||'not specified'}</span>
      ${a.url?`· <a href="${a.url}" target="_blank" style="color:var(--accent)">View Job →</a>`:''}
      ${a.notes?`<br><span style="color:var(--muted);font-size:11px">${a.notes.substring(0,100)}</span>`:''}
    </div>`).join('');
}

function getFiltered(){
  let f=apps.slice();
  if(filter!=='all') f=f.filter(a=>a.status===filter);
  if(search){const q=search.toLowerCase();f=f.filter(a=>(a.title+a.company+(a.notes||'')).toLowerCase().includes(q));}
  return f.sort((a,b)=>new Date(b.date)-new Date(a.date));
}

const SL={applied:'Applied',interview:'Interview 📞',offer:'Offer 🎉',rejected:'Rejected',ghosted:'Ghosted',withdrawn:'Withdrawn'};
const PC={LinkedIn:'#0077B5',Indeed:'#2164F3',Glassdoor:'#0CAA41',Dice:'#EB1C26',Handshake:'#E8543A',JobRight:'#7C3AED'};

function renderApps(){
  const f=getFiltered();
  document.getElementById('listTitle').textContent=`${filter==='all'?'All':cap(filter)} Applications (${f.length})`;
  const list=document.getElementById('appsList');
  if(!f.length){list.innerHTML=`<div class="empty-state">${apps.length?'No results.':'No applications yet. Click "+ Log Application" to start!'}</div>`;return;}
  list.innerHTML=f.map(a=>`
    <div class="ac" id="ac-${a.id}" onclick="toggleCard('${a.id}')">
      <div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <span class="atitle">${a.title}</span>
          <span class="sb s-${a.status}">${SL[a.status]||a.status}</span>
        </div>
        <div class="acomp">🏢 ${a.company}${a.location?' · 📍'+a.location:''}</div>
        <div class="ameta">
          <span class="db">📅 ${fmtDate(a.date)}</span>
          <span class="pb" style="background:${PC[a.platform]||'#475569'}22;color:${PC[a.platform]||'#94a3b8'}">${a.platform}</span>
          ${a.resume?`<span class="rb">📄 ${a.resume}</span>`:''}
        </div>
        <div class="adetail" id="ad-${a.id}">
          ${a.url?`<div class="di"><label>Job Link</label><a href="${a.url}" target="_blank" onclick="event.stopPropagation()">View Posting →</a></div>`:''}
          <div class="di"><label>Applied</label><span>${fmtDate(a.date)}</span></div>
          <div class="di"><label>Platform</label><span>${a.platform}</span></div>
          <div class="di"><label>Resume Sent</label><span>${a.resume||'Not specified'}</span></div>
          ${a.notes?`<div class="di full"><label>Notes</label><span style="white-space:pre-wrap;font-size:12px">${a.notes}</span></div>`:''}
          ${a.description?`<div class="di full"><label>Job Description</label><span class="desc">${a.description}</span></div>`:''}
        </div>
      </div>
      <div class="aa" onclick="event.stopPropagation()">
        <select class="ss" onchange="updateStatus('${a.id}',this.value)">
          ${['applied','interview','offer','rejected','ghosted','withdrawn'].map(s=>`<option value="${s}"${a.status===s?' selected':''}>${cap(s)}</option>`).join('')}
        </select>
        <button class="bd" onclick="delApp('${a.id}')">🗑</button>
      </div>
    </div>`).join('');
}

function renderCharts(){
  if(!apps.length)return;
  const g=document.getElementById('chartsGrid');
  const sc={applied:0,interview:0,offer:0,rejected:0,ghosted:0,withdrawn:0};
  apps.forEach(a=>{if(sc[a.status]!==undefined)sc[a.status]++;});
  const maxS=Math.max(...Object.values(sc),1);
  const sColors={applied:'var(--accent)',interview:'var(--yellow)',offer:'var(--green)',rejected:'var(--red)',ghosted:'var(--muted)',withdrawn:'var(--accent2)'};

  const pc={};apps.forEach(a=>{pc[a.platform]=(pc[a.platform]||0)+1;});
  const maxP=Math.max(...Object.values(pc),1);
  const pClrs=['var(--accent)','var(--green)','var(--yellow)','var(--blue)','var(--accent2)','var(--red)'];

  const days=[];
  for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const s=d.toISOString().split('T')[0];days.push({l:['Su','Mo','Tu','We','Th','Fr','Sa'][d.getDay()],c:apps.filter(a=>a.date===s).length});}
  const maxD=Math.max(...days.map(d=>d.c),1);
  const t=loadTargets();

  g.innerHTML=`
    <div class="cc"><div class="ct">Status Breakdown</div><div class="bar-chart">
      ${Object.entries(sc).map(([s,c])=>`<div class="bar-row"><div class="bar-key">${cap(s)}</div><div class="bar-bg"><div class="bar-fill" style="width:${c/maxS*100}%;background:${sColors[s]}"></div></div><div class="bar-val">${c}</div></div>`).join('')}
    </div></div>
    <div class="cc"><div class="ct">By Platform</div><div class="bar-chart">
      ${Object.entries(pc).sort((a,b)=>b[1]-a[1]).map(([p,c],i)=>`<div class="bar-row"><div class="bar-key">${p}</div><div class="bar-bg"><div class="bar-fill" style="width:${c/maxP*100}%;background:${pClrs[i%pClrs.length]}"></div></div><div class="bar-val">${c}</div></div>`).join('')}
    </div></div>
    <div class="cc"><div class="ct">Last 7 Days</div>
      <div class="week-grid">${days.map(d=>`<div class="wd"><div class="wdl">${d.l}</div><div class="wdb"><div class="wdf" style="height:${d.c/maxD*100}%;${d.c>=t.d?'background:var(--green)':''}"></div></div><div class="wdn">${d.c}</div></div>`).join('')}</div>
      <div style="margin-top:10px;font-size:11px;color:var(--muted)">🟢 Green = hit daily target (${t.d}/day)</div>
    </div>
    <div class="cc"><div class="ct">Weekly Progress</div>
      <div style="text-align:center;padding:16px 0">
        <div style="font-family:'DM Serif Display',serif;font-size:44px">${weekCount()}</div>
        <div style="color:var(--muted);font-size:13px;margin-bottom:14px">of ${t.w} weekly target</div>
        <div style="background:var(--border);border-radius:99px;height:9px;overflow:hidden">
          <div style="width:${Math.min(100,Math.round(weekCount()/t.w*100))}%;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),var(--green));transition:width .5s"></div>
        </div>
        <div style="color:var(--muted);font-size:12px;margin-top:6px">${Math.min(100,Math.round(weekCount()/t.w*100))}% of weekly goal</div>
      </div>
    </div>`;
}

function toggleForm(){
  const f=document.getElementById('addForm');
  f.classList.toggle('open');
  if(f.classList.contains('open')){document.getElementById('f_date').value=todayStr();document.getElementById('f_title').focus();}
}

function saveApp(){
  const title=document.getElementById('f_title').value.trim();
  const company=document.getElementById('f_company').value.trim();
  if(!title||!company){alert('Please fill in Job Title and Company.');return;}
  const a={
    id:Date.now().toString(),title,company,
    location:document.getElementById('f_location').value.trim(),
    platform:document.getElementById('f_platform').value,
    date:document.getElementById('f_date').value||todayStr(),
    resume:document.getElementById('f_resume').value.trim(),
    url:document.getElementById('f_url').value.trim(),
    status:document.getElementById('f_status').value,
    notes:document.getElementById('f_notes').value.trim(),
    description:document.getElementById('f_desc').value.trim(),
  };
  apps.unshift(a);saveToStorage();
  ['f_title','f_company','f_location','f_resume','f_url','f_notes','f_desc'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('f_status').value='applied';
  document.getElementById('addForm').classList.remove('open');
  render();
}

function updateStatus(id,status){const a=apps.find(x=>x.id===id);if(a){a.status=status;saveToStorage();render();}}
function delApp(id){if(!confirm('Delete?'))return;apps=apps.filter(a=>a.id!==id);saveToStorage();render();}
function toggleCard(id){document.getElementById('ac-'+id).classList.toggle('exp');}
function setFilter(f,btn){filter=f;document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));btn.classList.add('active');renderApps();}
function setSearch(q){search=q;renderApps();}
function switchTab(t,btn){document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));btn.classList.add('active');document.getElementById('tab-apps').style.display=t==='apps'?'block':'none';document.getElementById('tab-charts').style.display=t==='charts'?'block':'none';if(t==='charts')renderCharts();}
function fmtDate(d){if(!d)return'—';return new Date(d+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});}
function cap(s){return s.charAt(0).toUpperCase()+s.slice(1);}

init();


// ── GitHub Sync for email_updates.json ─────────────────────
// Replace YOUR_USERNAME and YOUR_REPO with your actual GitHub details
const GITHUB_JSON_URL = 'https://raw.githubusercontent.com/KRISHNA-05-06/ai-job-hunter/main/data/email_updates.json';

async function syncFromGitHub() {
  document.getElementById('lastSynced').textContent = 'Syncing...';
  try {
    const resp = await fetch(GITHUB_JSON_URL + '?t=' + Date.now());
    if (!resp.ok) throw new Error('Not found');
    const data = await resp.json();
    renderHeardBack(data);
    document.getElementById('lastSynced').textContent = 'Synced ' + new Date().toLocaleTimeString();

    // Save to storage for offline use
    if (typeof chrome !== 'undefined' && chrome.storage) {
      chrome.storage.local.set({ emailUpdates: data });
    }
  } catch(e) {
    document.getElementById('lastSynced').textContent = 'Sync failed — check GitHub URL';
    // Try loading from storage
    if (typeof chrome !== 'undefined' && chrome.storage) {
      chrome.storage.local.get(['emailUpdates'], (r) => {
        if (r.emailUpdates) renderHeardBack(r.emailUpdates);
      });
    }
  }
}

function renderHeardBack(data) {
  const heard = data.heard_back || [];
  const section = document.getElementById('heardBackSection');
  const list = document.getElementById('heardBackList');
  const badge = document.getElementById('heardBackBadge');

  if (!heard.length) { section.style.display = 'none'; return; }

  section.style.display = 'block';
  badge.textContent = heard.length + ' response' + (heard.length > 1 ? 's' : '');

  const catMeta = {
    interview: { color: 'var(--yellow)', bg: '#ffd16622', emoji: '📞', label: 'Interview' },
    offer:     { color: 'var(--green)',  bg: '#00d4a022', emoji: '🎉', label: 'Offer' },
    rejection: { color: 'var(--red)',    bg: '#ff6b6b22', emoji: '❌', label: 'Rejected' },
    followup:  { color: 'var(--blue)',   bg: '#4ecdc422', emoji: '💬', label: 'Follow-up' },
  };

  list.innerHTML = heard.map(item => {
    const m = catMeta[item.category] || { color: 'var(--muted)', bg: '#6b6b8a22', emoji: '📧', label: item.category };
    return `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
          <span style="font-size:16px">${m.emoji}</span>
          <span style="background:${m.bg};color:${m.color};padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;text-transform:uppercase">${m.label}</span>
          <strong style="font-size:14px;color:var(--text)">${item.company}</strong>
          <span style="color:var(--muted);font-size:12px">· ${item.platform}</span>
          <span style="margin-left:auto;font-size:11px;color:var(--muted);font-family:'DM Mono',monospace">${item.date ? item.date.substring(0,16) : ''}</span>
        </div>
        <div style="font-size:12px;color:var(--text);margin-bottom:4px">${item.job_title}</div>
        <div style="font-size:11px;color:var(--muted);font-style:italic;margin-bottom:6px">Subject: ${item.subject ? item.subject.substring(0,80) : ''}</div>
        <div style="font-size:11px;color:var(--muted);background:var(--surface2);border-radius:6px;padding:8px;line-height:1.5">
          ${item.body_preview ? item.body_preview.substring(0,200) + '...' : ''}
        </div>
      </div>`;
  }).join('');
}

// Auto-sync on page load
syncFromGitHub();
// Re-sync every 30 minutes
setInterval(syncFromGitHub, 30 * 60 * 1000);



// ── Attach all event listeners (no inline onclick allowed in extensions) ──
document.addEventListener('DOMContentLoaded', () => {

  // + Log Application button
  const btnToggle = document.getElementById('btnToggleForm');
  if (btnToggle) btnToggle.addEventListener('click', toggleForm);

  // Save button
  const btnSave = document.getElementById('btnSaveApp');
  if (btnSave) btnSave.addEventListener('click', saveApp);

  // Cancel button
  const btnCancel = document.getElementById('btnCancelForm');
  if (btnCancel) btnCancel.addEventListener('click', toggleForm);

  // Search input
  const searchInp = document.getElementById('searchInp');
  if (searchInp) searchInp.addEventListener('input', (e) => setSearch(e.target.value));

  // Target inputs
  const dTarget = document.getElementById('dTarget');
  const wTarget = document.getElementById('wTarget');
  if (dTarget) dTarget.addEventListener('change', saveTarget);
  if (wTarget) wTarget.addEventListener('change', saveTarget);

  // Filter buttons (data-filter attribute)
  document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      setFilter(btn.dataset.filter, btn);
    });
  });

  // Tab buttons (data-tab attribute)
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      switchTab(btn.dataset.tab, btn);
    });
  });

  // Sync button
  const syncBtn = document.getElementById('syncBtn');
  if (syncBtn) syncBtn.addEventListener('click', syncFromGitHub);
});
