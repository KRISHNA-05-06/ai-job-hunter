const STATUS_COLORS = {
  applied:'dot-applied', interview:'dot-interview',
  offer:'dot-offer', rejected:'dot-rejected', ghosted:'dot-ghosted'
};

function init() {
  chrome.storage.local.get(['applications','resumes'], (result) => {
    const apps    = result.applications || [];
    const resumes = result.resumes || [];

    // Stats
    const statsEl = document.getElementById('statsContent');
    if (apps.length > 0) {
      const today  = new Date().toISOString().split('T')[0];
      const todayN = apps.filter(a => a.date === today).length;
      const intrN  = apps.filter(a => a.status === 'interview').length;
      const offerN = apps.filter(a => a.status === 'offer').length;
      statsEl.innerHTML = `
        <div class="stat-row"><span class="stat-label">Total Applied</span><span class="stat-val accent">${apps.length}</span></div>
        <div class="stat-row"><span class="stat-label">Applied Today</span><span class="stat-val green">${todayN}</span></div>
        <div class="stat-row"><span class="stat-label">Interviews</span><span class="stat-val yellow">${intrN}</span></div>
        <div class="stat-row"><span class="stat-label">Offers</span><span class="stat-val green">${offerN}</span></div>`;
    }

    // Recent apps
    const recentEl = document.getElementById('recentContent');
    if (apps.length > 0) {
      recentEl.innerHTML = apps.slice(0,5).map(a => `
        <div class="app-item">
          <div class="app-title">
            <span class="status-dot ${STATUS_COLORS[a.status]||'dot-applied'}"></span>
            ${a.title}
          </div>
          <div class="app-company">${a.company} · ${a.platform} · ${a.date}</div>
        </div>`).join('');
    }

    renderResumes(resumes);
  });
}

function renderResumes(resumes) {
  const list = document.getElementById('resumeList');
  if (!resumes.length) {
    list.innerHTML = '<div class="empty">No resumes added yet</div>';
    return;
  }
  list.innerHTML = resumes.map((r,i) => `
    <div class="resume-tag">
      <span>📄 ${r}</span>
      <button class="resume-del" data-index="${i}">✕</button>
    </div>`).join('');

  // Attach delete listeners
  list.querySelectorAll('.resume-del').forEach(btn => {
    btn.addEventListener('click', () => deleteResume(parseInt(btn.dataset.index)));
  });
}

function addResume() {
  const inp = document.getElementById('resumeInp');
  const val = inp.value.trim();
  if (!val) return;
  chrome.storage.local.get(['resumes'], (r) => {
    const resumes = r.resumes || [];
    if (!resumes.includes(val)) {
      resumes.push(val);
      chrome.storage.local.set({ resumes }, () => {
        renderResumes(resumes);
        inp.value = '';
      });
    }
  });
}

function deleteResume(index) {
  chrome.storage.local.get(['resumes'], (r) => {
    const resumes = r.resumes || [];
    resumes.splice(index, 1);
    chrome.storage.local.set({ resumes }, () => renderResumes(resumes));
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('openTracker').addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('tracker.html') });
  });

  document.getElementById('addResumeBtn').addEventListener('click', addResume);

  document.getElementById('resumeInp').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addResume();
  });

  init();
});
