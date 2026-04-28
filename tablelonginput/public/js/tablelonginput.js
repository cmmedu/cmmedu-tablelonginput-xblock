/* Javascript for VoFXBlock. */
function TLIXBlock(runtime, element, settings) {

    var $ = window.jQuery;
    var $element = $(element);
    var buttonCheck = $element.find('.check');
    var textareas = $element.find('textarea.student_answer');
    var subFeedback = $element.find('.submission-feedback');
    var areaHeight = $element.data('area-height');
    var handlerUrl = runtime.handlerUrl(element, 'responder');

    if (areaHeight) {
        textareas.css('height', areaHeight);
    }

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
        if (result.nro_de_intentos > 0) {
            if (result.nro_de_intentos === 1) {
                subFeedback.text('Ha realizado ' + result.intentos + ' de ' + result.nro_de_intentos + ' intento');
            } else {
                subFeedback.text('Ha realizado ' + result.intentos + ' de ' + result.nro_de_intentos + ' intentos');
            }

            if (result.intentos >= result.nro_de_intentos) {
                buttonCheck.attr("disabled", true);
                $element.find('.tablagrande').addClass('noclick');
                renderAnswersAsPlainText();
            } else {
                buttonCheck.attr("disabled", false);
                $element.find('.tablagrande').removeClass('noclick');
            }
        } else {
            buttonCheck.attr("disabled", false);
            $element.find('.tablagrande').removeClass('noclick');
        }

        buttonCheck.html("<span>" + buttonCheck[0].dataset.value + "</span>");
    }

    inputs.click(function(eventObject) {
        if (!settings.is_past_due) {
            buttonCheck.attr("disabled", false);
        }
        eventObject.preventDefault();
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
        var resps = [];
        $element.find('.student_answer').each(function() {
            resps.push({
                name: $(this).attr('pregunta-id'),
                value: $(this).val()
            });
        });
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

}
