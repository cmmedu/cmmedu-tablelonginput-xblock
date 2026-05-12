/* Javascript for VoFXBlock. */
function TLIXBlock(runtime, element, settings) {

    var $ = window.jQuery;
    var $element = $(element);
    // Support current button class and legacy class names.
    var buttonCheck = $element.find('.tli-submit, .check');
    var textareas = $element.find('textarea.student_answer');
    var subFeedback = $element.find('.submission-feedback');
    var statusDiv = $element.find('.status');
    var $minWarn = $element.find('.tli-minlength-warning');
    var areaHeight = $element.data('area-height');
    var minCaracterInput = parseInt($element.attr('data-min-caracter-input'), 10);
    if (isNaN(minCaracterInput) || minCaracterInput < 0) {
        minCaracterInput = 0;
    }
    var handlerUrl = runtime.handlerUrl(element, 'responder');
    var minCharsBannerMsg = 'Verifique que sus respuestas cumplen con el mínimo de caracteres.';

    if (areaHeight) {
        textareas.css('height', areaHeight);
    }

    function hideMinLengthWarning() {
        $minWarn.attr('hidden', 'hidden');
        $minWarn.empty();
    }

    function showMinLengthWarning() {
        $minWarn.removeAttr('hidden');
        $minWarn.text(minCharsBannerMsg);
    }

    function minLengthViolationForTextarea($ta) {
        var val = ($ta.val() || '').trim();
        var minAttr = parseInt($ta.attr('minlength'), 10);
        if (isNaN(minAttr) || minAttr < 0) {
            minAttr = 0;
        }
        var isRequired = $ta.prop('required');
        if (minAttr > 0) {
            if (isRequired && val.length < minAttr) {
                return true;
            }
            if (!isRequired && val.length > 0 && val.length < minAttr) {
                return true;
            }
        } else if (minCaracterInput > 0) {
            if (isRequired && val.length < minCaracterInput) {
                return true;
            }
            if (!isRequired && val.length > 0 && val.length < minCaracterInput) {
                return true;
            }
        }
        return false;
    }

    function hasMinLengthViolation() {
        var found = false;
        $element.find('textarea.student_answer').each(function() {
            if (minLengthViolationForTextarea($(this))) {
                found = true;
                return false;
            }
        });
        return found;
    }

    function textareaHasApplicableMinRequirement($ta) {
        var val = ($ta.val() || '').trim();
        var minAttr = parseInt($ta.attr('minlength'), 10);
        if (isNaN(minAttr) || minAttr < 0) {
            minAttr = 0;
        }
        if (minAttr > 0) {
            return true;
        }
        if (minCaracterInput > 0 && $ta.prop('required')) {
            return true;
        }
        if (minCaracterInput > 0 && val.length > 0) {
            return true;
        }
        return false;
    }

    function refreshMinSatisfiedForTextarea($ta) {
        if (!textareaHasApplicableMinRequirement($ta) || minLengthViolationForTextarea($ta)) {
            $ta.removeClass('tli-min-satisfied');
        } else {
            $ta.addClass('tli-min-satisfied');
        }
    }

    function refreshAllMinSatisfiedClasses() {
        $element.find('textarea.student_answer').each(function() {
            refreshMinSatisfiedForTextarea($(this));
        });
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
        if (result.indicator_class && statusDiv.length) {
            statusDiv.removeClass('correct incorrect unanswered');
            statusDiv.addClass(result.indicator_class);
        }

        if (result.min_chars_error) {
            showMinLengthWarning();
            if (result.texto) {
                subFeedback.text(result.texto);
            }
        } else {
            hideMinLengthWarning();
        }

        if (result.nro_de_intentos > 0) {
            if (!result.min_chars_error) {
                if (result.nro_de_intentos === 1) {
                    subFeedback.text('Ha realizado ' + result.intentos + ' de ' + result.nro_de_intentos + ' intento');
                } else {
                    subFeedback.text('Ha realizado ' + result.intentos + ' de ' + result.nro_de_intentos + ' intentos');
                }
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
        refreshAllMinSatisfiedClasses();
    }

    $element.on('input', 'textarea.student_answer', function(eventObject) {
        if (!settings.is_past_due) {
            buttonCheck.attr("disabled", false);
        }
        hideMinLengthWarning();
        refreshMinSatisfiedForTextarea($(this));
        eventObject.preventDefault();
    });


    buttonCheck.click(function(eventObject) {
        eventObject.preventDefault();
        var missingRequired = false;
        $element.find('.student_answer[required]').each(function() {
            if (!$(this).val().trim()) {
                missingRequired = true;
                return false;
            }
        });
        if (missingRequired) {
            hideMinLengthWarning();
            subFeedback.text('Debe completar todas las celdas obligatorias antes de enviar.');
            return;
        }
        if (hasMinLengthViolation()) {
            showMinLengthWarning();
            if (minCaracterInput > 0) {
                subFeedback.text(
                    'Cada respuesta debe tener al menos ' + minCaracterInput + ' caracteres ' +
                    '(las celdas no obligatorias pueden quedar vacías).'
                );
            } else {
                subFeedback.text(
                    'Una o más celdas no alcanzan el número mínimo de caracteres indicado.'
                );
            }
            return;
        }
        buttonCheck.html("<span>" + buttonCheck[0].dataset.checking + "</span>");
        buttonCheck.attr("disabled", true);
        hideMinLengthWarning();
        if ($.isFunction(runtime.notify)) {
            runtime.notify('tli-submit', {
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
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            data: JSON.stringify({"respuestas": resps}),
            success: updateText,
            error: function() {
                buttonCheck.html("<span>" + buttonCheck[0].dataset.value + "</span>");
                buttonCheck.attr("disabled", false);
            }
        });
        if ($.isFunction(runtime.notify)) {
            runtime.notify('tli-submit', {
                state: 'end'
            });
        }
    });

    refreshAllMinSatisfiedClasses();

    var tablelonginputid = "tablelonginput_" + settings.sublocation;
    renderMathForSpecificElements(tablelonginputid);

    function renderMathForSpecificElements(id) {
        //console.log("Render mathjax in " + id)
        console.log("[CMM-ORDER-TABLE] Render mathjax in " + id)
        if (typeof MathJax !== "undefined") {
            var $ordtab = $('#' + id);
            console.log("[TABLELONGINPUT] encontrado " + $ordtab)
            //console.log($ordtab)
            if ($ordtab.length) {
                $ordtab.find('.tli-table-content').each(function (index, ordtabelem) {
                    MathJax.Hub.Queue(["Typeset", MathJax.Hub, ordtabelem]);
                });
            }
        } else {
            console.warn("[CMM-ORDER-TABLE] MathJax no está cargado.");
        }
    }
}
