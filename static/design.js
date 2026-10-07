(() => {
  const storageKey = 'badgeware-design-draft-v1';
  const booleanFields = new Set(['mirror', 'include_logo', 'include_print_marks', 'include_cut_lines', 'include_yellow_unifier', 'include_curve_effect']);
  const arrayFields = new Set(['sides', 'logo_sides']);
  const optionFields = new Set([
    'page_size', 'orientation', 'mode', 'order', 'unit', 'badge_size', 'spacing',
    'page_margin', 'panel_gap', 'logo_size', 'front_logo_size', 'back_logo_size',
    'copies', 'mirror', 'include_logo', 'sides', 'logo_sides', 'include_print_marks',
    'include_cut_lines', 'include_yellow_unifier', 'color_mode', 'ink_contrast',
    'include_curve_effect', 'curve_device', 'curve_diameter', 'front_text', 'back_text',
    'text_font', 'text_size', 'export_dpi', 'front_text_x', 'front_text_y', 'back_text_x', 'back_text_y',
  ]);

  function read() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(storageKey) || 'null');
      const design = stored?.version === 1 ? stored.design : null;
      return design && Array.isArray(design.badge_ids) && typeof design.options === 'object' ? design : null;
    } catch { return null; }
  }

  function write(design) {
    if (!design || !Array.isArray(design.badge_ids) || !design.options) return false;
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({ version: 1, saved_at: new Date().toISOString(), design }));
      window.dispatchEvent(new CustomEvent('badgeware:draft-saved', { detail: design }));
      return true;
    } catch { return false; }
  }

  function clear() {
    try { sessionStorage.removeItem(storageKey); } catch { /* Storage may be unavailable. */ }
  }

  function formOptions(form) {
    const options = {};
    for (const name of optionFields) {
      const fields = Array.from(form.elements).filter((field) => field.name === name);
      if (!fields.length) continue;
      if (arrayFields.has(name)) {
        options[name] = fields.filter((field) => field.type !== 'checkbox' || field.checked).map((field) => field.value);
      } else if (booleanFields.has(name)) {
        const checkbox = fields.find((field) => field.type === 'checkbox');
        options[name] = checkbox ? checkbox.checked : ['on', 'true', '1', 'yes'].includes(fields[0].value);
      } else {
        options[name] = fields[0].value;
      }
    }
    return options;
  }

  function attachManual(form, placements = []) {
    form.querySelectorAll('[data-draft-manual]').forEach((field) => field.remove());
    for (const item of placements) {
      if (!Number.isInteger(Number(item.layout_index)) || Number(item.layout_index) < 0 || !Number.isInteger(Number(item.placement_index)) || Number(item.placement_index) < 0) continue;
      const prefix = `manual_${Number(item.layout_index)}_${Number(item.placement_index)}`;
      const values = { x: item.x, y: item.y, rotation: item.rotation, badge_id: item.badge_id, side: item.side };
      if (item.locked) values.locked = 'on';
      for (const [key, value] of Object.entries(values)) {
        if (value === undefined || value === null) continue;
        const name = key === 'locked' ? `locked_${item.layout_index}_${item.placement_index}` : `${prefix}_${key}`;
        // Preview already has editable manual fields; do not duplicate them.
        if (Array.from(form.elements).some((field) => field.name === name && !field.hasAttribute('data-draft-manual'))) continue;
        const field = document.createElement('input');
        field.type = 'hidden'; field.name = name; field.value = String(value);
        field.dataset.draftManual = 'true'; form.appendChild(field);
      }
    }
  }

  window.BadgewareDesign = { read, write, clear, formOptions, attachManual };
})();
