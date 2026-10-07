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
    'Black only': 'Solo negro', 'Yellow & black': 'Amarillo y negro', 'No badges': 'Sin insignias',
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
    'Page': 'Página', 'Badge': 'Insignia', 'Width': 'Ancho', 'Height': 'Alto', 'Rotation': 'Rotación',
    'T-shirt sublimation badge templates': 'Plantillas de insignias para sublimación en camisetas',
    'Preview t-shirt template': 'Vista previa de la plantilla de camiseta',
    'Portrait': 'Vertical', 'Landscape': 'Horizontal', 'US Letter': 'Carta de EE. UU.',
    'Grid': 'Cuadrícula', 'Staggered rows': 'Filas alternadas', 'Diagonal sash': 'Banda diagonal',
    'Organic scatter': 'Distribución orgánica', 'Circle wreath': 'Corona circular',
    'Spiral trail': 'Espiral', 'Wave ribbon': 'Banda ondulada', 'Border frame': 'Marco de borde',
    'M pixel shape': 'Forma de M en píxeles', 'M pixel shape (no shrink)': 'Forma de M en píxeles (sin reducir)',
    'Selection order': 'Orden de selección', 'Alphabetical': 'Alfabético', 'By category': 'Por categoría',
    'Centimeters': 'Centímetros', 'Inches': 'Pulgadas', 'Uncategorized': 'Sin categoría',
    'Custom diameter': 'Diámetro personalizado', 'Standard mug': 'Taza estándar',
    'Skinny tumbler / canteen': 'Vaso o cantimplora estrechos', 'Wide canteen': 'Cantimplora ancha',
    'Ubuntu': 'Ubuntu', 'Fredoka One': 'Fredoka One', 'Helvetica': 'Helvetica',
    'Times': 'Times', 'Courier': 'Courier', 'DejaVu Sans': 'DejaVu Sans',
    '↕ Drag': '↕ Arrastrar', 'e.g. Ada': 'p. ej., Ada', 'e.g. MakeSpace Madrid': 'p. ej., MakeSpace Madrid',
    'Save the current badge assignments and print options as a reusable design template. Load a saved template to restore those choices before previewing or downloading a PDF.': 'Guarda la asignación de insignias y las opciones de impresión como una plantilla reutilizable. Carga una plantilla guardada para recuperar esas opciones antes de previsualizar o descargar un PDF.',
    'Badges are selected by default for both sides, except badge-template.png, which is only selected when you check it manually. Badges appear before template options so you can pick artwork first. Choose whether each badge prints on the front, back, or both; drag cards to set the initial order.': 'Las insignias se seleccionan por defecto para ambas caras, excepto badge-template.png, que requiere selección manual. Elige primero el diseño y después las opciones de plantilla. Asigna cada insignia al anverso, al reverso o a ambos; arrastra las tarjetas para establecer el orden inicial.',
    'Optional SVG, PNG, or JPG files are saved locally and included in this template.': 'Los archivos SVG, PNG o JPG opcionales se guardan localmente y se incluyen en esta plantilla.',
    'Start with page/layout basics, then only open the mug/canteen curve controls if you are printing for a curved heater adapter.': 'Empieza con la página y la disposición. Abre los controles de curva de taza o cantimplora si imprimes con un adaptador térmico curvo.',
    'Copy counts are limited to 1–24 to keep files practical.': 'Las copias se limitan a 1–24 para mantener un tamaño de archivo práctico.',
    'Badge size choices start at 2.5 cm / 1 in so generated badges stay printable and legible.': 'Los tamaños de insignia empiezan en 2,5 cm / 1 pulgada para que sean imprimibles y legibles.',
    'Practical gaps keep badges separable without wasting paper.': 'Un espaciado adecuado permite separar las insignias sin desperdiciar papel.',
    'Outer sheet margin in': 'Margen exterior de la hoja en',
    'Space between front/back panels in': 'Separación entre los paneles frontal y trasero en',
    'Optional name or short label printed on the front panel.': 'Nombre o etiqueta breve opcionales para el panel frontal.',
    'Optional name or short label printed on the back panel.': 'Nombre o etiqueta breve opcionales para el panel trasero.',
    'Font for front/back panel labels.': 'Fuente de las etiquetas de los paneles frontal y trasero.',
    'Panel label size in PDF points.': 'Tamaño de etiqueta del panel en puntos PDF.',
    'Check “Logo on front” below to add the MakeSpace logo to the front panel.': 'Marca «Logotipo en el anverso» para añadir el logotipo de MakeSpace al panel frontal.',
    'Logo size can differ from the front panel.': 'El tamaño del logotipo puede ser diferente al del panel frontal.',
    'Use this only for cylindrical blanks in a curved heater adapter. Pick a preset, then enter the measured outside diameter for the exact mug, canteen, or insert.': 'Úsalo solo para objetos cilíndricos en un adaptador térmico curvo. Elige un ajuste predefinido e introduce el diámetro exterior medido de la taza, cantimplora o inserto.',
    'Measured in': 'Medido en',
    'This is a guide for checking wrap width; still test with scrap paper before pressing.': 'Esta guía ayuda a comprobar el ancho de envoltura; prueba con papel antes de prensar.',
    'Circumference: about {amount} {unit}': 'Circunferencia: aproximadamente {amount} {unit}',
    'Enter a template name before saving this design.': 'Introduce un nombre de plantilla antes de guardar este diseño.',
    'Template could not be saved.': 'No se pudo guardar la plantilla.',
    'Choose a saved template to load.': 'Elige una plantilla guardada para cargarla.',
    'Template could not be loaded.': 'No se pudo cargar la plantilla.',
    'Choose a saved template to delete.': 'Elige una plantilla guardada para eliminarla.',
    'Template could not be deleted.': 'No se pudo eliminar la plantilla.',
    'Saved template “{name}”.': 'Plantilla «{name}» guardada.',
    'Loaded template “{name}”.': 'Plantilla «{name}» cargada.',
    'Deleted template “{name}”.': 'Plantilla «{name}» eliminada.',
    '{name} · {count} badge': '{name} · {count} insignia',
    '{name} · {count} badges': '{name} · {count} insignias',
    'Warning: front page has no badges.': 'Aviso: el anverso no tiene insignias.',
    'Warning: back page has no badges.': 'Aviso: el reverso no tiene insignias.',
    'Warning: front page has no badges and back page has no badges.': 'Aviso: el anverso y el reverso no tienen insignias.',
    'Preview ready. Ctrl/Shift-click badges to multi-select, then drag or nudge them together.': 'Vista previa lista. Pulsa Ctrl o Mayús y haz clic para seleccionar varias insignias; después arrástralas o muévelas juntas.',
    'Manual placement shortcuts': 'Atajos de colocación manual', 'Manual text placement': 'Colocación manual del texto',
    'Drag one badge or Ctrl/Shift-click multiple badges to move them together. Use arrow keys to nudge the focused badge or selected group (Shift = larger step), type X/Y/rotation values, or use the reset, alignment, distribution, and rotation preset controls.': 'Arrastra una insignia o pulsa Ctrl o Mayús y haz clic para seleccionar varias y moverlas juntas. Usa las flechas para desplazar la insignia enfocada o el grupo seleccionado (Mayús aumenta el paso), introduce X/Y/giro o usa los controles de restablecimiento, alineación, distribución y giro.',
    'Drag inserted front/back text in the preview, or type coordinates here.': 'Arrastra el texto del anverso o del reverso en la vista previa o introduce aquí las coordenadas.',
    'No badges selected for group movement.': 'No hay insignias seleccionadas para mover en grupo.',
    'Need at least two selected badges, or two badges in a panel, to distribute.': 'Selecciona al menos dos insignias o coloca dos en un panel para distribuirlas.',
    'No badge overlaps detected.': 'No se han detectado insignias superpuestas.',
    'Manual edits reset to the automatic layout.': 'Se han restablecido los cambios manuales a la disposición automática.',
    'Select a badge before applying a rotation preset.': 'Selecciona una insignia antes de aplicar un giro predefinido.',
    'High-contrast preview outlines enabled.': 'Contornos de alto contraste activados en la vista previa.',
    'High-contrast preview outlines disabled.': 'Contornos de alto contraste desactivados en la vista previa.',
    '{count} badges overlap. Move highlighted badges before printing.': '{count} insignias se superponen. Mueve las insignias resaltadas antes de imprimir.',
    'Applied {rotation}° rotation preset.': 'Giro predefinido de {rotation}° aplicado.',
    '{count} badge selected for group movement.': '{count} insignia seleccionada para mover en grupo.',
    '{count} badges selected for group movement.': '{count} insignias seleccionadas para mover en grupo.',
    '{count} badge moved. Coordinates updated below.': '{count} insignia movida. Las coordenadas se han actualizado abajo.',
    '{count} badges moved. Coordinates updated below.': '{count} insignias movidas. Las coordenadas se han actualizado abajo.',
    '{count} badge nudged with keyboard.': '{count} insignia desplazada con el teclado.',
    '{count} badges nudged with keyboard.': '{count} insignias desplazadas con el teclado.',
    '{side} text nudged with keyboard.': 'Texto del {side} desplazado con el teclado.',
    '{side} text moved. Coordinates updated below.': 'Texto del {side} movido. Las coordenadas se han actualizado abajo.',
    'Move {name}': 'Mover {name}', 'Choose print sides for {name}': 'Elige las caras de impresión para {name}',
    'Rotate {rotation}°': 'Girar {rotation}°',
    'Front text X': 'Texto del anverso X', 'Front text Y': 'Texto del anverso Y',
    'Back text X': 'Texto del reverso X', 'Back text Y': 'Texto del reverso Y',
    'FRONT': 'ANVERSO', 'BACK': 'REVERSO',
    'Your current design': 'Tu diseño actual', 'New design': 'Nuevo diseño',
    'Start blank': 'Empezar en blanco', 'Continue draft': 'Continuar borrador',
    'Recover draft': 'Recuperar borrador', 'Restore draft': 'Restaurar borrador',
    'Load a design': 'Cargar un diseño', 'Save finished design': 'Guardar diseño terminado',
    'Changes are saved in this browser tab as you work.': 'Los cambios se guardan en esta pestaña mientras trabajas.',
    "Discard this tab's draft and start a new design?": '¿Descartar el borrador de esta pestaña y empezar un diseño nuevo?',
    'Keep current design': 'Mantener diseño actual', 'Cancel': 'Cancelar',
    'Replace saved design': 'Reemplazar diseño guardado', 'Replace design': 'Reemplazar diseño',
    'Undo delete': 'Deshacer eliminación', 'Undo deletion': 'Deshacer eliminación',
    'Starting style': 'Estilo inicial', 'Starting presets': 'Ajustes iniciales',
    'Original-colour artwork': 'Diseño con colores originales',
    'Black artwork for yellow fabric': 'Diseño negro para tela amarilla',
    'Black and yellow artwork': 'Diseño negro y amarillo',
    'Styles change artwork colours and set balanced contrast. Check the mirror setting for your transfer method.': 'Los estilos cambian los colores del diseño y equilibran el contraste. Comprueba el ajuste de reflejo para tu método de transferencia.',
    'Advanced settings': 'Ajustes avanzados', 'Advanced placement controls': 'Controles avanzados de colocación',
    'Print marks': 'Marcas de impresión', 'Fine adjustments': 'Ajustes finos',
    'Mirroring depends on your transfer method. Proof exports are always unmirrored.': 'El reflejo depende del método de transferencia. Las exportaciones de prueba nunca se reflejan.',
    'Undo': 'Deshacer', 'Redo': 'Rehacer', 'Previous edit': 'Cambio anterior', 'Next edit': 'Cambio siguiente',
    'Compare original artwork': 'Comparar diseño original', 'Show original artwork': 'Mostrar diseño original',
    'Guides and selection outlines are preview-only. Colour changes keep your placement.': 'Las guías y los contornos de selección solo aparecen en la vista previa. Cambiar los colores conserva la colocación.',
    'Select a badge to move or rotate it.': 'Selecciona una insignia para moverla o girarla.',
    'Selected artwork': 'Diseño seleccionado', 'Selection tools': 'Herramientas de selección',
    'Move left': 'Mover a la izquierda', 'Move right': 'Mover a la derecha',
    'Move up': 'Mover arriba', 'Move down': 'Mover abajo', 'Select all badges': 'Seleccionar todas las insignias',
    'Clear selection': 'Quitar selección', 'Lock selected': 'Bloquear selección', 'Unlock selected': 'Desbloquear selección',
    'Output summary': 'Resumen de salida', 'Print summary': 'Resumen de impresión', 'Print readiness': 'Estado de impresión',
    'Print at actual size (100%), not “fit to page”.': 'Imprime al tamaño real (100 %), sin «ajustar a la página».',
    'Proof PDF is an unmirrored check of your design.': 'El PDF de prueba muestra tu diseño sin reflejarlo.',
    'Mirrored': 'Reflejado', 'Not mirrored': 'Sin reflejar', 'Mirror on': 'Reflejo activado', 'Mirror off': 'Reflejo desactivado',
    'Printing warnings': 'Avisos de impresión', 'Layout warnings': 'Avisos de disposición',
    'Generating download…': 'Generando descarga…', 'Generating file…': 'Generando archivo…',
    'Download started.': 'Descarga iniciada.', 'Retry download': 'Reintentar descarga', 'Retry': 'Reintentar',
    'Your edits are preserved. Try again.': 'Tus cambios se conservan. Inténtalo de nuevo.',
    'More than half of the artwork is transparent; verify its visible print area.': 'Más de la mitad del diseño es transparente; comprueba el área visible de impresión.',
    'Artwork could not be loaded.': 'No se pudo cargar el diseño.',
    'Effective resolution is about {dpi} DPI; 150 DPI or more is recommended.': 'La resolución efectiva es de unos {dpi} PPP; se recomiendan al menos 150 PPP.',
    'Start new design': 'Empezar diseño nuevo',
    'Remove missing artwork from this design': 'Quitar de este diseño las imágenes que faltan',
    'Move badge earlier': 'Adelantar insignia', 'Move badge later': 'Retrasar insignia',
    'Choose a starting style': 'Elige un estilo inicial',
    'Black artwork for a yellow shirt': 'Diseño negro para una camiseta amarilla',
    'Yellow & black artwork': 'Diseño amarillo y negro',
    'Advanced spacing and margins': 'Espaciado y márgenes avanzados',
    'Advanced print options': 'Opciones avanzadas de impresión',
    'Draft saved in this browser tab.': 'Borrador guardado en esta pestaña.',
    'Browser storage is unavailable. Save a named design before leaving this page.': 'El almacenamiento del navegador no está disponible. Guarda el diseño con un nombre antes de salir de esta página.',
    'Missing artwork: {names}. Upload it again or remove it from this design.': 'Faltan imágenes: {names}. Vuelve a subirlas o quítalas de este diseño.',
    'Template could not be saved. Check your connection and try again.': 'No se pudo guardar la plantilla. Comprueba la conexión e inténtalo de nuevo.',
    'Template could not be loaded. Check your connection and try again.': 'No se pudo cargar la plantilla. Comprueba la conexión e inténtalo de nuevo.',
    'Template could not be deleted. Check your connection and try again.': 'No se pudo eliminar la plantilla. Comprueba la conexión e inténtalo de nuevo.',
    'Template could not be restored. Check your connection and try again.': 'No se pudo restaurar la plantilla. Comprueba la conexión e inténtalo de nuevo.',
    'Restored template “{name}”.': 'Plantilla «{name}» restaurada.',
    'Deleted template “{name}”. You can undo this deletion.': 'Plantilla «{name}» eliminada. Puedes deshacer esta eliminación.',
    'A design named “{name}” already exists. Replace it with the current design?': 'Ya existe un diseño llamado «{name}». ¿Reemplazarlo por el diseño actual?',
    'A design with this name already exists. Undo has kept your deleted design available; choose another name to restore it.': 'Ya existe un diseño con este nombre. El diseño eliminado sigue disponible para recuperarlo; elige otro nombre para restaurarlo.',
    'Style applied: {style}; balanced contrast. Your mirror setting is unchanged.': 'Estilo aplicado: {style}; contraste equilibrado. Se mantiene el ajuste de reflejo.',
    'Draft restored. Uploaded file contents must be selected again before uploading.': 'Borrador restaurado. Para subir archivos, debes volver a seleccionarlos.',
    'Blank design started. Select badges or add a logo or text.': 'Diseño en blanco iniciado. Selecciona insignias o añade un logotipo o texto.',
    'New design started.': 'Diseño nuevo iniciado.',
    'Choose at least one panel to preview your design.': 'Elige al menos un panel para previsualizar el diseño.',
    'No badges selected. Choose artwork or add a logo or text to get started.': 'No hay insignias seleccionadas. Elige imágenes o añade un logotipo o texto para empezar.',
    'The front panel has no badges. Choose artwork or add a logo or text.': 'El panel frontal no tiene insignias. Elige imágenes o añade un logotipo o texto.',
    'The back panel has no badges. Choose artwork or add a logo or text.': 'El panel trasero no tiene insignias. Elige imágenes o añade un logotipo o texto.',
    'Check before printing': 'Comprueba antes de imprimir', 'Edit artwork': 'Editar diseño',
    'Compare original artwork (preview only)': 'Comparar diseño original (solo vista previa)',
    'Jump to page': 'Ir a la página', 'Selected badge controls': 'Controles de la insignia seleccionada',
    'Review print settings and export': 'Revisar ajustes de impresión y descargar',
    'SVG and PNG export unmirrored artwork pages in one contact sheet. Use PDF for transfer print settings.': 'SVG y PNG exportan las páginas sin reflejar en una sola hoja de contacto. Usa PDF para los ajustes de impresión por transferencia.',
    'Lock position': 'Bloquear posición', 'Unlock position': 'Desbloquear posición',
    'Advanced placement and text controls': 'Controles avanzados de colocación y texto',
    'Pages': 'Páginas', 'On — mirrored transfer': 'Activado — transferencia reflejada',
    'Off — unmirrored output': 'Desactivado — salida sin reflejar',
    'Print at actual size (100%). Do not use “fit to page”.': 'Imprime al tamaño real (100 %). No uses «ajustar a la página».',
    'Proof PDF is an unmirrored check of the design. Transfer mirroring depends on your printing method.': 'El PDF de prueba permite revisar el diseño sin reflejar. El reflejo de la transferencia depende del método de impresión.',
    'Save artwork order, settings, positions, text and locks for later.': 'Guarda el orden de las imágenes, los ajustes, las posiciones, el texto y los bloqueos para más adelante.',
    'Design name': 'Nombre del diseño',
    'Replace an existing design with this name': 'Reemplazar un diseño existente con este nombre',
    '{count} selected: {names}': '{count} seleccionadas: {names}',
    '{name}, position locked': '{name}, posición bloqueada',
    '{name} · {side}': '{name} · {side}',
    'Alignment applied to {count} badges.': 'Alineación aplicada a {count} insignias.',
    '{count} badges may overlap. Check highlighted artwork before printing.': '{count} insignias podrían superponerse. Comprueba las imágenes resaltadas antes de imprimir.',
    'Some artwork could not load. Re-upload missing files or check the source before exporting.': 'No se pudieron cargar algunas imágenes. Vuelve a subir los archivos que faltan o comprueba su origen antes de exportar.',
    'Text position updated.': 'Posición del texto actualizada.',
    'Unlock the badge before moving it.': 'Desbloquea la insignia antes de moverla.',
    '{count} badges moved. Coordinates updated.': '{count} insignias movidas. Coordenadas actualizadas.',
    'Edit undone.': 'Cambio deshecho.', 'Edit restored.': 'Cambio restaurado.',
    'Artwork colours updated. Placements preserved.': 'Colores del diseño actualizados. Se conserva la colocación.',
    'Showing original artwork for comparison. Exports keep your chosen colours.': 'Se muestra el diseño original para comparar. Las exportaciones mantienen los colores elegidos.',
    'Showing the colours used in exports.': 'Se muestran los colores de las exportaciones.',
    'Selected positions locked.': 'Posiciones seleccionadas bloqueadas.',
    'Selected positions unlocked.': 'Posiciones seleccionadas desbloqueadas.', 'Text updated.': 'Texto actualizado.',
    'Enter a design name using letters, numbers, hyphens or underscores.': 'Introduce un nombre de diseño con letras, números, guiones o guiones bajos.',
    'Saving design…': 'Guardando diseño…',
    'This name already exists. Choose another name or enable replacement.': 'Este nombre ya existe. Elige otro nombre o activa el reemplazo.',
    'Design could not be saved. Check the name and try again.': 'No se pudo guardar el diseño. Comprueba el nombre e inténtalo de nuevo.',
    'Saved design “{name}”, including your manual edits.': 'Diseño «{name}» guardado con los cambios manuales.',
    'Design could not be saved. Check your connection and try again.': 'No se pudo guardar el diseño. Comprueba la conexión e inténtalo de nuevo.',
    'Generating your download…': 'Generando tu descarga…',
    'Download could not be generated. Please try again.': 'No se pudo generar la descarga. Inténtalo de nuevo.',
    'Artwork could not be loaded: {names}. Check the affected badges and retry.': 'No se pudieron cargar las imágenes: {names}. Comprueba las insignias afectadas e inténtalo de nuevo.',
    'The server returned an unexpected download. Please retry.': 'El servidor devolvió una descarga inesperada. Inténtalo de nuevo.',
    'Download started. Check your browser’s downloads.': 'Descarga iniciada. Consulta las descargas del navegador.',
    'This download took too long. Your design is kept; try again.': 'La descarga tardó demasiado. Tu diseño se conserva; inténtalo de nuevo.',
    'Connection failed. Your design is kept; try again.': 'Error de conexión. Tu diseño se conserva; inténtalo de nuevo.',
    'Draft restored. Your selections and layout are ready.': 'Borrador restaurado. La selección y la disposición están listas.',
    'Use letters, numbers, dots, dashes, or underscores.': 'Usa letras, números, puntos, guiones o guiones bajos.',
    'Template name must use letters, numbers, dots, dashes, or underscores.': 'El nombre de la plantilla debe contener letras, números, puntos, guiones o guiones bajos.',
    'saved': 'guardadas', 'Curve adapter help': 'Ayuda del adaptador curvo',
    'Applies only to PNG exports.': 'Se aplica solo a las exportaciones PNG.', 'Panel': 'Panel',
    'Artwork is unavailable. Restore the upload or remove this badge from the design.': 'La imagen no está disponible. Vuelve a subirla o quita esta insignia del diseño.',
    'Some selected artwork is unavailable. Restore it or remove it from the design before exporting.': 'Algunas imágenes seleccionadas no están disponibles. Recupéralas o quítalas del diseño antes de exportar.',
    'A saved design already uses this name. Choose a new name or explicitly replace it.': 'Ya existe un diseño guardado con este nombre. Elige un nombre nuevo o indica que quieres reemplazarlo.'
  };


  // Language preferences also work when browser privacy settings block storage.
  let language = 'es';
  try {
    if (window.localStorage.getItem('badgeware-language') === 'en') language = 'en';
  } catch (error) { /* Keep the default when storage is unavailable. */ }
  const originals = new WeakMap();
  const attributes = new WeakMap();
  const messages = new Map();
  const ignored = 'script, style, noscript, textarea, [data-i18n-ignore], .panel-custom-text, .badge-card > strong, .badge-card > small, .badge-card .thumb img, .draggable-badge > title, .artwork-warning-link';

  function interpolate(template, params) {
    const values = typeof params === 'function' ? params() : params || {};
    return template.replace(/\{([\w]+)\}/g, (placeholder, name) => {
      if (!Object.prototype.hasOwnProperty.call(values, name)) return placeholder;
      const value = values[name];
      // A deferred translation keeps side/option names in the chosen language
      // when a previously displayed status is refreshed after a language switch.
      if (value && typeof value === 'object' && typeof value.key === 'string') return t(value.key, value.params);
      return value == null ? '' : String(value);
    });
  }

  function t(key, params) {
    const source = String(key || '');
    return interpolate(language === 'es' ? translations[source] || source : source, params);
  }

  // These patterns cover server-rendered descriptions and legacy text updates.
  // User-provided names remain parameters and are never treated as markup.
  const patterns = [
    [/^Circumference: about (.+) (cm|in)$/, (amount, unit) => t('Circumference: about {amount} {unit}', { amount, unit })],
    [/^(Saved|Loaded|Deleted) template “(.+)”\.$/, (verb, name) => t(`${verb} template “{name}”.`, { name })],
    [/^(.+) · (\d+) badge(s?)$/, (name, count, plural) => t(`{name} · {count} badge${plural}`, { name, count })],
    [/^(\d+) badges overlap\. Move highlighted badges before printing\.$/, (count) => t('{count} badges overlap. Move highlighted badges before printing.', { count })],
    [/^(\d+) badge(s?) selected for group movement\.$/, (count, plural) => t(`{count} badge${plural} selected for group movement.`, { count })],
    [/^(\d+) badge(s?) moved\. Coordinates updated below\.$/, (count, plural) => t(`{count} badge${plural} moved. Coordinates updated below.`, { count })],
    [/^(\d+) badge(s?) nudged with keyboard\.$/, (count, plural) => t(`{count} badge${plural} nudged with keyboard.`, { count })],
    [/^(front|back) text nudged with keyboard\.$/, (side) => t('{side} text nudged with keyboard.', { side: { key: side } })],
    [/^(front|back) text moved\. Coordinates updated below\.$/, (side) => t('{side} text moved. Coordinates updated below.', { side: { key: side } })],
    [/^Applied (-?[\d.]+)° rotation preset\.$/, (rotation) => t('Applied {rotation}° rotation preset.', { rotation })],
    [/^Rotate (-?[\d.]+)°$/, (rotation) => t('Rotate {rotation}°', { rotation })],
    [/^Choose print sides for (.+)$/, (name) => t('Choose print sides for {name}', { name })],
    [/^Move (front|back) text$/, (side) => language === 'es' ? `Mover texto del ${t(side)}` : `Move ${side} text`],
    [/^Effective resolution is about (\d+) DPI; 150 DPI or more is recommended\.$/, (dpi) => t('Effective resolution is about {dpi} DPI; 150 DPI or more is recommended.', { dpi })],
    [/^Page (\d+) · (Front|Back)$/, (number, side) => language === 'es' ? `Página ${number} · ${t(side)}` : `Page ${number} · ${side}`],
    [/^(Front|Back) · (\d+)$/, (side, number) => language === 'es' ? `${t(side)} · ${number}` : `${side} · ${number}`],
    [/^(\d+) · (Front|Back)(, (Front|Back))?$/, (count, side, separator, otherSide) => language === 'es' ? `${count} · ${t(side)}${otherSide ? `, ${t(otherSide)}` : ''}` : `${count} · ${side}${otherSide ? `, ${otherSide}` : ''}`],
    [/^(A4|A3|LETTER) · (Portrait|Landscape) · (.+)$/, (size, orientation, dimensions) => language === 'es' ? `${size === 'LETTER' ? t('US Letter') : size} · ${t(orientation)} · ${dimensions}` : `${size} · ${orientation} · ${dimensions}`],
    [/^(\d+) PDF page\(s\)$/, (count) => language === 'es' ? `${count} página(s) PDF` : `${count} PDF page(s)`],
    [/^(\d+) placement\(s\)\.$/, (count) => language === 'es' ? `${count} colocación(es).` : `${count} placement(s).`],
    [/^(Front|Back) page:$/, (side) => language === 'es' ? `${t(side)}:` : `${side} page:`],
    [/^PDF template preview - (Front|Back) page$/, (side) => language === 'es' ? `Vista previa de plantilla PDF: ${t(side)}` : `PDF template preview - ${side} page`],
    [/^(Front|Back) page with (\d+) badge placement\(s\)\. Detailed placement coordinates are listed in the layout summary after the preview\.$/, (side, count) => language === 'es' ? `${t(side)} con ${count} colocación(es) de insignias. Las coordenadas se muestran en el resumen de disposición después de la vista previa.` : `${side} page with ${count} badge placement(s). Detailed placement coordinates are listed in the layout summary after the preview.`],
    [/^(\d+) selected badges laid out across (\d+) PDF page\(s\)\. Drag badges on each page or edit their coordinates below before downloading\.$/, (count, pages) => language === 'es' ? `${count} insignias seleccionadas en ${pages} página(s) PDF. Arrastra las insignias o edita sus coordenadas antes de descargar.` : `${count} selected badges laid out across ${pages} PDF page(s). Drag badges on each page or edit their coordinates below before downloading.`],
    [/^Coordinates use (cm|in) from the page’s top-left corner\.$/, (unit) => language === 'es' ? `Coordenadas en ${unit} desde la esquina superior izquierda de la página.` : `Coordinates use ${unit} from the page’s top-left corner.`],
    [/^Text alternative for the generated preview\. Each side is exported as its own PDF page; coordinates use (cm|in) from that page’s top-left corner\.$/, (unit) => language === 'es' ? `Descripción de la vista previa. Cada cara se exporta en una página PDF; las coordenadas están en ${unit} desde su esquina superior izquierda.` : `Text alternative for the generated preview. Each side is exported as its own PDF page; coordinates use ${unit} from that page’s top-left corner.`],
    [/^Move buttons nudge by 0\.1 (cm|in)\. Locked badges stay fixed during edits and layout changes\.$/, (unit) => language === 'es' ? `Los botones desplazan 0,1 ${unit}. Las insignias bloqueadas mantienen su posición durante los cambios.` : `Move buttons nudge by 0.1 ${unit}. Locked badges stay fixed during edits and layout changes.`],
    [/^(Grid|Rows|Diagonal|Scatter|Circle|Spiral|Wave|Border|M-Pixels|M-Pixels-No-Shrink) placement$/, (mode) => {
      const labels = { Rows: 'Staggered rows', Diagonal: 'Diagonal sash', Scatter: 'Organic scatter', Circle: 'Circle wreath', Spiral: 'Spiral trail', Wave: 'Wave ribbon', Border: 'Border frame', 'M-Pixels': 'M pixel shape', 'M-Pixels-No-Shrink': 'M pixel shape (no shrink)' };
      return language === 'es' ? `Colocación: ${t(labels[mode] || mode)}` : `${mode} placement`;
    }],
    [/^(150|300|600) DPI$/, (dpi) => language === 'es' ? `${dpi} PPP` : `${dpi} DPI`],
    [/^(\d+) image assets$/, (count) => language === 'es' ? `${count} imágenes` : `${count} image assets`],
    [/^(.+) on (Front|Back) at X (-?[\d.]+), Y (-?[\d.]+), rotation (-?[\d.]+)°\.$/, (name, side, x, y, rotation) => language === 'es' ? `${name} en ${t(side)}: X ${x}, Y ${y}, giro ${rotation}°.` : `${name} on ${side} at X ${x}, Y ${y}, rotation ${rotation}°.`],
    [/^Move (.+)$/, (name) => t('Move {name}', { name })],
  ];

  function translatedSource(source) {
    if (language === 'en') return source;
    const trimmed = source.trim();
    if (!trimmed) return source;
    // A server warning follows a separate <strong> containing the artwork
    // name, so its text node starts with the punctuation between the two.
    if (trimmed.startsWith(': ')) return source.replace(trimmed, `: ${translatedSource(trimmed.slice(2))}`);
    let translated = translations[trimmed];
    if (translated === undefined) {
      for (const [pattern, render] of patterns) {
        const match = trimmed.match(pattern);
        if (match) { translated = render(...match.slice(1)); break; }
      }
    }
    return translated === undefined ? source : source.replace(trimmed, translated);
  }

  function managedAncestor(element) {
    while (element) {
      if (messages.has(element)) return element;
      element = element.parentElement;
    }
    return null;
  }

  function translateText(node) {
    const element = node.parentElement;
    if (!element || element.closest(ignored) || element.closest('[data-language-switch]') || managedAncestor(element)) return;
    let record = originals.get(node);
    // Re-read the English source after application code changes an existing
    // text node; toggling languages must never restore an older status.
    if (!record || node.nodeValue !== record.rendered) record = { source: node.nodeValue, rendered: node.nodeValue };
    const rendered = translatedSource(record.source);
    if (node.nodeValue !== rendered) node.nodeValue = rendered;
    record.rendered = rendered;
    originals.set(node, record);
  }

  function translateAttribute(element, attribute) {
    if (element.closest(ignored) || element.matches('[data-language-switch]')) return;
    let elementRecords = attributes.get(element);
    if (!elementRecords) { elementRecords = {}; attributes.set(element, elementRecords); }
    const current = element.getAttribute(attribute);
    if (current === null) return;
    let record = elementRecords[attribute];
    if (!record || current !== record.rendered) record = { source: current, rendered: current };
    const rendered = translatedSource(record.source);
    if (current !== rendered) element.setAttribute(attribute, rendered);
    record.rendered = rendered;
    elementRecords[attribute] = record;
  }

  function renderMessage(element, record) {
    const rendered = t(record.key, record.params);
    if (element.textContent !== rendered) element.textContent = rendered;
    record.rendered = rendered;
  }

  function message(element, key, params) {
    if (!element) return;
    const record = { key, params };
    messages.set(element, record);
    renderMessage(element, record);
    return record.rendered;
  }

  function translateTree(root) {
    if (root.nodeType === Node.TEXT_NODE) { translateText(root); return; }
    if (![Node.ELEMENT_NODE, Node.DOCUMENT_FRAGMENT_NODE].includes(root.nodeType)) return;
    if (root.nodeType === Node.ELEMENT_NODE && root.closest(ignored)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) translateText(walker.currentNode);
    const elements = root.querySelectorAll('[aria-label], [placeholder], [title], [alt]');
    const targets = root.nodeType === Node.ELEMENT_NODE ? [root, ...elements] : elements;
    targets.forEach((element) => {
      ['aria-label', 'placeholder', 'title', 'alt'].forEach((attribute) => {
        if (element.hasAttribute(attribute)) translateAttribute(element, attribute);
      });
    });
  }

  function refresh() {
    document.documentElement.lang = language;
    messages.forEach((record, element) => {
      if (!element.isConnected) { messages.delete(element); return; }
      renderMessage(element, record);
    });
    if (document.body) translateTree(document.body);
    const pageTitle = document.querySelector('head > title');
    if (pageTitle) translateTree(pageTitle);
    document.querySelectorAll('[data-language-switch]').forEach((button) => {
      const label = language === 'es' ? 'English' : 'Español';
      if (button.textContent !== label) button.textContent = label;
      button.setAttribute('aria-label', language === 'es' ? 'Switch language to English' : 'Cambiar el idioma a español');
      button.setAttribute('aria-pressed', String(language === 'es'));
    });
  }

  window.BadgewareI18n = { t, message, refresh, get language() { return language; } };
  document.addEventListener('click', (event) => {
    if (!event.target.closest?.('[data-language-switch]')) return;
    language = language === 'es' ? 'en' : 'es';
    try { window.localStorage.setItem('badgeware-language', language); } catch (error) { /* Translation does not require storage. */ }
    refresh();
    document.dispatchEvent(new CustomEvent('badgeware:languagechange', { detail: { language } }));
  });

  function initialize() {
    refresh();
    const observer = new MutationObserver((changes) => {
      changes.forEach((change) => {
        const element = change.target.nodeType === Node.ELEMENT_NODE ? change.target : change.target.parentElement;
        const managed = managedAncestor(element);
        if (managed) {
          const record = messages.get(managed);
          if (managed.textContent === record.rendered) return;
          // A direct external update replaces the previously keyed message.
          messages.delete(managed);
        }
        if (change.type === 'attributes') translateAttribute(change.target, change.attributeName);
        else if (change.type === 'characterData') translateText(change.target);
        else change.addedNodes.forEach(translateTree);
      });
    });
    observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['aria-label', 'placeholder', 'title', 'alt'] });
  }
  if (document.body) initialize();
  else document.addEventListener('DOMContentLoaded', initialize, { once: true });
})();
