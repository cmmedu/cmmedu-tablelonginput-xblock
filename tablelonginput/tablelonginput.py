#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""Bloque Tablas de entradas de texto"""

import pkg_resources
import re


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

def number_to_letter(n):
    """Convert number to letter (1=a, 2=b, etc.)."""
    if n < 1:
        return ''
    result = ''
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(97 + remainder) + result
    return result

def number_to_roman(n):
    """Convert number to roman numeral in lowercase."""
    if not 0 < n < 4000:
        return ''
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('m', 'cm', 'd', 'cd', 'c', 'xc', 'l', 'xl', 'x', 'ix', 'v', 'iv', 'i')
    result = []
    for i in range(len(ints)):
        count = int(n / ints[i])
        result.append(nums[i] * count)
        n -= ints[i] * count
    return ''.join(result)

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

    texto_header_num = String(
        display_name="Header de la numeración",
        help="Texto que se mostrará en la celda de la numeración si se utiliza.",
        scope=Scope.settings,
        default="N°",
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
    preguntas = Dict(default={'1': {'enunciado': 'Completa...'}, '2': {}},
                 scope=Scope.settings,
                 help="Lista de preguntas")
    #respuestas del estudiante
    #WARNING: por algún motivo dejar esto default vacio dio problemas
    respuestas = Dict(default={'1':'nada','2':'nada'},
                 scope=Scope.user_state,
                 help="Aquí guardaré las respuestas de los estudiantes")
    #si respondió o no
    respondido = Boolean(help="Respondió?", default=False,
        scope=Scope.user_state)

    
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

    area_height = String(
        display_name='Altura de las areas de texto',
        help='Altura de las areas de texto',
        default='116px',
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

    numbering_type = String(
        display_name="Tipo de numeración",
        help="Tipo de numeración para el listado de preguntas",
        default="none",
        values=["numbers", "numbers_zero", "letters", "roman", "none"],
        scope=Scope.settings
    )

    pretext_num = String(
        display_name="Texto antes de la numeración",
        help="Texto que se mostrará antes de la numeración",
        default="",
        scope=Scope.settings
    )

    postext_num = String(
        display_name="Texto después de la numeración",
        help="Texto que se mostrará después de la numeración",
        default=". ",
        scope=Scope.settings
    )

    columnas_por_fila = Integer(
        display_name="Cantidad de celdas por fila",
        help="Cantidad de celdas de contenido por fila (sin contar numeración)",
        default=2,
        values={'min': 1, 'max': 3},
        scope=Scope.settings,
    )

    mostrar_header_tabla = Boolean(
        display_name="Mostrar encabezado en la tabla",
        help="Si es verdadero, se muestra una fila de encabezado con una celda por columna de contenido.",
        default=False,
        scope=Scope.settings,
    )

    header_celdas = Dict(
        default={},
        scope=Scope.settings,
        help="Texto por columna de encabezado (claves '0', '1', '2').",
    )

    last_submission_time = Date(
        help= "Last submission time",
        scope=Scope.user_state)

    has_score = True

    icon_class = "problem"

    @staticmethod
    def normalize_area_height(value):
        """
        Returns a valid CSS height value for answer textareas.
        """
        default_height = tablelonginputXBlock.area_height.default
        if value is None:
            return default_height
        normalized_value = str(value).strip()
        if not normalized_value:
            return default_height
        if re.match(r'^\d+(\.\d+)?(px|em|rem|vh|vw|%)$', normalized_value):
            return normalized_value
        if re.match(r'^\d+(\.\d+)?$', normalized_value):
            return normalized_value + 'px'
        return default_height

    @staticmethod
    def build_numbering_label(position, numbering_type, pretext_num, postext_num):
        """
        Returns numbering label string for a 1-based position.
        """
        value = ""
        if numbering_type == "numbers":
            value = str(position)
        elif numbering_type == "numbers_zero":
            value = str(position - 1)
        elif numbering_type == "letters":
            value = number_to_letter(position)
        elif numbering_type == "roman":
            value = number_to_roman(position)
        else:
            return ""
        return str(pretext_num) + value + str(postext_num)

    @staticmethod
    def normalize_column_count(value):
        """
        Returns a valid number of content cells per row.
        """
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 2
        return max(1, min(3, parsed))

    @staticmethod
    def normalize_required_flag(value):
        """
        Returns True when a per-cell required flag is enabled.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'yes', 'on')
        return False

    @staticmethod
    def normalize_header_celdas(raw, columnas_por_fila):
        """
        Devuelve un dict con claves '0'..'n-1' y valores string para el encabezado por columna.
        """
        cols = tablelonginputXBlock.normalize_column_count(columnas_por_fila)
        out = {}
        if isinstance(raw, dict):
            for i in range(cols):
                key = str(i)
                val = raw.get(key, raw.get(i, ''))
                out[key] = '' if val is None else str(val)
        return out

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
        lista_pregs_raw = [ [k,v] for k, v in list(self.preguntas.items()) ]
        lista_pregs_raw = sorted(lista_pregs_raw, key=lambda x: int(x[0]))
        lista_pregs = []
        for preg in lista_pregs_raw:
            preg_data = preg[1]
            if not isinstance(preg_data, dict):
                preg_data = {}
            tipo_celda = preg_data.get('tipo_celda', 'input')
            legacy_enunciado = preg_data.get('enunciado', '')
            texto_celda = preg_data.get('texto_celda', legacy_enunciado)
            texto_input = preg_data.get('texto_input', legacy_enunciado if tipo_celda == 'input' else '')
            obligatoria = self.normalize_required_flag(preg_data.get('obligatoria', False))
            lista_pregs.append({
                'id': preg[0],
                'tipo_celda': tipo_celda,
                'texto_celda': texto_celda,
                'texto_input': texto_input,
                'obligatoria': obligatoria,
            })
        columnas_por_fila = self.normalize_column_count(self.columnas_por_fila)
        header_celdas_norm = self.normalize_header_celdas(self.header_celdas, columnas_por_fila)
        header_row_cells = [header_celdas_norm.get(str(i), '') for i in range(columnas_por_fila)]
        use_legacy_header = (
            not self.mostrar_header_tabla
            and bool((self.texto_header or '').strip())
        )
        filas_preguntas = []
        for idx in range(0, len(lista_pregs), columnas_por_fila):
            fila_celdas = lista_pregs[idx:idx + columnas_por_fila]
            fila_pos = (idx // columnas_por_fila) + 1
            filas_preguntas.append({
                'row_numbering_label': self.build_numbering_label(
                    fila_pos, self.numbering_type, self.pretext_num, self.postext_num
                ),
                'cells': fila_celdas,
            })
        texto_intentos = ''
        no_mas_intentos = False

        if self.max_attempts and self.max_attempts > 0:
            texto_intentos = "Ha realizado "+str(self.attempts)+" de "+str(self.max_attempts)+" intentos"
            if self.max_attempts == 1:
                texto_intentos = "Ha realizado "+str(self.attempts)+" de "+str(self.max_attempts)+" intento"
            if self.attempts >= self.max_attempts:
                no_mas_intentos = True

        context.update(
            {
                'display_name': self.display_name,
                'preguntas': lista_pregs,
                'filas_preguntas': filas_preguntas,
                'respuestas': self.respuestas,
                'texto_falso': self.texto_falso,
                'texto_header': self.texto_header,
                'mostrar_header_tabla': self.mostrar_header_tabla,
                'header_row_cells': header_row_cells,
                'use_legacy_header': use_legacy_header,
                'texto_correcto': self.texto_correcto,
                'texto_incorrecto': self.texto_incorrecto,
                'texto_intentos': texto_intentos,
                'no_mas_intentos': no_mas_intentos,
                'nro_de_intentos': self.max_attempts,
                'score': self.score,
                'respondido': self.respondido,
                'problem_progress': self.get_problem_progress(),
                'image_path' : self.runtime.local_resource_url(self, 'public/images/'),
                'location': str(self.location).split('@')[-1],
                'is_past_due': self.get_is_past_due,
                'area_height': self.normalize_area_height(self.area_height),
                'numbering_type': self.numbering_type,
                'texto_header_num': self.texto_header_num,
                'pretext_num': self.pretext_num,
                'postext_num': self.postext_num,
                'columnas_por_fila': columnas_por_fila,
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
        lista_pregs_raw = [[k, v] for k, v in list(self.preguntas.items())]
        lista_pregs_raw = sorted(lista_pregs_raw, key=lambda x: int(x[0]))
        lista_pregs = []
        for key, value in lista_pregs_raw:
            preg_data = value if isinstance(value, dict) else {}
            tipo_celda = preg_data.get('tipo_celda', 'input')
            legacy_enunciado = preg_data.get('enunciado', '')
            lista_pregs.append([key, {
                'enunciado': legacy_enunciado,
                'tipo_celda': tipo_celda,
                'texto_celda': preg_data.get('texto_celda', legacy_enunciado),
                'texto_input': preg_data.get('texto_input', legacy_enunciado if tipo_celda == 'input' else ''),
                'obligatoria': self.normalize_required_flag(preg_data.get('obligatoria', False)),
            }])
        cols = self.normalize_column_count(self.columnas_por_fila)
        hc = dict(self.header_celdas or {})
        legacy_header = (self.texto_header or '').strip()
        if legacy_header and not any((hc.get(str(i)) or '').strip() for i in range(cols)):
            hc['0'] = self.texto_header
        header_cells_studio = []
        for i in range(cols):
            header_cells_studio.append({
                'idx': i,
                'num': i + 1,
                'text': hc.get(str(i), '') or '',
            })

        context.update(
            {
                'display_name': self.display_name,
                'preguntas': lista_pregs,
                'location': self.location,
                'texto_falso': self.texto_falso,
                'texto_header': self.texto_header,
                'texto_header_num': self.texto_header_num,
                'mostrar_header_tabla': self.mostrar_header_tabla,
                'header_cells_studio': header_cells_studio,
                'weight': self.weight,
                'nro_de_intentos': self.max_attempts,
                'area_height': self.normalize_area_height(self.area_height),
                'numbering_type': self.numbering_type,
                'pretext_num': self.pretext_num,
                'postext_num': self.postext_num,
                'columnas_por_fila': cols,
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
            additional_css=[
                'public/css/tablelonginput.css'
            ],
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

            for idpreg, preg_data in self.preguntas.items():
                if not isinstance(preg_data, dict):
                    continue
                if preg_data.get('tipo_celda', 'input') != 'input':
                    continue
                if not self.normalize_required_flag(preg_data.get('obligatoria', False)):
                    continue
                respuesta = nuevas_resps.get(idpreg, '')
                if not str(respuesta).strip():
                    return {
                        'texto': 'Debe completar todas las celdas obligatorias antes de enviar.',
                        'score': self.score,
                        'nro_de_intentos': self.max_attempts,
                        'intentos': self.attempts,
                        'last_submission_time': self.last_submission_time.isoformat() if self.last_submission_time else ''
                    }


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

            self.last_submission_time = datetime.datetime.now(utc)

            return {
                    'texto':texto,
                    'score':self.score,
                    'nro_de_intentos': self.max_attempts,
                    'intentos': self.attempts, 
                    'last_submission_time': self.last_submission_time.isoformat()
                    }
        else:
            return {
                    'texto': str('Error: El estado de este problema fue modificado, por favor recargue la página.','utf8'),
                    'score':self.score,
                    'nro_de_intentos': self.max_attempts,
                    'intentos': self.attempts, 
                    'last_submission_time': self.last_submission_time
                    }


    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        """
        Called when submitting the form in Studio.
        """
        cols = self.normalize_column_count(
            data.get('columnas_por_fila', self.columnas_por_fila)
        )
        pregs = data.get('preguntas')
        if not isinstance(pregs, list):
            pregs = []
        if len(pregs) < cols:
            return {
                'result': 'error',
                'message': (
                    'Debe haber al menos una fila completa antes de guardar '
                    '(una celda por cada columna configurada).'
                ),
            }

        nuevas_pregs = {}
        for p in pregs:
            #WARNING: Aquí aunque castee a int, queda como string la id, me rendi por eso ocupo string
            tipo_celda = p.get('tipo_celda', 'input')
            nuevas_pregs[p['id']] = {
                'enunciado': p.get('texto_celda', ''),
                'tipo_celda': tipo_celda,
                'texto_celda': p.get('texto_celda', ''),
                'texto_input': p.get('texto_input', ''),
                'obligatoria': self.normalize_required_flag(p.get('obligatoria', False))
            }

        self.display_name = data.get('display_name')
        self.texto_verdadero = data.get('texto_verdadero')
        self.texto_falso = data.get('texto_falso')
        self.texto_header_num = data.get('texto_header_num', self.texto_header_num)
        self.numbering_type = data.get('numbering_type', self.numbering_type)
        self.pretext_num = data.get('pretext_num', self.pretext_num)
        self.postext_num = data.get('postext_num', self.postext_num)
        self.columnas_por_fila = self.normalize_column_count(data.get('columnas_por_fila', self.columnas_por_fila))
        self.mostrar_header_tabla = self.normalize_required_flag(data.get('mostrar_header_tabla', False))
        self.header_celdas = self.normalize_header_celdas(
            data.get('header_celdas', self.header_celdas),
            self.columnas_por_fila,
        )
        if self.mostrar_header_tabla:
            self.texto_header = ''
        elif 'texto_header' in data:
            self.texto_header = data.get('texto_header') or ''
        else:
            self.texto_header = self.header_celdas.get('0', '') or ''
        self.area_height = self.normalize_area_height(data.get('area_height'))
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
