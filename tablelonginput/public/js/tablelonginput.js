/* Javascript for VoFXBlock. */
function TLIXBlock(runtime, element, settings) {

    var $ = window.jQuery;
    var $element = $(element);
    var buttonCheck = $element.find('.check');
    var buttonVerRespuesta = $element.find('.ver_respuesta');
    var inputs = $element.find('.student_answer');
    var botonesVoF = $element.find('.opcion');
    var lasRespuestas = $element.find('.lasrespuestas');
    var subFeedback = $element.find('.submission-feedback');
    var statusDiv = $element.find('.status');

    function renderAnswersAsPlainText() {
        $element.find('.student_answer').each(function() {
            var answerText = $(this).val();
            var plainTextAnswer = $('<div class="student_answer_plaintext"></div>');
            plainTextAnswer.text(answerText);
            plainTextAnswer.css('white-space', 'pre-wrap');
            $(this).replaceWith(plainTextAnswer);
        });
    }

    function updateText(result) {
        //reviso si estoy mostrando correctitud
        
        statusDiv.removeClass('correct');
        statusDiv.removeClass('incorrect');
        statusDiv.removeClass('unanswered');
        //no deberia pasar pero por si las moscas
        if(result.indicator_class == 'unanswered')
            statusDiv.addClass('unanswered');
        $element.find('.notificacion').html('');
        $element.find('.notificacion').removeClass('lineaarriba');
        $element.find('.notificacion').removeClass('correcto');
        $element.find('.notificacion').removeClass('incorrecto');
        $element.find('.notificacion').removeClass('parcial');
        $element.find('.notificacion').addClass('dontshowcorrectness');
        $element.find('.notificacion.dontshowcorrectness').addClass('lineaarriba');
        $element.find('.notificacion.dontshowcorrectness').html('<span class="icon fa fa-info-circle" aria-hidden="true"></span>Respuesta enviada.');
        $element.find('.notificacion.correcto').html('<img src="'+settings.image_path+'enviado.png"/>');
        $element.find('.elticket').html();


        //desactivo el boton si es que se supero el nro de intentos
        var finalice = false;
        if(result.nro_de_intentos > 0){
            if(result.nro_de_intentos == 1){
                subFeedback.text('Ha realizado '+result.intentos+' de '+result.nro_de_intentos+' intento');
            }
            else{
                subFeedback.text('Ha realizado '+result.intentos+' de '+result.nro_de_intentos+' intentos');
            }

            if(result.intentos >= result.nro_de_intentos){
                buttonCheck.attr("disabled", true);
                $element.find('.tablagrande').addClass('noclick');
                renderAnswersAsPlainText();
                finalice = true;
            }
            else{
                buttonCheck.attr("disabled", false);
                $element.find('.tablagrande').removeClass('noclick');
            }
        }
        else{
            buttonCheck.attr("disabled", false);
            $element.find('.tablagrande').removeClass('noclick');
        }

        if(finalice || (result.intentos >0 && result.nro_de_intentos <= 0)){
            if(result.show_answers == 'Finalizado' && !$element.find('.ver_respuesta').length && result.show_correctness != 'never'){
                var mostrar_resp = '<button class="ver_respuesta" data-checking="Cargando..." data-value="Ver Respuesta">'
                                    + '<span class="icon fa fa-info-circle" aria-hidden="true"></span></br>'
                                    + '<span>Mostrar<br/>Respuesta</span>'
                                    + '</button>';
                $element.find('.action').append(mostrar_resp);
            }
            clickVerRespuesta();
        }

        buttonCheck.html("<span>" + buttonCheck[0].dataset.value + "</span>");
    }

    function showAnswers(result){
        /*
        $.each( result.preguntas, function( key, value ) {
            if(value.valor){
                $element.find('.opcV'+key).addClass('cuadroverde');
            }
            else{
                $element.find('.opcF'+key).addClass('cuadroverde');
            }
          });
          */
    }

    var handlerUrl = runtime.handlerUrl(element, 'responder');
    var handlerUrlVerResp = runtime.handlerUrl(element, 'mostrar_respuesta');

    
    inputs.click(function(eventObject) {
        if(statusDiv.hasClass("unanswered") && !settings.is_past_due){
            buttonCheck.attr("disabled", false);
        }
        eventObject.preventDefault();
        console.log("Click");
    });
    

    buttonCheck.click(function(eventObject) {
        eventObject.preventDefault();
        buttonCheck.html("<span>" + buttonCheck[0].dataset.checking + "</span>");
        buttonCheck.attr("disabled", true);
        if ($.isFunction(runtime.notify)) {
            runtime.notify('submit', {
                message: 'Submitting...',
                state: 'start'
            });
        }
        var resp,resps = [];
        $element.find('.student_answer').each(function() { // run through each of the checkboxes
            resp = {
              name: $(this).attr('pregunta-id'),
              value: $(this).val()
            };
            resps.push(resp);
          });
          //console.log(resps);
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify({"respuestas": resps}),
            success: updateText
        });
        if ($.isFunction(runtime.notify)) {
            runtime.notify('submit', {
                state: 'end'
            });
        }
    });


    function clickVerRespuesta(){
        buttonVerRespuesta = $element.find('.ver_respuesta');
        buttonVerRespuesta.click(function(eventObject) {
            eventObject.preventDefault();
            buttonVerRespuesta.attr("disabled", true);
            $.ajax({
                type: "POST",
                url: handlerUrlVerResp,
                data: JSON.stringify({}),
                //success: showAnswers
            });
        });
    }
    clickVerRespuesta();

    //console.log(lasRespuestas);
    lasRespuestas.each(function() {
        if($( this ).val() == 'verdadero'){
            var pid = $( this ).attr('respuesta-id');
            $element.find('.opcV'+pid).click();
        }
        else{
            var pid = $( this ).attr('respuesta-id');
            $element.find('.opcF'+pid).click();
        }
      });

    $(function ($) {
        /* Here's where you'd do things on page load. */
    });
}
