/* Shared navigation for the static PetTot screens. */
(function () {
  const routes = {
    'login-and-patient-switcher': '../pettot_welcome_patient_login/code.html',
    'recovery-overview': '../pettot_simple_pet_recovery_for_pet_parents/code.html',
    'daily-check-in': '../pettot_daily_check_in_routine/code.html',
    'care-team-notes': '../pettot_connect_doctor_care_team/code.html',
    'care-team-and-connect-doctor': '../pettot_connect_doctor_care_team/code.html',
    'help-and-emergency': '../pettot_help_emergency_vet_support/code.html'
  };

  const currentDirectory = window.location.pathname.split('/').slice(-2, -1)[0];
  const routeFor = (path) => routes[path] || routes['recovery-overview'];

  function navigate(path) {
    window.location.href = new URL(routeFor(path), window.location.href).href;
  }

  function addButtonRoutes() {
    const text = (element) => element.textContent.replace(/\s+/g, ' ').trim().toLowerCase();
    document.querySelectorAll('button').forEach((button) => {
      const label = text(button);
      if (label.includes('start 2-min check-in')) button.dataset.path = 'daily-check-in';
      if (label.includes('send quick photo') || label.includes('message dr.')) button.dataset.path = 'care-team-notes';
      if (label.includes('message nursing team')) button.dataset.path = 'care-team-notes';
      if (label.includes('view post-op medication chart')) button.dataset.path = 'daily-check-in';
      if (label.includes('save draft')) button.dataset.action = 'save-draft';
    });
  }

  function routeLegacyLinks() {
    document.querySelectorAll('a[href="#"]').forEach((link) => {
      const label = link.textContent.replace(/\s+/g, ' ').trim().toLowerCase();
      if (label.includes('clinic assistance') || label.includes('hospital support')) {
        link.dataset.path = 'care-team-notes';
      }
      if (label.includes('message nursing team')) link.dataset.path = 'care-team-notes';
      if (label.includes('save & complete')) link.dataset.path = 'recovery-overview';
      if (label.includes('view post-op medication chart')) link.dataset.path = 'daily-check-in';
    });
  }

  function markActiveRoute() {
    const page = Object.keys(routes).find((key) => routes[key].includes(currentDirectory + '/'));
    document.querySelectorAll('[data-path]').forEach((element) => {
      if (element.dataset.path === page) element.setAttribute('aria-current', 'page');
    });
  }

  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-path]');
    if (target) {
      event.preventDefault();
      navigate(target.dataset.path);
      return;
    }
    const action = event.target.closest('[data-action="save-draft"]');
    if (action) {
      action.textContent = 'Draft Saved';
      action.setAttribute('aria-label', 'Draft saved');
    }
  });

  document.addEventListener('submit', (event) => {
    if (!event.target.matches('#form-magic, #form-sms, #form-passcode')) return;
    window.setTimeout(() => navigate('recovery-overview'), 1300);
  });

  document.addEventListener('DOMContentLoaded', () => {
    addButtonRoutes();
    routeLegacyLinks();
    markActiveRoute();
  });
})();
