function TLIEditBlock(runtime, element) {
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
      nuevaPregunta += '<div class="tli-studio-cell div-pregunta-'+id+'">';
      nuevaPregunta += '<div class="wrapper-comp-setting">';
      nuevaPregunta += '<label class="label setting-label" for="tipo_celda">Tipo de celda</label>';
      nuevaPregunta += '<select class="input setting-input" name="tipo_celda" pregunta-id="'+id+'">';
      nuevaPregunta += '<option value="texto">Texto</option>';
      nuevaPregunta += '<option value="input" selected>Input</option>';
      nuevaPregunta += '</select>';
      nuevaPregunta += '</div>';
      nuevaPregunta += '<div class="wrapper-comp-setting cell-texto-field" pregunta-id="'+id+'">';
      nuevaPregunta += '<label class="label setting-label" for="texto_celda">Texto (admite HTML)</label>';
      nuevaPregunta += '<input class="input setting-input" name="texto_celda" pregunta-id="'+id+'" value="" type="text" />';
      nuevaPregunta += '</div>';
      nuevaPregunta += '<div class="wrapper-comp-setting cell-input-field" pregunta-id="'+id+'">';
      nuevaPregunta += '<label class="label setting-label" for="texto_input">Texto antes del input (opcional, admite HTML)</label>';
      nuevaPregunta += '<input class="input setting-input" name="texto_input" pregunta-id="'+id+'" value="" type="text" />';
      nuevaPregunta += '</div>';
      nuevaPregunta += '<div class="wrapper-comp-setting cell-required-field" pregunta-id="'+id+'">';
      nuevaPregunta += '<label class="label setting-label" for="obligatoria_'+id+'">';
      nuevaPregunta += '<input class="input setting-input" name="obligatoria" id="obligatoria_'+id+'" pregunta-id="'+id+'" type="checkbox" /> Obligatoria';
      nuevaPregunta += '</label>';
      nuevaPregunta += '</div>';
      nuevaPregunta += '</div>';
      return nuevaPregunta;
    }

    function appendQuestionCell(id) {
      $(element).find('#listapreguntas').append(buildQuestionHtml(id));
    }

    function rebuildRowsLayout() {
      var columnasPorFila = normalizeColumnCount($(element).find('select.columnas_por_fila').val());
      var $listaPreguntas = $(element).find('#listapreguntas');
      var $celdas = $listaPreguntas.find('.tli-studio-cell').detach();

      $listaPreguntas.empty();
      for (var i = 0; i < $celdas.length; i += columnasPorFila) {
        var numeroFila = Math.floor(i / columnasPorFila) + 1;
        var $fila = $('<div class="tli-studio-row"></div>');
        $fila.append('<div class="tli-studio-row-title">Fila ' + numeroFila + '</div>');

        for (var j = 0; j < columnasPorFila; j++) {
          var indiceCelda = i + j;
          if (indiceCelda < $celdas.length) {
            $fila.append($celdas.eq(indiceCelda));
          }
        }

        $fila.append(
          '<div class="tli-studio-row-actions"><a href="#" class="button action-primary borrar-fila-button">Eliminar Fila ' + numeroFila + '</a></div>'
        );
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

      //obtengo preguntas y su valor
      var pregs = [];
      $.each($(element).find('select[name=tipo_celda]'), function() {
        var idpreg = $(this).attr('pregunta-id');
        var tipoCelda = $(this).val() || 'input';
        var textoCelda = $(element).find('input[name=texto_celda][pregunta-id="' + idpreg + '"]').val();
        var textoInput = $(element).find('input[name=texto_input][pregunta-id="' + idpreg + '"]').val();
        var obligatoria = $(element).find('input[name=obligatoria][pregunta-id="' + idpreg + '"]').is(':checked');
        var preg = {
          id: idpreg,
          tipo_celda: tipoCelda,
          texto_celda: textoCelda,
          texto_input: textoInput,
          obligatoria: obligatoria
        };
        pregs.push(preg);
      });
      var data = {
        display_name: $(element).find('input[name=display_name]').val(),
        texto_verdadero: $(element).find('input[name=texto_verdadero]').val(),
        texto_falso: $(element).find('input[name=texto_falso]').val(),
        texto_header: $(element).find('input[name=texto_header]').val(),
        texto_header_num: $(element).find('input[name=texto_header_num]').val(),
        weight: $(element).find('input[name=weight]').val(),
        nro_de_intentos: $(element).find('input[name=nro_de_intentos]').val(),
        area_height: $(element).find('input[name=area_height]').val(),
        numbering_type: $(element).find('select.numbering_type').val(),
        pretext_num: $(element).find('input[name=pretext_num]').val(),
        postext_num: $(element).find('input[name=postext_num]').val(),
        columnas_por_fila: $(element).find('select.columnas_por_fila').val(),
        preguntas: pregs
      };
      //console.log(data)
      if ($.isFunction(runtime.notify)) {
        runtime.notify('save', {state: 'start'});
      }
      $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
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

    function refreshCellTypeVisibility() {
      $(element).find('select[name=tipo_celda]').each(function() {
        var idpreg = $(this).attr('pregunta-id');
        var tipoCelda = $(this).val();
        var textoField = $(element).find('.cell-texto-field[pregunta-id="' + idpreg + '"]');
        var inputField = $(element).find('.cell-input-field[pregunta-id="' + idpreg + '"]');
        var requiredField = $(element).find('.cell-required-field[pregunta-id="' + idpreg + '"]');
        if (tipoCelda === 'texto') {
          textoField.show();
          inputField.hide();
          requiredField.hide();
        } else {
          textoField.hide();
          inputField.show();
          requiredField.show();
        }
      });
    }

    $(element).on('change', 'select[name=tipo_celda]', function() {
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
