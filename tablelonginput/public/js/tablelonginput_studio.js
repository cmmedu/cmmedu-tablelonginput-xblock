function TLIEditBlock(runtime, element) {
    $(element).find('.save-button').bind('click', function(eventObject) {
      eventObject.preventDefault();
      var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

      //obtengo preguntas y su valor
      var pregs = [];
      $.each( $(element).find('input[name=pregunta]'), function( key, value ) {
        //enunciado
        enun = $(this).val();
        //valor
        idpreg = $(this).attr('pregunta-id');
        valor = $('[valor-id='+idpreg+']').val();
        preg = { 'id': idpreg, 'enunciado': enun, 'valor': valor};
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
      var max_id = 0;
      $.each( $(element).find('input[name=pregunta]'), function( key, value ) {
        cur_id = parseInt($(this).attr('pregunta-id'));
        if(max_id < cur_id)
          max_id = cur_id;
      });
      var nueva_id = max_id + 1;
      var nueva_pregunta = '';
      nueva_pregunta += '<div class="div-pregunta-'+nueva_id+'">';
      nueva_pregunta += '<div class="wrapper-comp-setting">';
      nueva_pregunta += '<label class="label setting-label" for="pregunta">Pregunta</label>';
      nueva_pregunta += '<input class="input setting-input" name="pregunta" pregunta-id="'+nueva_id+'" value="Escribe el enunciado" type="text" />';
      nueva_pregunta += '</div>';
      nueva_pregunta += '<div class="action-item">';
      nueva_pregunta += '<a href="#" borrar-id="'+nueva_id+'" class="button action-primary borrar-button">Borrar</a>';
      nueva_pregunta += '</div>';
      nueva_pregunta += '</div>';
      $(element).find("#listapreguntas").append(nueva_pregunta);
      botones_borrar();
    });

    function botones_borrar(){
      $(element).find('.borrar-button').bind('click', function(eventObject) {
        eventObject.preventDefault();
        var borrar_id = $(this).attr('borrar-id');
        $(element).find(".div-pregunta-"+borrar_id ).remove();
      });
    }
    botones_borrar();

  }
