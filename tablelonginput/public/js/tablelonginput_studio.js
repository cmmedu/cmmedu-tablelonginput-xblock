function TLIEditBlock(runtime, element, settings) {
    var $ = window.jQuery;
    settings = settings || {};
    var ui = settings.studio_ui || {};

    function escapeHtml(s) {
        if (s === undefined || s === null) {
            return '';
        }
        return $('<div/>').text(String(s)).html();
    }

    function normalizeColumnCount(value) {
        var columnasPorFila = parseInt(value, 10);
        if (isNaN(columnasPorFila) || columnasPorFila < 1) {
            return 2;
        }
        if (columnasPorFila > 3) {
            return 3;
        }
        return columnasPorFila;
    }

    function getMaxQuestionId() {
        var maxId = 0;
        $.each($(element).find('select[name=tipo_celda]'), function() {
            var curId = parseInt($(this).attr('pregunta-id'), 10);
            if (!isNaN(curId) && maxId < curId) {
                maxId = curId;
            }
        });
        return maxId;
    }

    function buildQuestionHtml(id) {
        var nuevaPregunta = '';
        nuevaPregunta += '<div class="tli-studio-cell div-pregunta-' + id + '">';
        nuevaPregunta += '<div class="wrapper-comp-setting">';
        nuevaPregunta += '<label class="label setting-label" for="tipo_celda">' + escapeHtml(ui.label_tipo_celda) + '</label>';
        nuevaPregunta += '<select class="input setting-input" name="tipo_celda" pregunta-id="' + id + '">';
        nuevaPregunta += '<option value="texto">' + escapeHtml(ui.opt_tipo_texto) + '</option>';
        nuevaPregunta += '<option value="input" selected>' + escapeHtml(ui.opt_tipo_input) + '</option>';
        nuevaPregunta += '</select>';
        nuevaPregunta += '</div>';
        nuevaPregunta += '<div class="wrapper-comp-setting cell-texto-field" pregunta-id="' + id + '">';
        nuevaPregunta += '<label class="label setting-label" for="texto_celda">' + escapeHtml(ui.label_texto_celda) + '</label>';
        nuevaPregunta += '<input class="input setting-input" name="texto_celda" pregunta-id="' + id + '" value="" type="text" />';
        nuevaPregunta += '</div>';
        nuevaPregunta += '<div class="wrapper-comp-setting cell-input-field" pregunta-id="' + id + '">';
        nuevaPregunta += '<label class="label setting-label" for="texto_input">' + escapeHtml(ui.label_texto_input) + '</label>';
        nuevaPregunta += '<input class="input setting-input" name="texto_input" pregunta-id="' + id + '" value="" type="text" />';
        nuevaPregunta += '</div>';
        nuevaPregunta += '<div class="wrapper-comp-setting cell-minimo-diferente-check-field" pregunta-id="' + id + '">';
        nuevaPregunta += '<label class="label setting-label" for="minimo_diferente_activo_' + id + '">';
        nuevaPregunta += '<input class="input setting-input" name="minimo_diferente_activo" id="minimo_diferente_activo_' + id + '" pregunta-id="' + id + '" type="checkbox" /> ' + escapeHtml(ui.label_minimo_diferente_activo);
        nuevaPregunta += '</label>';
        nuevaPregunta += '</div>';
        nuevaPregunta += '<div class="wrapper-comp-setting cell-minimo-diferente-value-field tli-setting-with-help" pregunta-id="' + id + '">';
        nuevaPregunta += '<div class="tli-setting-top-row">';
        nuevaPregunta += '<label class="label setting-label" for="minimo_diferente_' + id + '">' + escapeHtml(ui.label_minimo_diferente) + '</label>';
        nuevaPregunta += '<input class="input setting-input" name="minimo_diferente" id="minimo_diferente_' + id + '" pregunta-id="' + id + '" value="0" type="number" step="1" min="0" max="1000" />';
        nuevaPregunta += '</div>';
        nuevaPregunta += '<span class="help setting-help">' + escapeHtml(ui.help_minimo_diferente_cell) + '</span>';
        nuevaPregunta += '</div>';
        nuevaPregunta += '</div>';
        return nuevaPregunta;
    }

    function appendQuestionCell(id) {
        $(element).find('#listapreguntas').append(buildQuestionHtml(id));
    }

    function readHeaderCeldaValues() {
        var vals = {};
        $(element).find('.header-celda-input').each(function() {
            var col = $(this).data('col');
            vals[col] = $(this).val();
        });
        return vals;
    }

    function syncHeaderCellsToColumnCount(columnasPorFila) {
        var vals = readHeaderCeldaValues();
        var $container = $(element).find('#tli-studio-header-cells');
        if (!$container.length) {
            return;
        }
        $container.empty();
        for (var c = 0; c < columnasPorFila; c++) {
            var prev = vals[c] !== undefined && vals[c] !== null ? vals[c] : '';
            var $wrap = $('<div class="wrapper-comp-setting tli-studio-header-cell"></div>').attr('data-col', c);
            var $label = $('<label class="label setting-label"></label>').attr('for', 'header_celda_' + c);
            var prefix = ui.header_column_prefix || '';
            var suffix = ui.header_column_suffix_html || '';
            $label.text(prefix + ' ' + (c + 1) + suffix);
            var $inp = $('<input class="input setting-input header-celda-input" type="text" />')
                .attr('name', 'header_celda')
                .attr('id', 'header_celda_' + c)
                .attr('data-col', c)
                .val(prev);
            $wrap.append($label).append($inp);
            $container.append($wrap);
        }
    }

    function rebuildRowsLayout() {
        var columnasPorFila = normalizeColumnCount($(element).find('select.columnas_por_fila').val());
        var $listaPreguntas = $(element).find('#listapreguntas');
        var $headerRow = $listaPreguntas.children('.tli-studio-header-row').first().detach();
        var $celdas = $listaPreguntas.find('.tli-studio-cell').detach();

        $listaPreguntas.empty();
        if ($headerRow.length) {
            $listaPreguntas.append($headerRow);
            syncHeaderCellsToColumnCount(columnasPorFila);
        }
        for (var i = 0; i < $celdas.length; i += columnasPorFila) {
            var numeroFila = Math.floor(i / columnasPorFila) + 1;
            var $fila = $('<div class="tli-studio-row"></div>');
            var rowPrefix = ui.row_label_prefix || '';
            $fila.append($('<div class="tli-studio-row-title"></div>').text(rowPrefix + ' ' + numeroFila));

            for (var j = 0; j < columnasPorFila; j++) {
                var indiceCelda = i + j;
                if (indiceCelda < $celdas.length) {
                    $fila.append($celdas.eq(indiceCelda));
                }
            }

            var delPrefix = ui.btn_delete_row_prefix || '';
            var $actions = $('<div class="tli-studio-row-actions"></div>');
            var $delBtn = $('<a href="#" class="button action-primary borrar-fila-button"></a>');
            $delBtn.text(delPrefix + ' ' + numeroFila);
            $actions.append($delBtn);
            $fila.append($actions);
            $listaPreguntas.append($fila);
        }
    }

    function bindRowDeleteButtons() {
        $(element).find('.borrar-fila-button').off('click').on('click', function(eventObject) {
            eventObject.preventDefault();
            $(this).closest('.tli-studio-row').remove();
            rebuildRowsLayout();
            bindRowDeleteButtons();
        });
    }

    function syncVisibleCellsWithColumns() {
        var columnasPorFila = normalizeColumnCount($(element).find('select.columnas_por_fila').val());
        var totalCeldas = $(element).find('select[name=tipo_celda]').length;
        var faltantes = (columnasPorFila - (totalCeldas % columnasPorFila)) % columnasPorFila;
        if (faltantes === 0) {
            return;
        }
        var nextId = getMaxQuestionId() + 1;
        for (var i = 0; i < faltantes; i++) {
            appendQuestionCell(nextId + i);
        }
    }

    $(element).find('.save-button').bind('click', function(eventObject) {
        eventObject.preventDefault();
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

        var pregs = [];
        $.each($(element).find('select[name=tipo_celda]'), function() {
            var idpreg = $(this).attr('pregunta-id');
            var tipoCelda = $(this).val() || 'input';
            var textoCelda = $(element).find('input[name=texto_celda][pregunta-id="' + idpreg + '"]').val();
            var textoInput = $(element).find('input[name=texto_input][pregunta-id="' + idpreg + '"]').val();
            var minimoDiferenteActivo = $(element).find('input[name=minimo_diferente_activo][pregunta-id="' + idpreg + '"]').is(':checked');
            var minimoDiferente = $(element).find('input[name=minimo_diferente][pregunta-id="' + idpreg + '"]').val();
            var preg = {
                id: idpreg,
                tipo_celda: tipoCelda,
                texto_celda: textoCelda,
                texto_input: textoInput,
                minimo_diferente_activo: minimoDiferenteActivo,
                minimo_diferente: minimoDiferente
            };
            pregs.push(preg);
        });
        var columnasPorFilaSave = normalizeColumnCount(
            $(element).find('select.columnas_por_fila').val()
        );
        if (!pregs.length || pregs.length < columnasPorFilaSave) {
            window.alert(ui.save_incomplete_row_alert || '');
            return;
        }
        var headerCeldas = {};
        $(element).find('.header-celda-input').each(function() {
            var col = String($(this).data('col'));
            headerCeldas[col] = $(this).val();
        });
        var data = {
            display_name: $(element).find('input[name=display_name]').val(),
            texto_verdadero: $(element).find('input[name=texto_verdadero]').val(),
            texto_falso: $(element).find('input[name=texto_falso]').val(),
            texto_header_num: $(element).find('input[name=texto_header_num]').val(),
            weight: $(element).find('input[name=weight]').val(),
            nro_de_intentos: $(element).find('input[name=nro_de_intentos]').val(),
            area_height: $(element).find('input[name=area_height]').val(),
            min_caracter_input: $(element).find('input[name=min_caracter_input]').val(),
            color_de_celdas_completadas: $(element).find('input[name=color_de_celdas_completadas]').val(),
            numbering_type: $(element).find('select.numbering_type').val(),
            pretext_num: $(element).find('input[name=pretext_num]').val(),
            postext_num: $(element).find('input[name=postext_num]').val(),
            columnas_por_fila: $(element).find('select.columnas_por_fila').val(),
            mostrar_header_tabla: $(element).find('#mostrar_header_tabla').is(':checked'),
            header_celdas: headerCeldas,
            preguntas: pregs
        };
        if ($.isFunction(runtime.notify)) {
            runtime.notify('save', {state: 'start'});
        }
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response && response.result === 'error') {
                window.alert(response.message || ui.save_error_generic || '');
                return;
            }
            if ($.isFunction(runtime.notify)) {
                runtime.notify('save', {state: 'end'});
            }
        });
    });

    $(element).find('.cancel-button').bind('click', function(eventObject) {
        eventObject.preventDefault();
        runtime.notify('cancel', {});
    });

    $(element).find('.add-button').bind('click', function(eventObject) {
        eventObject.preventDefault();
        var max_id = getMaxQuestionId();
        var columnasPorFila = normalizeColumnCount($(element).find('select.columnas_por_fila').val());

        for (var i = 0; i < columnasPorFila; i++) {
            var nueva_id = max_id + 1 + i;
            appendQuestionCell(nueva_id);
        }
        rebuildRowsLayout();
        refreshCellTypeVisibility();
        bindRowDeleteButtons();
    });

    function setTliStudioFieldVisible($el, visible) {
        if (visible) {
            $el.removeClass('tli-studio-hidden');
            $el.css('display', '');
            $el.find('input, select, textarea').prop('disabled', false);
        } else {
            $el.addClass('tli-studio-hidden');
            $el.find('input, select, textarea').prop('disabled', true);
        }
    }

    function refreshCellTypeVisibility() {
        $(element).find('select[name=tipo_celda]').each(function() {
            var idpreg = $(this).attr('pregunta-id');
            var tipoCelda = $(this).val();
            var textoField = $(element).find('.cell-texto-field[pregunta-id="' + idpreg + '"]');
            var inputField = $(element).find('.cell-input-field[pregunta-id="' + idpreg + '"]');
            var minimoDiferenteCheckField = $(element).find('.cell-minimo-diferente-check-field[pregunta-id="' + idpreg + '"]');
            var minimoDiferenteValueField = $(element).find('.cell-minimo-diferente-value-field[pregunta-id="' + idpreg + '"]');
            var minimoDiferenteActivo = $(element).find('input[name=minimo_diferente_activo][pregunta-id="' + idpreg + '"]').is(':checked');
            if (tipoCelda === 'texto') {
                setTliStudioFieldVisible(textoField, true);
                setTliStudioFieldVisible(inputField, false);
                setTliStudioFieldVisible(minimoDiferenteCheckField, false);
                setTliStudioFieldVisible(minimoDiferenteValueField, false);
            } else {
                setTliStudioFieldVisible(textoField, false);
                setTliStudioFieldVisible(inputField, true);
                setTliStudioFieldVisible(minimoDiferenteCheckField, true);
                setTliStudioFieldVisible(minimoDiferenteValueField, !!minimoDiferenteActivo);
            }
        });
    }

    $(element).on('change', 'select[name=tipo_celda]', function() {
        refreshCellTypeVisibility();
    });
    $(element).on('change', 'input[name=minimo_diferente_activo]', function() {
        refreshCellTypeVisibility();
    });
    $(element).find('select.columnas_por_fila').on('change', function() {
        syncVisibleCellsWithColumns();
        rebuildRowsLayout();
        refreshCellTypeVisibility();
        bindRowDeleteButtons();
    });
    syncVisibleCellsWithColumns();
    rebuildRowsLayout();
    refreshCellTypeVisibility();
    bindRowDeleteButtons();
}
