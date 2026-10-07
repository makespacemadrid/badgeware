# Further UX improvements

Goal: help users produce a correct printable design with fewer decisions, while retaining precise controls for experienced users. Build on the responsive controls and action hierarchy already merged in PR #25.

Deliver the work in the order below, using separate pull requests. Each change must preserve the existing browser, API, CLI, and saved-template workflows where applicable.

## 1. Protect the current design

Current problems: “Adjust settings” returns to a page initialized with defaults. Switching units or changing the curve-device preset resets unrelated measurements. The browser’s saved-design payload omits manual placements and PNG resolution, and loading a saved design does not restore badge-card order.

- Use one complete design representation for draft recovery and named templates: badge order and front/back assignments, normalized options, placements and locks, text positions, and export settings. Reuse the existing template JSON format and extend it compatibly where necessary.
- Keep a draft per browser tab across settings, preview, reload, and exports. Provide explicit “New design” and draft recovery controls. Retain uploaded asset references, not file-input contents; explain when referenced artwork no longer exists.
- Convert measurements when switching units. Where a converted size does not match a preset, support the equivalent custom value rather than resetting it. Changing the curve-device preset should affect its diameter alone.
- Allow saving the finished design from preview, including manual edits. Make replacement of a named design explicit and offer recovery for accidental deletion.

Acceptance: select and order three badges, assign different sides, change measurements, move/rotate/lock a badge, and reposition text. Preview → adjust settings → preview, reload, and save/load must retain that design. Switching cm ↔ inches must preserve physical dimensions, and choosing a curve preset must preserve unrelated settings. Older saved templates must still load.

## 2. Reduce setup decisions

- Offer a small set of clearly named starting presets, such as original-color transfer, black artwork for a yellow shirt, and black/yellow artwork. Show which settings each preset changes and allow customization.
- Keep badge selection, side selection, size, layout, and artwork colors in the main flow. Put spacing, margins, print marks, and other fine adjustments in an advanced section.
- Show contrast only for converted artwork and logo sizing only for selected logo sides. Keep inactive values so toggling an option does not erase work. Label PNG resolution as applying only to PNG exports.
- Move the full template library behind “Load a design”; offer “Start blank” and “Continue draft” when relevant.
- Do not imply that a color preset alone determines the correct transfer method or mirror setting. Show mirroring explicitly and explain it separately.

Acceptance: a new user can select three badges and reach a useful preview without opening advanced settings. Presets show their effects, inactive controls are clearly excluded from output, and existing users can access every current option.

## 3. Make preview the editing workspace

- Add compact color-mode and contrast controls directly above the preview. Update artwork without regenerating badge geometry or discarding manual edits.
- Provide undo/redo for movement, rotation, alignment, text positioning, and reset. Treat a drag as one edit.
- Keep front/back navigation and primary export actions easy to reach on mobile. Show selected-badge controls near the artwork; collapse the full coordinate table into an advanced view.
- Provide an explicit comparison of original and converted artwork for checking small lettering. Identify fabric backgrounds and guides as preview-only.

Acceptance: changing contrast retains every position and lock; undo restores a drag, an alignment operation, and a reset. The workflow works with touch and keyboard, and the exported artwork matches the chosen preview settings.

## 4. Make print output predictable

- Show a compact summary near export: sides/pages, page size, badge size, color mode, and mirror state. Include resolution when PNG is selected.
- Match the PDF button and filename to the actual mirror setting. Explain proof output as an unmirrored check, with a short reminder to print at actual size rather than “fit to page.”
- Keep overlap, missing-artwork, and low-resolution warnings visible until resolved. Separate those warnings from transient messages such as “Badge moved.” Link each warning to the affected artwork.
- Show generation progress and clear download errors, preserve edits on failure, and offer retry. Report successful generation/download initiation accurately rather than claiming the file was saved by the user.

Acceptance: a mirror-off design never offers misleading mirrored-output wording. Overlap warnings remain visible after another edit, asset failures identify the badge, and retry uses the same design. PDF and PNG dimensions match the displayed summary.

## 5. Complete language and accessibility support

- Translate dynamic selection labels, save/load results, placement messages, errors, and option names through shared translation keys. Retain the chosen language throughout the workflow.
- Make focus, selected elements, disabled options, and warnings understandable without relying on color alone. Give touch users visible selection and move controls alongside keyboard shortcuts.
- Review help text and empty states: no selected badges, no saved designs, missing uploads, and unavailable upstream artwork should each explain the next useful action.

Acceptance: complete selection → preview editing → save/load → export in Spanish and English without mixed-language status messages. Complete the same flow using keyboard controls, with readable focus and warning states at mobile widths.

## Validation and delivery

- Add browser regression coverage for draft recovery, physical unit conversion, saved final layouts, filter changes without movement, and mirror-aware exports. Keep existing integration tests for the underlying routes.
- Check both languages at narrow mobile, tablet, and desktop widths; verify that menus and help content remain usable without horizontal page scrolling.
- Use the actual Archivist, Assembly Regular, and Been There artwork when checking contrast and print output.
- Run a short usability check with a first-time user and a returning user. Record completion time, backtracking, missed warnings, and whether their downloaded output matches their intent. Compare before and after rather than assuming improvement from appearance alone.
- Prioritize steps 1–4; apply translation, accessibility, and error handling to each step as it ships. Step 5 closes the remaining gaps.

Defer new garment templates, additional layout algorithms, and broader integrations until the current design-to-print workflow reliably preserves work and explains its output.

## Implementation status

Stages 1–5 are implemented locally as one connected design-to-print workflow. Drafts use per-tab session storage; named templates provide longer-term storage. Preview and exports share normalized options and complete placement identities, including locks, labels, and PNG resolution. Browser exports stop on unavailable artwork and support retry. The existing JSON API and MCP explicit partial-render options remain available.

Browser regressions cover recovery from an older submitted preview after reload or a cached settings page after browser Back, finished-design save/load and delete recovery, explicit name replacement, unit conversion before and after manual edits, badge reordering with retained positions, direct text creation, undo/redo, locked controls, conversion without geometry changes, persistent warnings, mirror-aware PDF downloads, missing-artwork recovery, disabled-panel submission prevention, and both interface languages at mobile widths.

SVG and PNG include edited labels and retain their existing unmirrored contact-sheet format. PDF remains the output for transfer-specific settings and proof printing.

Visual checks passed for 280 combinations of page, language, colour mode, viewport, and opened help across 320, 375, 414, 768, 1024, 1440, and 1920 pixel widths. Checks used the actual Archivist, Assembly Regular, and Been There artwork. Print summaries and resolution checks use the placed badge sizes, including layouts that shrink artwork to fit.

Final verification: 203 tests passed, including 18 Chromium workflow regressions; Ruff and whitespace checks passed. One existing ReportLab deprecation warning remains.

The first-time/returning-user usability sessions remain a follow-up requiring participants. Automated checks verify behavior; they do not establish human completion time or missed-warning rates.
