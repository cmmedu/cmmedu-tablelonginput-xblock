#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""Bloque Tablas de entradas de texto"""

import pkg_resources


from xblock.core import XBlock
from django.db import IntegrityError
from django.template.context import Context
from xblock.fields import Integer, String, Dict, Scope, Float, Boolean
from xmodule.fields import Date
from xblockutils.resources import ResourceLoader
from xblock.fragment import Fragment
import datetime
import pytz

utc=pytz.UTC

loader = ResourceLoader(__name__)

@XBlock.needs('i18n')
class tablelonginputXBlock(XBlock):

    #campos de los settings
    display_name = String(
        display_name="Display Name",
        help="Nombre del componente",
        scope=Scope.settings,
        default="Table long input XBlock"
    )

    texto_verdadero = String(
        display_name="Verdadero",
        help="Texto que ve el estudiante en el Verdadero",
        scope=Scope.settings,
        default="V"
    )

    texto_falso = String(
        display_name="Label respuesta",
        help="Texto que ve el estudiante en el Falso",
        scope=Scope.settings,
        default="Respuesta"
    )

    texto_header = String(
        display_name="Header",
        help="Texto de cabecera si es que se necesita",
        scope=Scope.settings,
        default=""
    )

    texto_correcto = String(
        display_name="Falso",
        help="Texto que aparece al tener todas buenas",
        scope=Scope.settings,
        default="¡Respuesta Correcta!",
    )

    texto_incorrecto = String(
        display_name="Falso",
        help="Texto que aparece cuando tienes todas malas",
        scope=Scope.settings,
        default="Respuesta Incorrecta",
    )

    texto_parcial = String(
        display_name="Falso",
        help="Texto que aparece cuando tienes una buena pero no el total",
        scope=Scope.settings,
        default="Respuesta parcialmente correcta",
    )

    #preguntas
    preguntas = Dict(default={'1':{'enunciado':'¿1+1=2?'}, '2':{'enunciado':'Un triángulo tiene 4 lados'}},
                 scope=Scope.settings,
                 help="Lista de preguntas del V o F")
    #respuestas del estudiante
    #WARNING: por algún motivo dejar esto default vacio dio problemas
    respuestas = Dict(default={'1':'nada','2':'nada'},
                 scope=Scope.user_state,
                 help="Aquí guardaré las respuestas de los estudiantes")
    #si respondió o no
    respondido = Boolean(help="Respondió?", default=False,
        scope=Scope.user_state)

    theme = String(
        display_name = "Estilo",
        help = "Cambiar estilo de la pregunta",
        default = "SumaySigue",
        values = ["SumaySigue", "Media","RedFid"],
        scope = Scope.settings
    )
    
    score = Float(
        default=0.0,
        scope=Scope.user_state,
    )

    weight = Integer(
        display_name='Weight',
        help='Entero que representa el peso del problema',
        default=1,
        values={'min': 0},
        scope=Scope.settings,
    )

    max_attempts = Integer(
        display_name='Nro. de Intentos',
        help='Entero que representa cuantas veces se puede responder problema',
        default=2,
        values={'min': 0},
        scope=Scope.settings,
    )

    attempts = Integer(
        display_name='Intentos',
        help='Cuantas veces el estudiante ha intentado responder',
        default=0,
        values={'min': 0},
        scope=Scope.user_state,
    )

    
    show_answer = String(
        display_name = "Mostrar Respuestas",
        help = "Si aparece o no el boton mostrar respuestas",
        default = "Ocultar",
        values = ["Mostrar", "Finalizado", "Ocultar"],
        scope = Scope.settings
    )

    last_submission_time = Date(
        help= "Last submission time",
        scope=Scope.user_state)

    has_score = True

    icon_class = "problem"

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")
    
    def build_fragment(
            self,
            rendered_template,
            initialize_js_func,
            additional_css=[],
            additional_js=[],
    ):
        #  pylint: disable=dangerous-default-value, too-many-arguments
        """
        Creates a fragment for display.
        """
        fragment = Fragment(rendered_template)
        for item in additional_css:
            url = self.runtime.local_resource_url(self, item)
            fragment.add_css_url(url)
        for item in additional_js:
            url = self.runtime.local_resource_url(self, item)
            fragment.add_javascript_url(url)
        settings = {
            'image_path': self.runtime.local_resource_url(self, 'public/images/'),
            'is_past_due': self.get_is_past_due()
        }
        fragment.initialize_js(initialize_js_func, json_args=settings)
        return fragment

    def student_view(self, context={}):
        """
        Vista estudiante
        """
        #Tuve que pasar las preguntas a una lista para ordenarlas, TO DO: pasar a listas o ver que es mas eficiente
        lista_pregs = [ [k,v] for k, v in list(self.preguntas.items()) ]
        lista_pregs = sorted(lista_pregs, key=lambda x: int(x[0]))
        texto_intentos = ''
        no_mas_intentos = False

        if self.max_attempts and self.max_attempts > 0:
            texto_intentos = "Ha realizado "+str(self.attempts)+" de "+str(self.max_attempts)+" intentos"
            if self.max_attempts == 1:
                texto_intentos = "Ha realizado "+str(self.attempts)+" de "+str(self.max_attempts)+" intento"
            if self.attempts >= self.max_attempts:
                no_mas_intentos = True

        #status respuesta
        indicator_class = self.get_indicator_class()

        context.update(
            {
                'display_name': self.display_name,
                'preguntas': lista_pregs,
                'respuestas': self.respuestas,
                'theme': self.theme,
                'texto_falso': self.texto_falso,
                'texto_header': self.texto_header,
                'texto_correcto': self.texto_correcto,
                'texto_incorrecto': self.texto_incorrecto,
                'texto_intentos': texto_intentos,
                'no_mas_intentos': no_mas_intentos,
                'nro_de_intentos': self.max_attempts,
                'score': self.score,
                'respondido': self.respondido,
                'show_answers': self.show_answer,
                'problem_progress': self.get_problem_progress(),
                'indicator_class': indicator_class,
                'image_path' : self.runtime.local_resource_url(self, 'public/images/'),
                'location': str(self.location).split('@')[-1],
                'show_correctness': self.get_show_correctness(),
                'is_past_due': self.get_is_past_due
            }
        )
        template = loader.render_django_template(
            'public/html/tablelonginput.html',
            context=Context(context),
            i18n_service=self.runtime.service(self, 'i18n'),
        )
        frag = self.build_fragment(
            template,
            initialize_js_func='TLIXBlock',
            additional_css=[
                'public/css/tablelonginput.css'
            ],
            additional_js=[
                'public/js/mathjax.js',
                'public/js/tablelonginput.js'
            ],
        )
        return frag

    def studio_view(self, context):
        """
        Create a fragment used to display the edit view in the Studio.
        """
        #Tuve que pasar las preguntas a una lista para ordenarlas
        lista_pregs = [ [k,v] for k, v in list(self.preguntas.items()) ]
        lista_pregs = sorted(lista_pregs, key=lambda x: int(x[0]))

        context.update(
            {
                'display_name': self.display_name,
                'preguntas': lista_pregs,
                'location': self.location,
                'texto_falso': self.texto_falso,
                'texto_header': self.texto_header,
                'weight': self.weight,
                'show_answers': self.show_answer,
                'theme': self.theme,
                'nro_de_intentos': self.max_attempts
            }
        )
        template = loader.render_django_template(
            'public/html/tablelonginput_studio.html',
            context=Context(context),
            i18n_service=self.runtime.service(self, 'i18n'),
        )
        frag = self.build_fragment(
            template,
            initialize_js_func='TLIEditBlock',
            additional_js=[
                'public/js/tablelonginput_studio.js',
            ],
        )    
        return frag

    # handler para votar sí o no
    @XBlock.json_handler
    def responder(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Responder el V o F
        """
        print("Revisar Long Input ")
        #Reviso si no estoy haciendo trampa y contestando mas veces en paralelo
        max_attempts_fixed = self.max_attempts if self.max_attempts else self.attempts + 1 # Fix max attempts None
        if ((self.attempts + 1) <= max_attempts_fixed) or max_attempts_fixed <= 0:
            nuevas_resps = {}
            texto = self.texto_correcto
            buenas = 0.0
            malas = 0.0
            total = len(self.preguntas)

            for e in data['respuestas']:
                idpreg = e['name']
                miresp = e['value']
                nuevas_resps[idpreg] = miresp
                buenas+=1


            self.respuestas = nuevas_resps

            #puntaje
            self.score = 1

            if self.score > 0 and self.score < 1:
                texto = self.texto_parcial

            ptje = float(self.weight)*self.score
            try:
                self.runtime.publish(
                    self,
                    'grade',
                    {
                        'value': ptje,
                        'max_value': self.weight
                    }
                )
                self.attempts += 1
            except IntegrityError:
                pass

            #ya respondi
            self.respondido = True

            #status respuesta
            indicator_class = self.get_indicator_class()

            self.last_submission_time = datetime.datetime.now(utc)

            return {
                    'texto':texto,
                    'score':self.score,
                    'nro_de_intentos': self.max_attempts,
                    'intentos': self.attempts, 
                    'indicator_class':indicator_class,
                    'show_correctness': self.get_show_correctness(),
                    'show_answers': self.show_answer,
                    'last_submission_time': self.last_submission_time.isoformat()
                    }
        else:
            return {
                    'texto': str('Error: El estado de este problema fue modificado, por favor recargue la página.','utf8'),
                    'score':self.score,
                    'nro_de_intentos': self.max_attempts,
                    'intentos': self.attempts, 
                    'indicator_class': self.get_indicator_class(),
                    'show_correctness': self.get_show_correctness(),
                    'show_answers': self.show_answer,
                    'last_submission_time': self.last_submission_time
                    }
    
    @XBlock.json_handler
    def mostrar_respuesta(self, data, suffix=''):
        """
        Mostrar las respuestas
        """
        max_attempts_fixed = self.max_attempts if self.max_attempts else self.attempts + 1 # Fix max attempts None
        if (self.attempts >= max_attempts_fixed and self.show_answer == 'Finalizado') or self.show_answer == 'Mostrar':
            return {'preguntas': self.preguntas}
        else:
            return {}


    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        """
        Called when submitting the form in Studio.
        """
        nuevas_pregs = {}
        pregs = data.get('preguntas')
        for p in pregs:
            #WARNING: Aquí aunque castee a int, queda como string la id, me rendi por eso ocupo string
            nuevas_pregs[p['id']] = {'enunciado':p['enunciado']}

        self.display_name = data.get('display_name')
        self.texto_verdadero = data.get('texto_verdadero')
        self.texto_falso = data.get('texto_falso')
        self.texto_header = data.get('texto_header')
        self.theme = data.get('theme')
        self.show_answer = data.get('show_answers')
        if data.get('weight') and int(data.get('weight')) >= 0:
            self.weight = int(data.get('weight'))
        if data.get('nro_de_intentos') and int(data.get('nro_de_intentos')) > 0:
            self.max_attempts = int(data.get('nro_de_intentos'))
        self.preguntas = nuevas_pregs
    
        return {'result': 'success'}

    def get_indicator_class(self):
        indicator_class = 'unanswered'
        if self.respondido and self.attempts:
            if self.score >= 1:
                indicator_class = 'correct'
            else:
                indicator_class = 'incorrect'
        return indicator_class

    def get_show_correctness(self):
        if hasattr(self, 'show_correctness'):
            if self.show_correctness == 'past_due':
               if self.is_past_due():
                   return "always"
               else:
                   return "never"
            else:
                return self.show_correctness
        else:
            return "always"

    def get_is_past_due(self):
        if hasattr(self, 'show_correctness'):
            return self.is_past_due()
        else:
            return False

    def is_past_due(self):
        """
        Determine if component is past-due
        """
        # These values are pulled from platform.
        # They are defaulted to None for tests.
        due = getattr(self, 'due', None)
        graceperiod = getattr(self, 'graceperiod', None)
        # Calculate the current DateTime so we can compare the due date to it.
        # datetime.utcnow() returns timezone naive date object.
        now = datetime.datetime.utcnow()
        if due is not None:
            # Remove timezone information from platform provided due date.
            # Dates are stored as UTC timezone aware objects on platform.
            due = due.replace(tzinfo=None)
            if graceperiod is not None:
                # Compare the datetime objects (both have to be timezone naive)
                due = due + graceperiod
            return now > due
        return False

    def get_problem_progress(self):
        """
        Returns a statement of progress for the XBlock, which depends
        on the user's current score
        """
        calif = ' (no calificable)'
        if hasattr(self, 'graded') and self.graded:
            calif = ' (calificable)'
        if self.weight == 0:
            result = '0 puntos posibles'+calif
        elif self.attempts <= 0:
            if self.weight == 1:
                result = "1 punto posible"+calif
            else:
                result = str(self.weight)+" puntos posibles"+calif
        else:
            scaled_score = self.score * self.weight
            # No trailing zero and no scientific notation
            score_string = ('%.15f' % scaled_score).rstrip('0').rstrip('.')
            if self.weight == 1:
                result = str(score_string)+"/"+str(self.weight)+" punto"+calif
            else:
                result = str(score_string)+"/"+str(self.weight)+" puntos"+calif
        return result

    def max_score(self):
        """
        Returns the configured number of possible points for this component.
        Arguments:
            None
        Returns:
            float: The number of possible points for this component
        """
        return self.weight

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("TliXBlock",
             """<tli/>
             """),
            ("Multiple VoFXBlock",
             """<vertical_demo>
                <tli/>
                <tli/>
                <tli/>
                </vertical_demo>
             """),
        ]
