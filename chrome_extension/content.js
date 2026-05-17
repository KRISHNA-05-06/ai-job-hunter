/**
 * content.js — runs on every job page
 * Detects apply button clicks, extracts job details, shows resume picker popup
 */

(function() {
  'use strict';

  // Avoid double injection
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

  // ── Job detail extractors per platform ─────────────────
  function extractJobDetails() {
    const platform = getPlatform();
    let title = '', company = '', location = '', description = '';

    if (platform === 'LinkedIn') {
      title       = text('.job-details-jobs-unified-top-card__job-title h1') ||
                    text('.jobs-unified-top-card__job-title') ||
                    text('h1.t-24');
      company     = text('.job-details-jobs-unified-top-card__company-name a') ||
                    text('.jobs-unified-top-card__company-name');
      location    = text('.job-details-jobs-unified-top-card__bullet') ||
                    text('.jobs-unified-top-card__workplace-type');
      description = text('.jobs-description__content') ||
                    text('.jobs-box__html-content');

    } else if (platform === 'Indeed') {
      title       = text('[data-testid="jobsearch-JobInfoHeader-title"] span') ||
                    text('.jobsearch-JobInfoHeader-title');
      company     = text('[data-testid="inlineHeader-companyName"] a') ||
                    text('.jobsearch-CompanyInfoContainer a');
      location    = text('[data-testid="job-location"]') ||
                    text('.jobsearch-JobInfoHeader-subtitle span');
      description = text('#jobDescriptionText') ||
                    text('.jobsearch-jobDescriptionText');

    } else if (platform === 'Glassdoor') {
      title       = text('[data-test="job-title"]') ||
                    text('.job-title');
      company     = text('[data-test="employer-name"]') ||
                    text('.employer-name');
      location    = text('[data-test="emp-location"]');
      description = text('.jobDescriptionContent') ||
                    text('[class*="JobDetails_jobDescription"]');

    } else if (platform === 'Dice') {
      title       = text('h1[data-cy="jobTitle"]') || text('h1.jobTitle');
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

    // Fallback to page title
    if (!title) title = document.title.split('|')[0].split('-')[0].trim();

    return {
      title:       title.trim(),
      company:     company.trim(),
      location:    location.trim(),
      description: description.trim().substring(0, 2000),
      platform:    platform,
      url:         window.location.href,
      date:        new Date().toISOString().split('T')[0],
    };
  }

  function text(selector) {
    const el = document.querySelector(selector);
    return el ? el.innerText.trim() : '';
  }

  // ── Apply button selectors ──────────────────────────────
  const APPLY_SELECTORS = [
    // LinkedIn
    'button.jobs-apply-button',
    'button[aria-label*="Easy Apply"]',
    'button[aria-label*="Apply"]',
    'button.jobs-s-apply button',
    // Indeed
    'button#indeedApplyButton',
    'button[id*="apply"]',
    'a[id*="apply"]',
    // Glassdoor
    'button[data-test="apply-button"]',
    'a[data-test="apply-button"]',
    // Dice
    'a[data-cy="apply-button"]',
    'button[data-cy="apply-button"]',
    // Generic
    'button[class*="apply"i]',
    'a[class*="apply"i]',
    'button[data-automation*="apply"i]',
  ];

  // Submit button selectors (final step)
  const SUBMIT_SELECTORS = [
    'button[aria-label="Submit application"]',
    'button[data-easy-apply-next-button]',
    'button:not([disabled])[class*="submit"i]',
    'button:not([disabled])[aria-label*="Submit"i]',
    'footer button[aria-label*="Submit"i]',
  ];

  // ── Popup UI ────────────────────────────────────────────
  let popupEl = null;
  let currentJobDetails = null;

  function showPopup(jobDetails) {
    currentJobDetails = jobDetails;
    if (popupEl) popupEl.remove();

    // Get saved resumes
    chrome.storage.local.get(['resumes'], (result) => {
      const resumes = result.resumes || [
        'resume_v1_dataeng.pdf',
        'resume_v2_spark.pdf',
        'resume_v3_aws.pdf',
      ];

      popupEl = document.createElement('div');
      popupEl.id = 'jh-popup';
      popupEl.innerHTML = `
        <div id="jh-popup-inner">
          <div id="jh-header">
            <span id="jh-logo">🎯</span>
            <span id="jh-title">Job Hunter</span>
            <button id="jh-close">✕</button>
          </div>
          <div id="jh-job-info">
            <div id="jh-job-title">${jobDetails.title || 'Unknown Role'}</div>
            <div id="jh-job-company">${jobDetails.company || 'Unknown Company'} · ${jobDetails.platform}</div>
          </div>
          <div id="jh-field">
            <label>Which resume did you send?</label>
            <select id="jh-resume-select">
              ${resumes.map(r => `<option value="${r}">${r}</option>`).join('')}
              <option value="__custom__">+ Add new...</option>
            </select>
            <input type="text" id="jh-custom-resume" placeholder="Enter resume filename..." style="display:none;margin-top:6px">
          </div>
          <div id="jh-field">
            <label>Notes (optional)</label>
            <textarea id="jh-notes" placeholder="Recruiter name, cover letter sent, anything useful..."></textarea>
          </div>
          <div id="jh-actions">
            <button id="jh-save">✅ Log Application</button>
            <button id="jh-skip">Skip</button>
          </div>
          <div id="jh-status" style="display:none"></div>
        </div>
      `;

      document.body.appendChild(popupEl);

      // Events
      document.getElementById('jh-close').onclick = () => popupEl.remove();
      document.getElementById('jh-skip').onclick  = () => popupEl.remove();
      document.getElementById('jh-save').onclick  = saveApplication;

      document.getElementById('jh-resume-select').onchange = function() {
        const custom = document.getElementById('jh-custom-resume');
        custom.style.display = this.value === '__custom__' ? 'block' : 'none';
        if (this.value === '__custom__') custom.focus();
      };

      // Draggable
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
      // Save new resume to list
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

    // Save to chrome storage
    chrome.storage.local.get(['applications'], (result) => {
      const applications = result.applications || [];
      applications.unshift(app);
      chrome.storage.local.set({ applications }, () => {
        const status = document.getElementById('jh-status');
        status.style.display = 'block';
        status.textContent   = '✅ Logged! Check your tracker dashboard.';
        setTimeout(() => popupEl && popupEl.remove(), 2000);
      });
    });
  }

  function makeDraggable(el, handle) {
    let x = 0, y = 0, mx = 0, my = 0;
    handle.style.cursor = 'move';
    handle.onmousedown = (e) => {
      e.preventDefault();
      mx = e.clientX; my = e.clientY;
      document.onmousemove = (e) => {
        x = mx - e.clientX; y = my - e.clientY;
        mx = e.clientX; my = e.clientY;
        el.style.top  = (el.offsetTop  - y) + 'px';
        el.style.left = (el.offsetLeft - x) + 'px';
        el.style.right = 'auto'; el.style.bottom = 'auto';
      };
      document.onmouseup = () => {
        document.onmousemove = null;
        document.onmouseup   = null;
      };
    };
  }

  // ── Button detection ────────────────────────────────────
  function attachApplyListeners() {
    const platform = getPlatform();

    // Watch for apply button clicks
    document.addEventListener('click', (e) => {
      const el = e.target.closest('button, a');
      if (!el) return;

      const isApply = APPLY_SELECTORS.some(sel => {
        try { return el.matches(sel); } catch { return false; }
      });

      const label = (el.getAttribute('aria-label') || el.innerText || '').toLowerCase();
      const isApplyText = label.includes('apply') || label.includes('easy apply');

      if (isApply || isApplyText) {
        // Small delay so page updates first
        setTimeout(() => {
          const details = extractJobDetails();
          if (details.title) {
            // For LinkedIn Easy Apply — show after submit button is clicked
            if (platform === 'LinkedIn' && label.includes('easy apply')) {
              watchForSubmit(details);
            } else {
              showPopup(details);
            }
          }
        }, 800);
      }
    }, true);
  }

  function watchForSubmit(jobDetails) {
    // Watch for final Submit click on LinkedIn multi-step form
    const observer = new MutationObserver(() => {
      SUBMIT_SELECTORS.forEach(sel => {
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
    // Auto-stop after 10 minutes
    setTimeout(() => observer.disconnect(), 600000);
  }

  // ── Init ────────────────────────────────────────────────
  attachApplyListeners();
  console.log('🎯 Job Hunter Tracker active on', getPlatform());

})();
