document.querySelectorAll('.export-menu').forEach((menu) => {
  const summary = menu.querySelector('summary');
  menu.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      summary.focus();
      event.preventDefault();
    }
  });
  document.addEventListener('click', (event) => {
    if (!menu.contains(event.target)) menu.open = false;
  });
});

document.addEventListener('DOMContentLoaded', () => {
  // Keep opened help beside its trigger and within the viewport at every width.
  const help = [...document.querySelectorAll('.info-hint')];
  const positionHelp = (element) => {
    const bubble = element.querySelector('.hint-bubble');
    if (!bubble || !bubble.getClientRects().length) return;
    const trigger = element.querySelector('summary').getBoundingClientRect();
    const bounds = bubble.getBoundingClientRect();
    const left = Math.max(16, Math.min(trigger.left, window.innerWidth - bounds.width - 16));
    const top = trigger.bottom + 8 + bounds.height <= window.innerHeight - 16 ? trigger.bottom + 8 : Math.max(16, trigger.top - bounds.height - 8);
    Object.assign(bubble.style, { left: `${left}px`, top: `${top}px`, bottom: 'auto' });
  };
  help.forEach((element) => {
    ['toggle', 'mouseenter', 'focusin'].forEach((name) => element.addEventListener(name, () => {
      if (name !== 'toggle' || element.open) delete element.dataset.helpDismissed;
      positionHelp(element);
    }));
    element.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        element.open = false;
        element.dataset.helpDismissed = 'true';
        event.preventDefault();
      }
    });
  });
  const repositionHelp = () => help.forEach(positionHelp);
  window.addEventListener('resize', repositionHelp);
  window.addEventListener('scroll', repositionHelp, { capture: true, passive: true });
  const endpoints = new Set(['/pdf', '/proof.pdf', '/export.svg', '/export.png']);
  const setMessage = (element, key, params) => {
    if (window.BadgewareI18n) window.BadgewareI18n.message(element, key, params);
    else element.textContent = key;
  };
  const downloadError = (key, params = {}) => {
    const error = new Error(key);
    error.i18nKey = key; error.i18nParams = params;
    return error;
  };
  document.querySelectorAll('form.generator, #manual-layout-form').forEach((form) => {
    const actions = form.querySelector('.actions');
    if (!actions) return;
    const feedback = document.createElement('div');
    feedback.className = 'download-feedback'; feedback.hidden = true;
    const status = document.createElement('p');
    status.setAttribute('role', 'status'); status.tabIndex = -1;
    const retry = document.createElement('button');
    retry.type = 'button'; retry.className = 'secondary-button'; retry.hidden = true;
    setMessage(retry, 'Retry download');
    feedback.append(status, retry); actions.append(feedback);
    let busy = false;
    let lastSubmitter = null;
    retry.addEventListener('click', () => form.requestSubmit(lastSubmitter));
    form.addEventListener('submit', async (event) => {
      const submitter = event.submitter;
      const target = new URL(submitter?.getAttribute('formaction') || form.action, window.location.href);
      if (!endpoints.has(target.pathname)) return;
      event.preventDefault();
      if (busy) return;
      busy = true; lastSubmitter = submitter;
      const data = new FormData(form);
      if (submitter?.name) data.append(submitter.name, submitter.value);
      const buttons = Array.from(form.querySelectorAll('button[type="submit"]'));
      const disabled = buttons.map((button) => button.disabled);
      buttons.forEach((button) => { button.disabled = true; });
      form.setAttribute('aria-busy', 'true');
      feedback.hidden = false; retry.hidden = true; feedback.classList.remove('warning');
      setMessage(status, 'Generating your download…');
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 120000);
      try {
        const response = await fetch(target, { method: 'POST', body: data, signal: controller.signal });
        if (!response.ok) {
          let key = 'Download could not be generated. Please try again.';
          let params = {};
          try {
            const payload = await response.json();
            if (payload.error?.failures?.length) {
              const names = payload.error.failures.map((failure) => failure.name || failure.badge_id).filter(Boolean).join(', ');
              if (names) { key = 'Artwork could not be loaded: {names}. Check the affected badges and retry.'; params = { names }; }
            } else if (payload.error?.message) key = payload.error.message;
          } catch { /* Keep the clear fallback for HTML or empty error responses. */ }
          throw downloadError(key, params);
        }
        const blob = await response.blob();
        const expected = target.pathname.endsWith('.png') ? 'image/png' : target.pathname.endsWith('.svg') ? 'image/svg+xml' : 'application/pdf';
        if (!response.headers.get('Content-Type')?.includes(expected)) throw downloadError('The server returned an unexpected download. Please retry.');
        const disposition = response.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^";]+)"?/i);
        const filename = match?.[1] || (expected === 'image/png' ? 'badgeware.png' : expected === 'image/svg+xml' ? 'badgeware.svg' : 'badgeware.pdf');
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        setMessage(status, 'Download started. Check your browser’s downloads.');
        form.dispatchEvent(new CustomEvent('badgeware:download-ready'));
      } catch (error) {
        feedback.classList.add('warning'); retry.hidden = false;
        const key = error.name === 'AbortError' ? 'This download took too long. Your design is kept; try again.' : error.i18nKey || 'Connection failed. Your design is kept; try again.';
        setMessage(status, key, error.i18nParams); status.focus();
      } finally {
        clearTimeout(timeout);
        buttons.forEach((button, index) => { button.disabled = disabled[index]; });
        form.removeAttribute('aria-busy'); busy = false;
      }
    });
  });
});
