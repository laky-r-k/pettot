/* PetTot prototype UI. Local owner data is kept in this browser; API image requests are explicit. */
(function () {
  'use strict';

  const KEYS = {
    profile: 'pettot.prototype.profile.v2',
    checkins: 'pettot.prototype.checkins.v2',
    medications: 'pettot.prototype.medications.v2',
    analyses: 'pettot.prototype.analyses.v2',
    apiBase: 'pettot.prototype.apiBase.v2',
    sessionEmail: 'pettot.prototype.sessionEmail.v2'
  };
  const DEFAULT_API = (window.location.protocol === 'http:' || window.location.protocol === 'https:') && window.location.port !== '5500' ? window.location.origin : 'http://127.0.0.1:8000';
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));

  // If a remote design photo is unavailable, keep the designed color/shape treatment.
  function wirePhotoFallbacks() {
    $$('.decorative-photo').forEach(image => {
      const useFallback = () => {
        image.parentElement?.classList.add('photo-fallback');
        image.remove();
      };
      if (image.complete && image.naturalWidth === 0) useFallback();
      else image.addEventListener('error', useFallback, { once: true });
    });
  }

  function read(key, fallback) {
    try {
      const value = localStorage.getItem(key);
      return value === null ? fallback : JSON.parse(value);
    } catch (error) {
      return fallback;
    }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch (error) { showToast('Could not save in this browser. Check storage settings or available space.'); }
  }
  function cleanText(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  }
  function localDateISO(date) {
    const d = date || new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function formatDate(dateString, options) {
    if (!dateString) return 'Not set';
    const d = new Date(dateString + 'T12:00:00');
    if (Number.isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString(undefined, options || { day: 'numeric', month: 'short', year: 'numeric' });
  }
  function formatMoment(iso) {
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleString(undefined, { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' });
  }
  function safeURLPhone(phone) { return String(phone || '').replace(/[^\d+]/g, ''); }
  function showToast(message) {
    const toast = $('#toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove('hidden');
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.add('hidden'), 3200);
  }
  function getRoute() {
    return (window.location.hash || '').replace(/^#\/?/, '').split('?')[0] || 'login';
  }

  const state = {
    profile: read(KEYS.profile, null),
    checkins: read(KEYS.checkins, []),
    medications: read(KEYS.medications, []),
    analyses: read(KEYS.analyses, []),
    apiBase: localStorage.getItem(KEYS.apiBase) || DEFAULT_API,
    sessionEmail: sessionStorage.getItem(KEYS.sessionEmail) || ''
  };

  function isActiveSession() { return sessionStorage.getItem(KEYS.sessionEmail) !== null; }
  function go(route) {
    const next = '#' + route;
    if (window.location.hash === next) renderRoute();
    else window.location.hash = next;
  }
  function pageTitle(route) {
    return ({ overview: "Today's overview", checkin: 'Daily check-in', photos: 'Photo review', care: 'Care & contacts' })[route] || 'Recovery space';
  }
  function renderRoute() {
    const requested = getRoute();
    const loggedIn = isActiveSession();
    let route = requested;
    if (!loggedIn) route = 'login';
    else if (!state.profile && route !== 'setup') route = 'setup';
    if (!['login', 'setup', 'overview', 'checkin', 'photos', 'care'].includes(route)) route = state.profile ? 'overview' : 'setup';

    $('#login-screen').classList.toggle('hidden', route !== 'login');
    $('#setup-screen').classList.toggle('hidden', route !== 'setup');
    $('#workspace').classList.toggle('hidden', !['overview', 'checkin', 'photos', 'care'].includes(route));
    $$('.page').forEach(page => page.classList.toggle('active', page.id === 'page-' + route));
    $$('.nav-link').forEach(link => {
      const active = link.dataset.route === route;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
    if (route !== requested) {
      if (window.location.hash !== '#' + route) window.history.replaceState(null, '', '#' + route);
    }
    $('#topbar-title').textContent = pageTitle(route);
    $('#topbar-pet').textContent = state.profile ? state.profile.petName : 'Pet profile not set';
    if (route === 'setup') fillSetupForm();
    if (route === 'overview') updateOverview();
    if (route === 'checkin') updateCheckinPage();
    if (route === 'photos') updatePhotosPage();
    if (route === 'care') updateCarePage();
  }

  function fillSetupForm() {
    const form = $('#setup-form');
    if (!form) return;
    const p = state.profile || {};
    const values = {
      petName: p.petName || '', species: p.species || '', breed: p.breed || '',
      procedure: p.procedure || '', surgeryDate: p.surgeryDate || '', clinic: p.clinic || '',
      vetName: p.vetName || '', vetPhone: p.vetPhone || '', vetEmail: p.vetEmail || '', instructions: p.instructions || ''
    };
    Object.keys(values).forEach(name => {
      const field = form.elements.namedItem(name);
      if (field && field.value !== values[name]) field.value = values[name];
    });
    const dateInput = $('#surgery-date-input');
    if (dateInput) dateInput.max = localDateISO();
  }
  function saveProfile(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const petName = String(data.get('petName') || '').trim();
    const species = String(data.get('species') || '').trim();
    const procedure = String(data.get('procedure') || '').trim();
    const surgeryDate = String(data.get('surgeryDate') || '').trim();
    if (!petName || !species || !procedure || !surgeryDate) {
      showToast('Please complete the pet, procedure and date fields.');
      return;
    }
    if (surgeryDate > localDateISO()) {
      showToast('Please use the procedure date from the clinic record.');
      return;
    }
    state.profile = {
      petName, species, procedure, surgeryDate,
      breed: String(data.get('breed') || '').trim(),
      clinic: String(data.get('clinic') || '').trim(),
      vetName: String(data.get('vetName') || '').trim(),
      vetPhone: String(data.get('vetPhone') || '').trim(),
      vetEmail: String(data.get('vetEmail') || '').trim(),
      instructions: String(data.get('instructions') || '').trim(),
      updatedAt: new Date().toISOString()
    };
    write(KEYS.profile, state.profile);
    showToast('Pet profile saved to this browser.');
    go('overview');
  }

  function petDayLabel() {
    const date = state.profile && state.profile.surgeryDate;
    if (!date) return 'RECOVERY OVERVIEW';
    const start = new Date(date + 'T12:00:00');
    const now = new Date(localDateISO() + 'T12:00:00');
    const diff = Math.floor((now.getTime() - start.getTime()) / 86400000) + 1;
    return diff < 1 ? 'PROCEDURE SCHEDULED' : 'RECOVERY DAY ' + diff;
  }
  function latestCheckin() { return state.checkins.length ? state.checkins[0] : null; }
  function todaysCheckins() { const today = localDateISO(); return state.checkins.filter(item => item.date === today); }
  function todaysMedicationStatus(med) { return Array.isArray(med.takenDates) && med.takenDates.includes(localDateISO()); }
  function statusPill(color) {
    const c = String(color || '').toUpperCase();
    if (c === 'GREEN') return '<span class="pill pill-green">Model flag: GREEN</span>';
    if (c === 'YELLOW') return '<span class="pill pill-yellow">Model flag: YELLOW</span>';
    if (c === 'RED') return '<span class="pill pill-red">Model flag: RED</span>';
    return '<span class="pill">Review result</span>';
  }
  function updateOverview() {
    const profile = state.profile || {};
    const name = profile.petName || 'your pet';
    $('#overview-date').textContent = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' }).toUpperCase();
    $('#recovery-day').textContent = petDayLabel();
    $('#hero-pet-name').textContent = name;
    $('#hero-summary').textContent = profile.procedure ? profile.procedure + ' · ' + profile.species + (profile.breed ? ' · ' + profile.breed : '') + '. Keep following the plan your veterinary team gave you.' : 'A short check-in helps you keep a useful record and spot changes worth discussing with your vet.';
    $$('[data-pet-name]').forEach(node => { node.textContent = name; });

    const todays = todaysCheckins();
    $('#stat-checkin').textContent = todays.length ? 'Recorded' : 'Not yet';
    $('#stat-checkin-foot').textContent = todays.length ? todays.length + ' check-in' + (todays.length > 1 ? 's' : '') + ' saved today' : 'A few quick questions';
    $('#task-checkin-desc').textContent = todays.length ? 'A check-in is saved. Add another if something changes.' : 'Record comfort, appetite and activity.';

    const medsCount = state.medications.length;
    const medsDone = state.medications.filter(todaysMedicationStatus).length;
    $('#stat-meds').textContent = medsCount ? medsDone + ' / ' + medsCount : 'No plan';
    $('#stat-meds-foot').textContent = medsCount ? 'Doses marked as given today' : 'Add the vet’s medication schedule';
    const analysis = state.analyses.length ? state.analyses[0] : null;
    $('#stat-photo').textContent = analysis ? analysis.color : 'None yet';
    $('#stat-photo-foot').textContent = analysis ? analysis.type + ' · ' + formatMoment(analysis.timestamp) : 'Optional, experimental support';

    const last = latestCheckin();
    const bannerText = last && last.urgent ? 'A warning sign was checked in. Contact a veterinary professional now; do not wait for photo analysis.' : (last && last.incision === 'More red or swollen' ? 'Your latest note records increased redness or swelling. Follow the discharge instructions and contact your clinic promptly for guidance.' : 'A short check-in helps you keep a useful record and spot changes worth discussing with your vet.');
    $('#hero-summary').textContent = bannerText;

    const medList = $('#med-list');
    if (!medsCount) {
      medList.innerHTML = '<div class="empty-state">No medication schedule added yet. Add the name and time exactly as written in your vet’s plan.</div>';
    } else {
      medList.innerHTML = state.medications.map(med => {
        const done = todaysMedicationStatus(med);
        return '<div class="med-row"><div><div class="med-name">' + cleanText(med.name) + '</div><div class="med-detail">' + cleanText(med.time) + (med.instructions ? ' · ' + cleanText(med.instructions) : '') + '</div></div><button type="button" class="btn btn-sm ' + (done ? 'btn-secondary' : '') + '" data-action="toggle-med" data-id="' + cleanText(med.id) + '">' + (done ? 'Undo tick' : 'Mark given') + '</button></div>';
      }).join('');
    }

    const history = $('#checkin-history');
    if (!state.checkins.length) {
      history.innerHTML = '<div class="empty-state">No recovery notes yet. Start with today’s check-in and add a note whenever something changes.</div>';
    } else {
      history.innerHTML = state.checkins.slice(0, 5).map(item => {
        const title = item.urgent ? 'Warning sign selected — veterinary help advised' : (item.incision === 'More red or swollen' ? 'Incision change noted' : 'Daily check-in saved');
        const copy = 'Comfort: ' + item.comfort + ' · Appetite: ' + item.appetite + ' · Movement: ' + item.mobility + (item.notes ? ' · Note: ' + item.notes : '');
        return '<article class="history-item"><div class="history-date">' + cleanText(formatDate(item.date, { day: 'numeric', month: 'short' })) + '<br><span class="muted">' + cleanText(item.time || '') + '</span></div><div><div class="history-title">' + cleanText(title) + '</div><p class="history-copy">' + cleanText(copy) + '</p></div></article>';
      }).join('');
    }
  }

  function updateCheckinPage() {
    $('#checkin-date-pill').textContent = new Date().toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' });
    $$('[data-pet-name]').forEach(node => { node.textContent = state.profile ? state.profile.petName : 'your pet'; });
  }

  function saveCheckin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const flags = data.getAll('redFlags').map(String);
    const mobility = String(data.get('mobility') || '');
    const incision = String(data.get('incision') || '');
    const urgent = flags.length > 0 || mobility === 'Unable to stand or walk' || incision === 'Open, bleeding or discharge';
    const item = {
      id: String(Date.now()) + '-' + Math.random().toString(36).slice(2, 7),
      date: localDateISO(), time: new Date().toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }),
      timestamp: new Date().toISOString(),
      comfort: String(data.get('comfort') || ''), appetite: String(data.get('appetite') || ''),
      mobility, incision, medication: String(data.get('medication') || ''),
      redFlags: flags, urgent, notes: String(data.get('notes') || '').trim()
    };
    state.checkins.unshift(item);
    write(KEYS.checkins, state.checkins);
    form.reset();
    if (urgent) {
      showToast('Check-in saved. Please seek urgent veterinary guidance now.');
      go('care');
    } else if (incision === 'More red or swollen' || item.appetite === 'Not eating' || item.medication === 'Missed or unsure') {
      showToast('Check-in saved. Consider contacting your clinic for guidance.');
      go('overview');
    } else {
      showToast('Check-in saved in this browser.');
      go('overview');
    }
  }

  function addMedication(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const name = String(data.get('name') || '').trim();
    const time = String(data.get('time') || '').trim();
    const instructions = String(data.get('instructions') || '').trim();
    if (!name || !time) return;
    state.medications.unshift({ id: String(Date.now()), name, time, instructions, takenDates: [] });
    write(KEYS.medications, state.medications);
    event.currentTarget.reset();
    updateOverview();
    showToast('Added to the local medication log. No reminder was scheduled.');
  }
  function toggleMedication(id) {
    const med = state.medications.find(item => String(item.id) === String(id));
    if (!med) return;
    if (!Array.isArray(med.takenDates)) med.takenDates = [];
    const today = localDateISO();
    med.takenDates = med.takenDates.includes(today) ? med.takenDates.filter(date => date !== today) : med.takenDates.concat(today);
    write(KEYS.medications, state.medications);
    updateOverview();
    showToast('Medication log updated. Follow the prescribed dose and timing.');
  }

  function normalizedApiBase() {
    let value = String(state.apiBase || DEFAULT_API).trim();
    value = value.replace(/\/+$/, '');
    return value;
  }
  async function apiRequest(path, options) {
    const base = normalizedApiBase();
    const response = await fetch(base + path, options || {});
    const type = response.headers.get('content-type') || '';
    const body = type.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      const detail = body && body.detail ? body.detail : (typeof body === 'string' ? body : response.statusText);
      throw new Error('API error (' + response.status + '): ' + detail);
    }
    return body;
  }
  function updatePhotosPage() {
    $('#api-base').value = state.apiBase;
  }
  async function saveApiSettings(event) {
    if (event) event.preventDefault();
    const input = $('#api-base');
    const value = String(input.value || '').trim().replace(/\/+$/, '');
    try {
      const url = new URL(value);
      if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Use an HTTP or HTTPS API address.');
      state.apiBase = url.origin + url.pathname.replace(/\/+$/, '');
      localStorage.setItem(KEYS.apiBase, state.apiBase);
      $('#api-base').value = state.apiBase;
      showToast('API address saved in this browser.');
    } catch (error) {
      $('#api-status').textContent = 'Enter a valid HTTP or HTTPS API base URL.';
      return false;
    }
    return true;
  }
  async function checkApi() {
    const button = $('#check-api-button');
    const status = $('#api-status');
    const pill = $('#api-state-pill');
    button.disabled = true;
    button.textContent = 'Checking…';
    status.className = 'note';
    status.textContent = 'Checking ' + normalizedApiBase() + '/health …';
    try {
      const health = await apiRequest('/health');
      if (!health || typeof health !== 'object' || health.status !== 'online' || !health.service) throw new Error('The /health response did not identify a PetTot API. Check the API base URL.');
      status.textContent = 'Connected: ' + health.service + '. Models: ' + ((health.models || []).join(', ') || 'not listed') + '.';
      pill.className = 'pill pill-green';
      pill.textContent = 'Connected';
    } catch (error) {
      status.textContent = 'Could not reach the API. Start the FastAPI server on the configured address, then try again. Details: ' + error.message;
      pill.className = 'pill pill-red';
      pill.textContent = 'Offline';
    } finally {
      button.disabled = false;
      button.textContent = 'Check connection';
    }
  }
  function previewFile(input, previewSelector) {
    const file = input.files && input.files[0];
    const img = $(previewSelector);
    if (!file || !img) { if (img) img.classList.add('hidden'); return; }
    if (!file.type || !file.type.startsWith('image/')) {
      input.value = '';
      img.removeAttribute('src');
      img.classList.add('hidden');
      showToast('Please choose an image file.');
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      input.value = '';
      img.removeAttribute('src');
      img.classList.add('hidden');
      showToast('Please use an image smaller than 15 MB.');
      return;
    }
    if (img.dataset.objectUrl) URL.revokeObjectURL(img.dataset.objectUrl);
    const objectUrl = URL.createObjectURL(file);
    img.dataset.objectUrl = objectUrl;
    img.src = objectUrl;
    img.classList.remove('hidden');
  }
  function buttonBusy(button, busy, label) {
    if (!button) return;
    if (busy) {
      button.dataset.originalLabel = button.textContent;
      button.disabled = true;
      button.textContent = label || 'Analyzing…';
    } else {
      button.disabled = false;
      button.textContent = button.dataset.originalLabel || button.textContent;
    }
  }
  function saveAnalysis(type, color, summary, metrics) {
    const entry = { id: String(Date.now()), timestamp: new Date().toISOString(), type, color: String(color || 'REVIEW').toUpperCase(), summary: String(summary || ''), metrics: metrics || {} };
    state.analyses.unshift(entry);
    state.analyses = state.analyses.slice(0, 30);
    write(KEYS.analyses, state.analyses);
    return entry;
  }
  function modelGuidance(color, kind) {
    const c = String(color || '').toUpperCase();
    if (c === 'RED') return 'This prototype model flagged the image for urgent review. Contact your veterinary clinic or emergency service now. The app has not notified anyone.';
    if (c === 'YELLOW') return 'This prototype model flagged a possible change. Follow your clinic’s instructions and contact them for advice about the next step.';
    if (c === 'GREEN') return 'The model did not flag a change under its current rules. This does not rule out pain, infection or another complication. Trust your observations and contact your vet if concerned.';
    return 'The model did not return a familiar status. Do not treat this as reassurance; contact your vet if you are concerned.';
  }
  function resultStatusClass(color) {
    const c = String(color || '').toUpperCase();
    return c === 'GREEN' ? 'pill-green' : (c === 'YELLOW' ? 'pill-yellow' : (c === 'RED' ? 'pill-red' : ''));
  }
  function safeImageData(value) {
    return typeof value === 'string' && /^data:image\/(?:png|jpe?g|webp);base64,/i.test(value) ? value : '';
  }
  async function analyzeFace(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = $('#face-file').files[0];
    if (!file) { showToast('Choose a face photo first.'); return; }
    const button = $('button[type="submit"]', form);
    buttonBusy(button, true, 'Analyzing photo…');
    const out = $('#face-result');
    out.innerHTML = '<div class="result-card"><p class="result-copy">Sending the selected image to the configured PetTot API…</p></div>';
    try {
      const data = new FormData();
      data.append('file', file);
      data.append('baseline_mar', '2.0');
      data.append('force_fallback', 'false');
      const result = await apiRequest('/api/grimace/analyze', { method: 'POST', body: data });
      const color = String(result.triage_color || 'REVIEW').toUpperCase();
      const score = result.total_grimace_score;
      const scoreText = Number.isFinite(Number(score)) ? cleanText(score) + ' / ' + cleanText(result.max_score || 8) : 'Score unavailable';
      const image = safeImageData(result.visualization_b64);
      out.innerHTML = '<div class="result-card"><div class="result-top"><div><div class="eyebrow">Experimental facial-feature output</div><div class="result-score">' + scoreText + '</div></div><span class="pill ' + resultStatusClass(color) + '">' + cleanText(color) + '</span></div><p class="result-copy">' + cleanText(result.triage_status || 'No status text returned.') + '</p><p class="result-copy">' + cleanText(modelGuidance(color, 'face')) + '</p><p class="footnote">Pipeline: ' + cleanText(result.pipeline || 'not specified') + '. This prototype score is not a validated general-purpose pain scale.</p>' + (image ? '<img src="' + image + '" alt="Backend-generated face analysis preview">' : '') + '</div>';
      saveAnalysis('Face', color, 'Facial-feature score ' + scoreText + '. ' + modelGuidance(color, 'face'), { score: Number.isFinite(Number(score)) ? Number(score) : null, maxScore: Number(result.max_score || 8) });
    } catch (error) {
      out.innerHTML = '<div class="result-card"><span class="pill pill-red">Analysis unavailable</span><p class="result-copy">' + cleanText(error.message) + '</p><p class="result-copy">Check the API address and the backend terminal. A failed request is not a health assessment.</p></div>';
      showToast('Face analysis could not be completed.');
    } finally { buttonBusy(button, false); }
  }
  async function analyzeWound(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const baseFile = $('#wound-base-file').files[0];
    const currentFile = $('#wound-current-file').files[0];
    if (!baseFile || !currentFile) { showToast('Choose both baseline and current incision photos.'); return; }
    const button = $('button[type="submit"]', form);
    buttonBusy(button, true, 'Comparing photos…');
    const out = $('#wound-result');
    out.innerHTML = '<div class="result-card"><p class="result-copy">Sending both images to the configured PetTot API…</p></div>';
    try {
      const data = new FormData();
      data.append('day1_file', baseFile);
      data.append('dayN_file', currentFile);
      const result = await apiRequest('/api/incision/scan', { method: 'POST', body: data });
      const color = String(result.triage_color || 'REVIEW').toUpperCase();
      const metrics = result.metrics || {};
      const delta = Number(metrics.delta_e_percent);
      const deltaText = Number.isFinite(delta) ? (delta > 0 ? '+' : '') + delta.toFixed(1) + '%' : 'Not available';
      const gap = metrics.structural_gap_detected === true ? 'A possible structural gap was flagged.' : 'No structural gap was flagged by this model.';
      const image = safeImageData(result.overlay_mask_b64);
      out.innerHTML = '<div class="result-card"><div class="result-top"><div><div class="eyebrow">Incision comparison output</div><div class="result-score">' + cleanText(deltaText) + '</div><p class="result-copy">Change in the model’s redness ratio</p></div><span class="pill ' + resultStatusClass(color) + '">' + cleanText(color) + '</span></div><p class="result-copy">' + cleanText(gap) + '</p><p class="result-copy">' + cleanText(modelGuidance(color, 'incision')) + '</p><div class="note">Metrics describe an image-processing heuristic, not a diagnosis of infection or wound opening. ' + cleanText(result.triage_label || '') + '</div>' + (image ? '<img src="' + image + '" alt="Backend-generated incision comparison overlay">' : '') + '</div>';
      saveAnalysis('Incision', color, 'Redness-ratio change ' + deltaText + '. ' + gap + ' ' + modelGuidance(color, 'incision'), { deltaPercent: Number.isFinite(delta) ? delta : null, gapDetected: metrics.structural_gap_detected === true });
    } catch (error) {
      out.innerHTML = '<div class="result-card"><span class="pill pill-red">Comparison unavailable</span><p class="result-copy">' + cleanText(error.message) + '</p><p class="result-copy">Check the API address and the backend terminal. A failed request is not a health assessment.</p></div>';
      showToast('Incision comparison could not be completed.');
    } finally { buttonBusy(button, false); }
  }

  function updateCarePage() {
    const p = state.profile || {};
    const details = $('#care-contact-details');
    const rows = [];
    rows.push('<div class="contact-row"><div class="contact-icon">⌂</div><div><strong>' + cleanText(p.clinic || 'Clinic not added') + '</strong><p>' + cleanText(p.vetName || 'Care team not specified') + '</p></div></div>');
    rows.push('<div class="contact-row"><div class="contact-icon">☎</div><div><strong>Phone</strong><p>' + cleanText(p.vetPhone || 'Add a phone number in the pet profile') + '</p></div></div>');
    rows.push('<div class="contact-row"><div class="contact-icon">✉</div><div><strong>Email</strong><p>' + cleanText(p.vetEmail || 'Add an email address in the pet profile') + '</p></div></div>');
    rows.push('<div class="contact-row"><div class="contact-icon">✚</div><div><strong>Procedure</strong><p>' + cleanText(p.procedure || 'Not specified') + ' · ' + cleanText(formatDate(p.surgeryDate)) + '</p></div></div>');
    details.innerHTML = rows.join('');
    const call = $('#call-clinic');
    if (p.vetPhone && safeURLPhone(p.vetPhone).replace(/\D/g, '').length >= 5) {
      call.href = 'tel:' + safeURLPhone(p.vetPhone);
      call.setAttribute('aria-disabled', 'false');
      call.classList.remove('btn-secondary');
    } else {
      call.href = '#'; call.setAttribute('aria-disabled', 'true'); call.classList.add('btn-secondary');
    }
    const email = $('#email-clinic');
    if (p.vetEmail) {
      email.href = 'mailto:' + encodeURIComponent(p.vetEmail);
      email.setAttribute('aria-disabled', 'false');
    } else {
      email.href = '#'; email.setAttribute('aria-disabled', 'true');
    }
    $('#vet-summary').value = buildVetSummary();
  }
  function buildVetSummary() {
    const p = state.profile || {};
    const lines = [
      'PetTot recovery summary (prepared locally; not sent)',
      'Pet: ' + (p.petName || 'Not provided') + ' (' + (p.species || 'species not provided') + (p.breed ? ', ' + p.breed : '') + ')',
      'Procedure: ' + (p.procedure || 'Not provided'),
      'Procedure date: ' + formatDate(p.surgeryDate),
      'Clinic: ' + (p.clinic || 'Not provided'),
      'Generated: ' + new Date().toLocaleString(),
      '',
      'Latest check-in:'
    ];
    const checkin = latestCheckin();
    if (checkin) {
      lines.push(formatDate(checkin.date) + (checkin.time ? ' at ' + checkin.time : ''));
      lines.push('Comfort: ' + checkin.comfort + '; appetite: ' + checkin.appetite + '; movement: ' + checkin.mobility + '; incision observation: ' + checkin.incision);
      lines.push('Medication note: ' + checkin.medication);
      if (checkin.redFlags && checkin.redFlags.length) lines.push('Warning signs selected: ' + checkin.redFlags.join(', '));
      if (checkin.notes) lines.push('Owner note: ' + checkin.notes);
    } else lines.push('No check-in recorded yet.');
    lines.push('', 'Latest image-model output:');
    const analysis = state.analyses[0];
    if (analysis) lines.push(analysis.type + ' · ' + analysis.color + ' · ' + formatMoment(analysis.timestamp), analysis.summary || '');
    else lines.push('No image analysis recorded.');
    lines.push('', 'This is an owner-prepared log, not a diagnosis. Please advise on the appropriate next step.');
    return lines.join('\n');
  }
  async function copySummary() {
    const area = $('#vet-summary');
    const text = area.value || buildVetSummary();
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(text);
      else { area.focus(); area.select(); const copied = document.execCommand('copy'); if (!copied) throw new Error('Copy unavailable'); }
      $('#summary-status').textContent = 'Copied to clipboard. It has not been sent to the clinic.';
      showToast('Summary copied. You decide where to share it.');
    } catch (error) {
      area.focus(); area.select();
      $('#summary-status').textContent = 'Select the text above and copy it manually. It has not been sent.';
    }
  }
  function emailSummary() {
    const email = (state.profile && state.profile.vetEmail) || '';
    if (!email) { showToast('Add your clinic’s email address in the pet profile first.'); go('setup'); return; }
    const subject = 'Recovery update for ' + ((state.profile && state.profile.petName) || 'my pet');
    const url = 'mailto:' + encodeURIComponent(email) + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent($('#vet-summary').value || buildVetSummary());
    window.location.href = url;
    $('#summary-status').textContent = 'Your email app was asked to open a draft. You still need to review and send it.';
  }
  function exitDemo() {
    sessionStorage.removeItem(KEYS.sessionEmail);
    go('login');
  }

  document.addEventListener('click', event => {
    const routeButton = event.target.closest('[data-route]');
    if (routeButton) {
      event.preventDefault();
      if (routeButton.dataset.route === 'setup' && !isActiveSession()) { go('login'); return; }
      go(routeButton.dataset.route);
      return;
    }
    const action = event.target.closest('[data-action]');
    if (!action) return;
    event.preventDefault();
    switch (action.dataset.action) {
      case 'back-login': go('login'); break;
      case 'exit-demo': exitDemo(); break;
      case 'toggle-med': toggleMedication(action.dataset.id); break;
      case 'check-api': checkApi(); break;
      case 'copy-summary': copySummary(); break;
      case 'email-summary': emailSummary(); break;
      case 'scroll-analysis': {
        const tools = $('#analysis-tools');
        if (tools) { tools.scrollIntoView({ behavior: 'smooth', block: 'start' }); const first = $('#face-file'); if (first) window.setTimeout(() => first.focus({ preventScroll: true }), 350); }
        break;
      }
      case 'focus-summary': {
        const summary = $('#vet-summary');
        if (summary) { summary.scrollIntoView({ behavior: 'smooth', block: 'center' }); window.setTimeout(() => summary.focus({ preventScroll: true }), 350); }
        break;
      }
      default: break;
    }
  });
  document.addEventListener('click', event => {
    const disabledLink = event.target.closest('a[aria-disabled="true"]');
    if (disabledLink) {
      event.preventDefault();
      showToast('Add the clinic contact details in your pet profile first.');
    }
  });
  document.addEventListener('change', event => {
    const previews = {
      'face-file': '#face-preview',
      'wound-base-file': '#wound-base-preview',
      'wound-current-file': '#wound-current-preview'
    };
    if (previews[event.target.id]) previewFile(event.target, previews[event.target.id]);
  });
  wirePhotoFallbacks();

  $('#demo-form').addEventListener('submit', event => {
    event.preventDefault();
    const email = String($('#demo-email').value || '').trim();
    state.sessionEmail = email;
    sessionStorage.setItem(KEYS.sessionEmail, email || 'demo-session');
    go(state.profile ? 'overview' : 'setup');
  });
  $('#setup-form').addEventListener('submit', saveProfile);
  $('#checkin-form').addEventListener('submit', saveCheckin);
  $('#medication-form').addEventListener('submit', addMedication);
  $('#api-form').addEventListener('submit', async event => { const saved = await saveApiSettings(event); if (saved) checkApi(); });
  $('#face-form').addEventListener('submit', analyzeFace);
  $('#wound-form').addEventListener('submit', analyzeWound);
  window.addEventListener('hashchange', renderRoute);

  // Populate the API field and route to the first step unless an active demo session exists.
  $('#api-base').value = state.apiBase;
  if (!window.location.hash) window.history.replaceState(null, '', '#' + (isActiveSession() ? (state.profile ? 'overview' : 'setup') : 'login'));
  renderRoute();
})();
