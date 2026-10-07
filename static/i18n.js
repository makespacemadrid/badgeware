/* Lightweight browser-side localization. English remains the source language so
   form values and server APIs are unchanged when the visible language changes. */
(() => {
  const translations = {
    'Download calibration page': 'Descargar página de calibración',
    'Refresh badges from GitHub': 'Actualizar insignias desde GitHub',
    'AutoPlot badges (& other images) into t-shirts & mugs': 'Coloca insignias (y otras imágenes) automáticamente en camisetas y tazas',
    'Select badges, choose a print-safe placement mode, tune the sheet by hand, then download a mirrored PDF.': 'Selecciona insignias, elige una colocación segura para imprimir, ajusta la hoja manualmente y descarga un PDF reflejado.',
    'Template workflow': 'Flujo de trabajo de la plantilla',
    '1. Pick': '1. Elige', 'Choose badges, logo, panels, and units.': 'Elige insignias, logotipo, paneles y unidades.',
    '2. Arrange': '2. Organiza', 'Preview automatic layouts or drag elements.': 'Previsualiza la disposición automática o arrastra los elementos.',
    '3. Print': '3. Imprime', 'Export a sublimation-ready PDF.': 'Exporta un PDF listo para sublimación.',
    'Upload notices': 'Avisos de carga', 'Saved design templates': 'Plantillas de diseño guardadas',
    'Template library help': 'Ayuda de la biblioteca de plantillas', 'Template name': 'Nombre de la plantilla',
    'Load saved template': 'Cargar plantilla guardada', 'Choose a saved template': 'Elige una plantilla guardada',
    'Save current design': 'Guardar diseño actual', 'Load selected design': 'Cargar diseño seleccionado',
    'Delete selected design': 'Eliminar diseño seleccionado', 'Saved template actions': 'Acciones de plantillas guardadas',
    'Saved templates stay on this server under the configured template folder.': 'Las plantillas guardadas permanecen en este servidor, en la carpeta configurada.',
    'Badges': 'Insignias', 'Badge picker help': 'Ayuda del selector de insignias',
    'Upload badge artwork': 'Subir imagen de insignia', 'More information': 'Más información',
    'front': 'anverso', 'back': 'reverso', 'on both pages': 'en ambas páginas',
    'selected by default': 'seleccionadas por defecto', 'visible after filters': 'visibles tras filtrar',
    'Front and back are ready.': 'El anverso y el reverso están listos.',
    'Skip badge list and continue to actions': 'Saltar la lista de insignias y continuar a las acciones',
    'Badge search and bulk selection': 'Búsqueda y selección masiva de insignias', 'Search badges': 'Buscar insignias',
    'Name or path': 'Nombre o ruta', 'Category': 'Categoría', 'All categories': 'Todas las categorías',
    'Show assignment': 'Mostrar asignación', 'All assignments': 'Todas las asignaciones',
    'Front page': 'Anverso', 'Back page': 'Reverso', 'Both pages': 'Ambas páginas', 'Not printed': 'No se imprime',
    'Apply side assignment to visible badges': 'Asignar caras a las insignias visibles',
    'Select visible for both sides': 'Seleccionar visibles para ambas caras', 'Front only': 'Solo anverso',
    'Back only': 'Solo reverso', 'Clear visible': 'Limpiar visibles', 'Reset filters': 'Restablecer filtros',
    'Toggle badge view': 'Cambiar vista de insignias', 'Show text rows': 'Mostrar filas de texto',
    'Show thumbnails': 'Mostrar miniaturas',
    'Print on': 'Imprimir en', 'Front': 'Anverso', 'Back': 'Reverso', 'Replace upload': 'Reemplazar archivo',
    'Delete upload': 'Eliminar archivo', 'Template options': 'Opciones de plantilla',
    'Set up once, adjust in preview': 'Configura una vez y ajusta en la vista previa',
    'Template setup help': 'Ayuda de configuración', '1. Page and layout': '1. Página y disposición',
    'Page size': 'Tamaño de página', 'Orientation': 'Orientación', 'Placement': 'Colocación',
    'Badge order': 'Orden de insignias', 'Units': 'Unidades', 'Copies per badge': 'Copias por insignia',
    '2. Badge size and labels': '2. Tamaño y etiquetas de insignias', 'Badge size': 'Tamaño de insignia',
    'Spacing': 'Espaciado', 'Page margin': 'Margen de página', 'Panel gap': 'Separación entre paneles',
    'Front text': 'Texto del anverso', 'Back text': 'Texto del reverso', 'Text font': 'Fuente del texto',
    'Text size': 'Tamaño del texto', '3. PDF output': '3. Salida PDF',
    'Front logo size': 'Tamaño del logotipo frontal', 'Back logo size': 'Tamaño del logotipo trasero',
    'Curve device': 'Dispositivo curvo', 'Apply curved effect in the PDF': 'Aplicar efecto curvo en el PDF',
    'Front panel': 'Panel frontal', 'Back panel': 'Panel trasero', 'Logo on front': 'Logotipo en el anverso',
    'Logo on back': 'Logotipo en el reverso', 'Mirror for sublimation transfer': 'Reflejar para transferencia por sublimación',
    'Optional: mug/canteen curved adapter effect': 'Opcional: efecto curvo para adaptador de taza/cantimplora',
    'Adapter math': 'Cálculo del adaptador', 'Curve diameter': 'Diámetro de curva',
    'Add crop and registration marks': 'Añadir marcas de corte y registro',
    'Add badge cut-line outlines': 'Añadir contornos de corte de insignias',
    'Artwork colours': 'Colores del diseño', 'Original colours': 'Colores originales',
    'Replace colours with yellow & black': 'Sustituir colores por amarillo y negro',
    'Black only (for yellow shirts)': 'Solo negro (para camisetas amarillas)',
    'Ink contrast': 'Contraste de tinta',
    'Soft — more gray detail': 'Suave — más detalle en grises',
    'Balanced': 'Equilibrado', 'Strong': 'Fuerte',
    'High — sharper black areas': 'Alto — zonas negras más definidas',
    'Applies to black-only and yellow & black artwork.': 'Se aplica a diseños solo negros o amarillos y negros.',
    'Yellow shirt preview: the background represents the fabric and is not included in exports.': 'Vista previa de camiseta amarilla: el fondo representa la tela y no se incluye en las exportaciones.',
    'PNG export resolution': 'Resolución de exportación PNG',
    'More exports': 'Más exportaciones',
    'Preview template': 'Previsualizar plantilla', 'Download PDF': 'Descargar PDF',
    '← Adjust settings': '← Ajustar configuración', 'Preview': 'Vista previa',
    'Preview tools': 'Herramientas de vista previa', 'Zoom': 'Zoom', 'Snap to grid': 'Ajustar a la cuadrícula',
    'Grid step': 'Paso de cuadrícula', 'Snap to panel edges': 'Ajustar a los bordes del panel',
    'Edge tolerance': 'Tolerancia del borde', 'High-contrast outlines': 'Contornos de alto contraste',
    'Layout summary': 'Resumen de disposición', 'Manual placement': 'Colocación manual',
    'Reset automatic placement': 'Restablecer colocación automática', 'Apply manual layout': 'Aplicar disposición manual',
    'Inserted text position': 'Posición del texto insertado', 'Align left': 'Alinear a la izquierda',
    'Center horizontally': 'Centrar horizontalmente', 'Align right': 'Alinear a la derecha',
    'Align top': 'Alinear arriba', 'Center vertically': 'Centrar verticalmente', 'Align bottom': 'Alinear abajo',
    'Distribute horizontally': 'Distribuir horizontalmente', 'Distribute vertically': 'Distribuir verticalmente',
    'Download mirrored PDF': 'Descargar PDF reflejado',
    'Download proof PDF': 'Descargar PDF de prueba', 'Export SVG': 'Exportar SVG', 'Export PNG': 'Exportar PNG',
    'Artwork preflight': 'Comprobación previa del diseño', 'Review these artwork warnings before exporting:': 'Revisa estas advertencias del diseño antes de exportar:',
    'Lock': 'Bloquear', 'Keep position': 'Mantener posición', 'Re-run layout with locked badges': 'Reorganizar manteniendo las insignias bloqueadas',
    'Page': 'Página', 'Badge': 'Insignia', 'Width': 'Ancho', 'Height': 'Alto', 'Rotation': 'Rotación'
  };

  // Spanish is the default, while still honoring an explicit English choice
  // saved by a returning visitor.
  let language = localStorage.getItem('badgeware-language') === 'en' ? 'en' : 'es';
  const originals = new WeakMap();

  function translateText(node) {
    if (!originals.has(node)) originals.set(node, node.nodeValue);
    const original = originals.get(node);
    if (language === 'en') { node.nodeValue = original; return; }
    const trimmed = original.trim();
    if (!trimmed || !translations[trimmed]) return;
    node.nodeValue = original.replace(trimmed, translations[trimmed]);
  }

  function translateAttribute(element, attribute) {
    const key = `i18nOriginal${attribute.replace(/[^a-z]/gi, '')}`;
    if (!(key in element.dataset)) element.dataset[key] = element.getAttribute(attribute) || '';
    const original = element.dataset[key];
    element.setAttribute(attribute, language === 'es' && translations[original] ? translations[original] : original);
  }

  function applyLanguage() {
    document.documentElement.lang = language;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      if (!['SCRIPT', 'STYLE'].includes(walker.currentNode.parentElement?.tagName)) translateText(walker.currentNode);
    }
    document.querySelectorAll('[aria-label], [placeholder], [title]').forEach((element) => {
      ['aria-label', 'placeholder', 'title'].forEach((attribute) => {
        if (element.hasAttribute(attribute)) translateAttribute(element, attribute);
      });
    });
    document.querySelectorAll('[data-language-switch]').forEach((button) => {
      button.textContent = language === 'es' ? 'English' : 'Español';
      button.setAttribute('aria-label', language === 'es' ? 'Switch language to English' : 'Cambiar el idioma a español');
      button.setAttribute('aria-pressed', String(language === 'es'));
    });
  }

  document.addEventListener('click', (event) => {
    if (!event.target.closest('[data-language-switch]')) return;
    language = language === 'es' ? 'en' : 'es';
    localStorage.setItem('badgeware-language', language);
    applyLanguage();
  });
  applyLanguage();
})();
