/**
 * content.js — runs on every job page
 * Detects apply button clicks, extracts job details, shows resume picker popup
 */

(function() {
  'use strict';

  if (window.__jobHunterInjected) return;
  window.__jobHunterInjected = true;

  // ── Platform detection ──────────────────────────────────
  const PLATFORM_MAP = {
    'linkedin.com':      'LinkedIn',
    'indeed.com':        'Indeed',
    'glassdoor.com':     'Glassdoor',
    'dice.com':          'Dice',
    'joinhandshake.com': 'Handshake',
    'jobright.ai':       'JobRight',
  };

  function getPlatform() {
    const host = window.location.hostname;
    for (const [key, name] of Object.entries(PLATFORM_MAP)) {
      if (host.includes(key)) return name;
    }
    return 'Other';
  }

  // ── Job detail extractors ───────────────────────────────
  function extractJobDetails() {
    const platform = getPlatform();
    let title = '', company = '', location = '', description = '';

    if (platform === 'LinkedIn') {
      title       = text('.job-details-jobs-unified-top-card__job-title h1') ||
                    text('.jobs-unified-top-card__job-title') ||
                    text('h1.t-24') || text('h1');
      company     = text('.job-details-jobs-unified-top-card__company-name a') ||
                    text('.jobs-unified-top-card__company-name');
      location    = text('.job-details-jobs-unified-top-card__bullet') ||
                    text('.jobs-unified-top-card__workplace-type');
      description = text('.jobs-description__content') ||
                    text('.jobs-box__html-content');

    } else if (platform === 'Indeed') {
      title       = text('[data-testid="jobsearch-JobInfoHeader-title"] span') ||
                    text('.jobsearch-JobInfoHeader-title') ||
                    text('h1.jobsearch-JobInfoHeader-title') ||
                    text('h1');
      company     = text('[data-testid="inlineHeader-companyName"] a') ||
                    text('[data-testid="inlineHeader-companyName"]') ||
                    text('.jobsearch-CompanyInfoContainer a') ||
                    text('.jobsearch-InlineCompanyRating-companyHeader');
      location    = text('[data-testid="job-location"]') ||
                    text('[data-testid="inlineHeader-companyLocation"]') ||
                    text('.jobsearch-JobInfoHeader-subtitle span:last-child');
      description = text('#jobDescriptionText') ||
                    text('.jobsearch-jobDescriptionText') ||
                    text('[id*="jobDescription"]');

    } else if (platform === 'Glassdoor') {
      title       = text('[data-test="job-title"]') || text('h1');
      company     = text('[data-test="employer-name"]');
      location    = text('[data-test="emp-location"]');
      description = text('.jobDescriptionContent') ||
                    text('[class*="JobDetails_jobDescription"]');

    } else if (platform === 'Dice') {
      title       = text('h1[data-cy="jobTitle"]') || text('h1.jobTitle') || text('h1');
      company     = text('[data-cy="companyNameLink"]') || text('.company-name');
      location    = text('[data-cy="location"]') || text('.location');
      description = text('.job-description') || text('[data-cy="jobDescription"]');

    } else if (platform === 'Handshake') {
      title       = text('h1') || text('[class*="PostingTitle"]');
      company     = text('[class*="employer-name"]') || text('[class*="EmployerName"]');
      location    = text('[class*="location"]');
      description = text('[class*="job-description"]') || text('[class*="PostingBody"]');

    } else if (platform === 'JobRight') {
      title       = text('h1') || text('[class*="title"]');
      company     = text('[class*="company"]');
      location    = text('[class*="location"]');
      description = text('[class*="description"]') || text('[class*="detail"]');
    }

    if (!title) title = document.title.split('|')[0].split('-')[0].trim();

    return {
      title:       title.trim(),
      company:     company.trim(),
      location:    location.trim(),
      description: description.trim().substring(0, 2000),
      platform:    getPlatform(),
      url:         window.location.href,
      date:        new Date().toISOString().split('T')[0],
    };
  }

  function text(selector) {
    const el = document.querySelector(selector);
    return el ? el.innerText.trim() : '';
  }

  // ── Apply button text patterns ──────────────────────────
  const APPLY_TEXT_PATTERNS = [
    'apply now', 'easy apply', 'apply on company site',
    'apply for this job', 'indeedapply', 'apply',
    'submit application', 'submit your application',
  ];

  function isApplyButton(el) {
    if (!el) return false;
    const tag   = el.tagName.toLowerCase();
    const label = (
      el.getAttribute('aria-label') ||
      el.getAttribute('data-testid') ||
      el.innerText ||
      el.id || ''
    ).toLowerCase().trim();

    if (tag !== 'button' && tag !== 'a') return false;
    return APPLY_TEXT_PATTERNS.some(p => label.includes(p));
  }

  // ── Popup ───────────────────────────────────────────────
  let popupEl = null;
  let currentJobDetails = null;

  function showPopup(jobDetails) {
    currentJobDetails = jobDetails;
    if (popupEl) popupEl.remove();

    chrome.storage.local.get(['resumes'], (result) => {
      const resumes = result.resumes || [
        'resume_v1_general.pdf',
        'resume_v2_spark_aws.pdf',
      ];

      popupEl = document.createElement('div');
      popupEl.id = 'jh-popup';

      const resumeOptions = resumes.map(r =>
        `<option value="${r}">${r}</option>`
      ).join('') + '<option value="__custom__">+ Add new...</option>';

      popupEl.innerHTML = `
        <div id="jh-popup-inner">
          <div id="jh-header">
            <span id="jh-logo">🎯</span>
            <span id="jh-title">Job Hunter Tracker</span>
            <button id="jh-close" type="button">✕</button>
          </div>
          <div id="jh-job-info">
            <div id="jh-job-title">${jobDetails.title || 'Unknown Role'}</div>
            <div id="jh-job-company">${jobDetails.company || 'Unknown Company'} · ${jobDetails.platform}</div>
          </div>
          <div id="jh-field">
            <label>Which resume did you send?</label>
            <select id="jh-resume-select">${resumeOptions}</select>
            <input type="text" id="jh-custom-resume" placeholder="Enter resume filename..." style="display:none;margin-top:6px">
          </div>
          <div id="jh-field">
            <label>Notes (optional)</label>
            <textarea id="jh-notes" placeholder="Recruiter name, cover letter sent, anything useful..."></textarea>
          </div>
          <div id="jh-actions">
            <button id="jh-save" type="button">✅ Log Application</button>
            <button id="jh-skip" type="button">Skip</button>
          </div>
          <div id="jh-status" style="display:none"></div>
        </div>
      `;

      document.body.appendChild(popupEl);

      // Attach all events with addEventListener (no onclick attributes)
      document.getElementById('jh-close').addEventListener('click', () => popupEl.remove());
      document.getElementById('jh-skip').addEventListener('click',  () => popupEl.remove());
      document.getElementById('jh-save').addEventListener('click',  saveApplication);

      document.getElementById('jh-resume-select').addEventListener('change', function() {
        const custom = document.getElementById('jh-custom-resume');
        custom.style.display = this.value === '__custom__' ? 'block' : 'none';
        if (this.value === '__custom__') custom.focus();
      });

      makeDraggable(popupEl, document.getElementById('jh-header'));
    });
  }

  function saveApplication() {
    const resumeSelect = document.getElementById('jh-resume-select');
    const customResume = document.getElementById('jh-custom-resume');
    const notes        = document.getElementById('jh-notes').value.trim();

    let resume = resumeSelect.value;
    if (resume === '__custom__') {
      resume = customResume.value.trim();
      if (!resume) { alert('Please enter a resume filename.'); return; }
      chrome.storage.local.get(['resumes'], (r) => {
        const resumes = r.resumes || [];
        if (!resumes.includes(resume)) {
          resumes.push(resume);
          chrome.storage.local.set({ resumes });
        }
      });
    }

    const app = {
      id:          Date.now().toString(),
      ...currentJobDetails,
      resume,
      notes,
      status:      'applied',
      loggedAt:    new Date().toISOString(),
    };

    chrome.storage.local.get(['applications'], (result) => {
      const applications = result.applications || [];
      applications.unshift(app);
      chrome.storage.local.set({ applications }, () => {
        const status = document.getElementById('jh-status');
        status.style.display = 'block';
        status.textContent   = '✅ Logged! Check your tracker dashboard.';
        setTimeout(() => { if (popupEl) popupEl.remove(); }, 2000);
      });
    });
  }

  function makeDraggable(el, handle) {
    let x = 0, y = 0, mx = 0, my = 0;
    handle.style.cursor = 'move';
    handle.addEventListener('mousedown', (e) => {
      e.preventDefault();
      mx = e.clientX; my = e.clientY;
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup',   onUp);
    });
    function onMove(e) {
      x = mx - e.clientX; y = my - e.clientY;
      mx = e.clientX; my = e.clientY;
      el.style.top    = (el.offsetTop  - y) + 'px';
      el.style.left   = (el.offsetLeft - x) + 'px';
      el.style.right  = 'auto';
      el.style.bottom = 'auto';
    }
    function onUp() {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup',   onUp);
    }
  }

  // ── Indeed specific: watch for apply modal ──────────────
  function watchIndeedApplyModal() {
    const observer = new MutationObserver(() => {
      // Indeed apply modal appears with this selector
      const modal = document.querySelector(
        '[id*="apply-modal"], [class*="ApplyModal"], #indeedApplyModal, [data-testid*="apply"]'
      );
      if (modal && !modal.__jhWatched) {
        modal.__jhWatched = true;
        // Watch for submit inside the modal
        const submitObserver = new MutationObserver(() => {
          const submitBtn = modal.querySelector(
            'button[type="submit"], button[data-testid*="submit"], button[aria-label*="Submit"]'
          );
          if (submitBtn && !submitBtn.__jhListened) {
            submitBtn.__jhListened = true;
            submitBtn.addEventListener('click', () => {
              setTimeout(() => showPopup(extractJobDetails()), 2000);
            });
          }
        });
        submitObserver.observe(modal, { childList: true, subtree: true });
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  // ── Global click listener ───────────────────────────────
  document.addEventListener('click', (e) => {
    const el = e.target.closest('button, a, [role="button"]');
    if (!el) return;

    if (isApplyButton(el)) {
      const platform = getPlatform();
      setTimeout(() => {
        const details = extractJobDetails();
        if (!details.title) return;

        if (platform === 'LinkedIn') {
          // LinkedIn Easy Apply — wait for submit step
          watchForLinkedInSubmit(details);
        } else {
          // For Indeed, Glassdoor, Dice etc — show popup after short delay
          // (gives time for any redirect/modal to load)
          setTimeout(() => showPopup(details), 1500);
        }
      }, 500);
    }
  }, true);

  function watchForLinkedInSubmit(jobDetails) {
    const SUBMIT_SELS = [
      'button[aria-label="Submit application"]',
      'button[aria-label*="Submit"]',
      'footer button:last-child',
    ];
    const observer = new MutationObserver(() => {
      SUBMIT_SELS.forEach(sel => {
        const btn = document.querySelector(sel);
        if (btn && !btn.__jhListened) {
          btn.__jhListened = true;
          btn.addEventListener('click', () => {
            setTimeout(() => showPopup(jobDetails), 1500);
          });
        }
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 600000);
  }

  // ── Also watch for URL changes (Indeed SPA navigation) ──
  let lastUrl = location.href;
  new MutationObserver(() => {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      // Re-init on page change
      window.__jobHunterInjected = false;
    }
  }).observe(document, { subtree: true, childList: true });

  // ── Init Indeed modal watcher ───────────────────────────
  if (getPlatform() === 'Indeed') {
    watchIndeedApplyModal();
  }

  console.log('🎯 Job Hunter Tracker active on', getPlatform());

})();
