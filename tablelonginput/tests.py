# -*- coding: utf-8 -*-
"""
Tests unitarios para el XBlock tablelonginput.
"""
import datetime
import json
import unittest

from django.db import IntegrityError
from mock import Mock

from opaque_keys.edx.locator import CourseLocator
from xblock.field_data import DictFieldData

from .tablelonginput import number_to_letter, number_to_roman, tablelonginputXBlock


class TestRequest(object):
    """Objeto tipo request para invocar @XBlock.json_handler como en LMS."""

    method = None
    body = None
    success = None


class _ServiceWithGettext(object):
    """Servicio i18n simulado que traduce con éxito."""

    def gettext(self, text):
        return text.upper()


class _ServiceGettextRaises(object):
    """Servicio i18n simulado cuyo gettext falla pero ugettext funciona."""

    def gettext(self, text):
        raise ValueError('boom')

    def ugettext(self, text):
        return text + '_ug'


class _ServiceNoTranslators(object):
    """Servicio i18n simulado sin métodos de traducción."""


class _ServiceIdentity(object):
    """Servicio i18n simulado que devuelve el texto sin modificar (strings reales,
    a diferencia del Mock por defecto del runtime, para que build_fragment pueda
    serializar studio_ui a JSON sin errores)."""

    def gettext(self, text):
        return text


class TestNumberHelpers(unittest.TestCase):
    """Conversiones de numeración reutilizadas por el bloque."""

    def test_number_to_letter_basic(self):
        self.assertEqual(number_to_letter(1), 'a')
        self.assertEqual(number_to_letter(26), 'z')
        self.assertEqual(number_to_letter(27), 'aa')

    def test_number_to_letter_edge(self):
        self.assertEqual(number_to_letter(0), '')

    def test_number_to_roman_basic(self):
        self.assertEqual(number_to_roman(1), 'i')
        self.assertEqual(number_to_roman(4), 'iv')
        self.assertEqual(number_to_roman(9), 'ix')

    def test_number_to_roman_out_of_range(self):
        self.assertEqual(number_to_roman(0), '')
        self.assertEqual(number_to_roman(4000), '')


class TestNormalizationStatic(unittest.TestCase):
    """Métodos estáticos de normalización (sin runtime Django)."""

    X = tablelonginputXBlock

    def test_normalize_area_height(self):
        default = self.X.area_height.default
        self.assertEqual(self.X.normalize_area_height(None), default)
        self.assertEqual(self.X.normalize_area_height(''), default)
        self.assertEqual(self.X.normalize_area_height('120px'), '120px')
        self.assertEqual(self.X.normalize_area_height('10'), '10px')
        self.assertEqual(self.X.normalize_area_height('  2rem '), '2rem')
        self.assertEqual(self.X.normalize_area_height('not-css'), default)

    def test_build_numbering_label(self):
        self.assertEqual(
            self.X.build_numbering_label(1, 'numbers', '(', ')'),
            '(1)',
        )
        self.assertEqual(
            self.X.build_numbering_label(2, 'numbers_zero', '', ''),
            '1',
        )
        self.assertEqual(
            self.X.build_numbering_label(3, 'letters', '', '. '),
            'c. ',
        )
        self.assertEqual(
            self.X.build_numbering_label(4, 'roman', '[', ']'),
            '[iv]',
        )
        self.assertEqual(self.X.build_numbering_label(1, 'none', 'x', 'y'), '')

    def test_normalize_column_count(self):
        self.assertEqual(self.X.normalize_column_count(2), 2)
        self.assertEqual(self.X.normalize_column_count(5), 3)
        self.assertEqual(self.X.normalize_column_count(0), 1)
        self.assertEqual(self.X.normalize_column_count('bad'), 2)

    def test_normalize_color_de_celdas_completadas(self):
        self.assertEqual(self.X.normalize_color_de_celdas_completadas('#fff'), '#fff')
        self.assertEqual(self.X.normalize_color_de_celdas_completadas('#aabbcc'), '#aabbcc')
        self.assertEqual(self.X.normalize_color_de_celdas_completadas('red'), '#008801')
        self.assertEqual(self.X.normalize_color_de_celdas_completadas(None), '#008801')

    def test_normalize_submit_button_color(self):
        self.assertEqual(self.X.normalize_submit_button_color(None), '')
        self.assertEqual(self.X.normalize_submit_button_color('#123'), '#123')
        self.assertEqual(self.X.normalize_submit_button_color('#112233'), '#112233')
        self.assertEqual(self.X.normalize_submit_button_color('not-a-color'), '')

    def test_normalize_min_caracter_input(self):
        self.assertEqual(self.X.normalize_min_caracter_input(0), 0)
        self.assertEqual(self.X.normalize_min_caracter_input(500), 500)
        self.assertEqual(self.X.normalize_min_caracter_input(2000), 1000)
        self.assertEqual(self.X.normalize_min_caracter_input('x'), 0)

    def test_normalize_minimo_diferente(self):
        self.assertEqual(self.X.normalize_minimo_diferente(5), 5)
        self.assertEqual(self.X.normalize_minimo_diferente(2000), 1000)
        self.assertEqual(self.X.normalize_minimo_diferente('bad'), 0)

    def test_normalize_required_flag(self):
        self.assertTrue(self.X.normalize_required_flag(True))
        self.assertTrue(self.X.normalize_required_flag('true'))
        self.assertTrue(self.X.normalize_required_flag('1'))
        self.assertFalse(self.X.normalize_required_flag(False))
        self.assertFalse(self.X.normalize_required_flag('no'))
        self.assertFalse(self.X.normalize_required_flag(0))

    def test_compute_minimo_efectivo_for_cell(self):
        min_ef, obl, diff_act, diff = self.X.compute_minimo_efectivo_for_cell(
            {'obligatoria': True, 'minimo_diferente_activo': False},
            3,
        )
        self.assertTrue(obl)
        self.assertFalse(diff_act)
        self.assertEqual(min_ef, 3)

        min_ef, _, _, _ = self.X.compute_minimo_efectivo_for_cell(
            {'minimo_diferente_activo': True, 'minimo_diferente': 5},
            1,
        )
        self.assertEqual(min_ef, 5)

    def test_compute_minimo_efectivo_for_cell_non_dict(self):
        min_ef, obl, diff_act, diff = self.X.compute_minimo_efectivo_for_cell(None, 4)
        self.assertFalse(obl)
        self.assertFalse(diff_act)
        self.assertEqual(min_ef, 4)

    def test_normalize_header_celdas(self):
        out = self.X.normalize_header_celdas({'0': 'A', '1': 'B'}, 2)
        self.assertEqual(out, {'0': 'A', '1': 'B'})
        out = self.X.normalize_header_celdas({}, 3)
        self.assertEqual(out, {'0': '', '1': '', '2': ''})


class TestTableLongInputXBlock(unittest.TestCase):
    """Pruebas del XBlock con runtime simulado."""

    @classmethod
    def make_an_xblock(cls, **kw):
        course_id = CourseLocator('foo', 'bar', 'baz')
        runtime = Mock(
            course_id=course_id,
            service=Mock(return_value=Mock(_catalog={})),
            local_resource_url=Mock(
                side_effect=lambda _self, path: '/static-resource/' + path
            ),
            publish=Mock(),
        )
        scope_ids = Mock()
        field_data = DictFieldData(kw)
        xblock = tablelonginputXBlock(runtime, field_data, scope_ids)
        xblock.xmodule_runtime = runtime
        xblock.location = course_id
        xblock.max_attempts = kw.get('max_attempts', 10)
        return xblock

    def setUp(self):
        self.xblock = self.make_an_xblock()

    def test_defaults(self):
        self.assertEqual(self.xblock.display_name, 'Table long input XBlock')
        # attempts is stored 1-indexed (it represents the upcoming attempt),
        # so a fresh xblock has consumed 0 attempts even though the raw field is 1.
        self.assertEqual(self.xblock.attempts, 1)
        self.assertEqual(self.xblock.get_attempts_used(), 0)
        self.assertEqual(self.xblock.score, 0.0)
        self.assertFalse(self.xblock.respondido)
        self.assertEqual(self.xblock.get_indicator_class(), 'unanswered')
        self.assertEqual(self.xblock.max_score(), self.xblock.weight)
        self.assertIn('1', self.xblock.preguntas)

    def test_get_problem_progress_unattempted(self):
        self.xblock.weight = 2
        self.xblock.attempts = 1
        self.assertIn('2 puntos posibles', self.xblock.get_problem_progress())

    def test_get_problem_progress_weight_zero(self):
        self.xblock.weight = 0
        self.assertIn('0 puntos posibles', self.xblock.get_problem_progress())

    def test_get_problem_progress_graded(self):
        self.xblock.graded = True
        self.xblock.weight = 1
        self.xblock.attempts = 1
        result = self.xblock.get_problem_progress()
        self.assertIn('(calificable)', result)
        self.assertIn('1 punto posible', result)

    def test_get_problem_progress_attempted_weight_one(self):
        self.xblock.weight = 1
        self.xblock.attempts = 2
        self.xblock.score = 1.0
        self.assertIn('1/1 punto', self.xblock.get_problem_progress())

    def test_get_problem_progress_attempted_weight_multi(self):
        self.xblock.weight = 3
        self.xblock.attempts = 2
        self.xblock.score = 1.0
        self.assertIn('3/3 puntos', self.xblock.get_problem_progress())

    def test_responder_success_default_preguntas(self):
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [
                {'name': '1', 'value': 'respuesta uno'},
                {'name': '2', 'value': 'respuesta dos'},
            ],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        body = response.json_body
        self.assertEqual(body['texto'], 'Respuesta enviada correctamente.')
        self.assertEqual(body['score'], 1.0)
        self.assertEqual(body['intentos'], 1)
        self.assertTrue(self.xblock.respondido)
        self.xblock.runtime.publish.assert_called()

    def test_responder_sin_clave_respuestas(self):
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({}).encode('utf-8')

        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['texto'], 'Respuesta enviada correctamente.')

    def test_responder_obligatoria_vacia(self):
        self.xblock.preguntas = {
            '1': {
                'tipo_celda': 'input',
                'texto_celda': 'P1',
                'obligatoria': True,
            },
        }
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [{'name': '1', 'value': '   '}],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        body = response.json_body
        self.assertIn('obligatorias', body['texto'])

    def test_responder_min_caracteres_no_cumplido(self):
        self.xblock.min_caracter_input = 5
        self.xblock.preguntas = {
            '1': {'tipo_celda': 'input', 'texto_celda': 'P1', 'obligatoria': True},
        }
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [{'name': '1', 'value': 'abc'}],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        body = response.json_body
        self.assertTrue(body.get('min_chars_error'))
        # A rejected submission must not consume an attempt.
        self.assertEqual(self.xblock.get_attempts_used(), 0)

    def test_responder_obligatoria_minimo_diferente(self):
        self.xblock.preguntas = {
            '1': {
                'tipo_celda': 'input',
                'texto_celda': 'P1',
                'obligatoria': True,
                'minimo_diferente_activo': True,
                'minimo_diferente': 8,
            },
        }
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [{'name': '1', 'value': 'corto'}],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        self.assertIn('mínimo diferente', response.json_body['texto'])

    def test_responder_opcional_minimo_diferente(self):
        self.xblock.preguntas = {
            '1': {
                'tipo_celda': 'input',
                'texto_celda': 'P1',
                'minimo_diferente_activo': True,
                'minimo_diferente': 8,
            },
        }
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [{'name': '1', 'value': 'corto'}],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        self.assertIn('mínimo diferente', response.json_body['texto'])

    def test_responder_opcional_minimo_no_cumplido(self):
        self.xblock.min_caracter_input = 5
        self.xblock.preguntas = {
            '1': {'tipo_celda': 'input', 'texto_celda': 'P1'},
        }
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [{'name': '1', 'value': 'ab'}],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        self.assertIn('no vacías', response.json_body['texto'])

    def test_responder_ignora_preguntas_invalidas_o_no_input(self):
        self.xblock.preguntas = {
            '1': 'no-es-un-dict',
            '2': {'tipo_celda': 'texto', 'texto_celda': 'solo lectura'},
            '3': {'tipo_celda': 'input', 'texto_celda': 'p3'},
        }
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [{'name': '3', 'value': 'respuesta'}],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['texto'], 'Respuesta enviada correctamente.')

    def test_responder_integrity_error_no_detiene_envio(self):
        self.xblock.runtime.publish = Mock(side_effect=IntegrityError('boom'))
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [
                {'name': '1', 'value': 'respuesta uno'},
                {'name': '2', 'value': 'respuesta dos'},
            ],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['texto'], 'Respuesta enviada correctamente.')
        self.assertTrue(self.xblock.respondido)

    def test_responder_max_intentos(self):
        self.xblock.max_attempts = 1
        # 1 attempt already used out of 1 allowed -> raw field is used(1) + 1.
        self.xblock.attempts = 2
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({
            'respuestas': [
                {'name': '1', 'value': 'a'},
                {'name': '2', 'value': 'b'},
            ],
        }).encode('utf-8')

        response = self.xblock.responder(request)
        body = response.json_body
        self.assertIn('Error', body['texto'])
        self.assertEqual(self.xblock.attempts, 2)

    def test_get_state(self):
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps({}).encode('utf-8')

        response = self.xblock.get_state(request)
        self.assertEqual(response.json_body['result'], 'success')

    def test_studio_submit_success(self):
        request = TestRequest()
        request.method = 'POST'
        payload = {
            'display_name': 'Tabla test',
            'columnas_por_fila': 2,
            'preguntas': [
                {
                    'id': '1',
                    'tipo_celda': 'input',
                    'texto_celda': 'Celda A',
                    'texto_input': '',
                    'minimo_diferente_activo': False,
                    'minimo_diferente': 0,
                },
                {
                    'id': '2',
                    'tipo_celda': 'texto',
                    'texto_celda': 'Solo lectura',
                    'texto_input': '',
                    'minimo_diferente_activo': False,
                    'minimo_diferente': 0,
                },
            ],
            'weight': 3,
            'nro_de_intentos': 4,
            'area_height': '80px',
            'min_caracter_input': 2,
            'color_de_celdas_completadas': '#00ff00',
            'numbering_type': 'letters',
            'pretext_num': '',
            'postext_num': '. ',
            'texto_header_num': 'N',
            'mostrar_header_tabla': False,
            'header_celdas': {},
            'texto_header': '',
        }
        request.body = json.dumps(payload).encode('utf-8')

        response = self.xblock.studio_submit(request)
        self.assertEqual(response.json_body['result'], 'success')
        self.assertEqual(self.xblock.display_name, 'Tabla test')
        self.assertEqual(self.xblock.weight, 3)
        self.assertEqual(self.xblock.max_attempts, 4)
        self.assertEqual(self.xblock.preguntas['1']['tipo_celda'], 'input')

    def test_studio_submit_error_fila_incompleta(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.columnas_por_fila = 2
        request.body = json.dumps({
            'columnas_por_fila': 2,
            'preguntas': [
                {'id': '1', 'tipo_celda': 'input', 'texto_celda': 'solo una'},
            ],
        }).encode('utf-8')

        response = self.xblock.studio_submit(request)
        self.assertEqual(response.json_body['result'], 'error')
        self.assertIn('fila completa', response.json_body['message'])

    def test_studio_submit_pregs_no_es_lista(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.columnas_por_fila = 2
        request.body = json.dumps({
            'columnas_por_fila': 2,
        }).encode('utf-8')

        response = self.xblock.studio_submit(request)
        self.assertEqual(response.json_body['result'], 'error')

    def test_studio_submit_mostrar_header_tabla(self):
        request = TestRequest()
        request.method = 'POST'
        payload = {
            'display_name': 'Tabla con header',
            'columnas_por_fila': 1,
            'preguntas': [
                {'id': '1', 'tipo_celda': 'input', 'texto_celda': 'Celda'},
            ],
            'mostrar_header_tabla': True,
            'header_celdas': {'0': 'Encabezado'},
        }
        request.body = json.dumps(payload).encode('utf-8')

        response = self.xblock.studio_submit(request)
        self.assertEqual(response.json_body['result'], 'success')
        self.assertEqual(self.xblock.texto_header, '')

    def test_studio_submit_header_desde_header_celdas(self):
        request = TestRequest()
        request.method = 'POST'
        payload = {
            'display_name': 'Tabla sin texto_header',
            'columnas_por_fila': 1,
            'preguntas': [
                {'id': '1', 'tipo_celda': 'input', 'texto_celda': 'Celda'},
            ],
            'mostrar_header_tabla': False,
            'header_celdas': {'0': 'Encabezado legado'},
        }
        request.body = json.dumps(payload).encode('utf-8')

        response = self.xblock.studio_submit(request)
        self.assertEqual(response.json_body['result'], 'success')
        self.assertEqual(self.xblock.texto_header, 'Encabezado legado')

    def test_resource_string(self):
        content = self.xblock.resource_string('public/html/tablelonginput.html')
        self.assertTrue(len(content) > 0)

    def test_student_view_default(self):
        frag = self.xblock.student_view()
        self.assertIsNotNone(frag)

    def test_student_view_max_attempts_uno(self):
        self.xblock.max_attempts = 1
        self.xblock.attempts = 1
        frag = self.xblock.student_view()
        self.assertIsNotNone(frag)

    def test_student_view_sin_mas_intentos(self):
        self.xblock.max_attempts = 1
        self.xblock.attempts = 2
        frag = self.xblock.student_view()
        self.assertIsNotNone(frag)

    def test_student_view_con_header_legado(self):
        self.xblock.texto_header = 'Encabezado legado'
        self.xblock.mostrar_header_tabla = False
        frag = self.xblock.student_view()
        self.assertIsNotNone(frag)

    def test_studio_view_default(self):
        self.xblock.runtime.service = Mock(return_value=_ServiceIdentity())
        frag = self.xblock.studio_view(None)
        self.assertIsNotNone(frag)

    def test_studio_view_con_header_legado(self):
        self.xblock.runtime.service = Mock(return_value=_ServiceIdentity())
        self.xblock.texto_header = 'Encabezado legado'
        self.xblock.header_celdas = {}
        frag = self.xblock.studio_view({})
        self.assertIsNotNone(frag)

    def test_studio_gettext_sin_servicio(self):
        self.xblock.runtime.service = Mock(return_value=None)
        self.assertEqual(self.xblock._studio_gettext('hola'), 'hola')

    def test_studio_gettext_usa_gettext(self):
        self.xblock.runtime.service = Mock(return_value=_ServiceWithGettext())
        self.assertEqual(self.xblock._studio_gettext('hola'), 'HOLA')

    def test_studio_gettext_reintenta_tras_excepcion(self):
        self.xblock.runtime.service = Mock(return_value=_ServiceGettextRaises())
        self.assertEqual(self.xblock._studio_gettext('hola'), 'hola_ug')

    def test_studio_gettext_sin_traductores(self):
        self.xblock.runtime.service = Mock(return_value=_ServiceNoTranslators())
        self.assertEqual(self.xblock._studio_gettext('hola'), 'hola')

    def test_get_indicator_class_incorrect(self):
        self.xblock.respondido = True
        self.xblock.attempts = 2
        self.xblock.score = 0
        self.assertEqual(self.xblock.get_indicator_class(), 'incorrect')

    def test_get_show_correctness_default(self):
        self.assertEqual(self.xblock.get_show_correctness(), 'always')

    def test_get_show_correctness_explicit_value(self):
        self.xblock.show_correctness = 'never'
        self.assertEqual(self.xblock.get_show_correctness(), 'never')

    def test_get_show_correctness_past_due_true(self):
        self.xblock.show_correctness = 'past_due'
        self.xblock.due = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        self.assertEqual(self.xblock.get_show_correctness(), 'always')

    def test_get_show_correctness_past_due_false(self):
        self.xblock.show_correctness = 'past_due'
        self.xblock.due = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        self.assertEqual(self.xblock.get_show_correctness(), 'never')

    def test_get_is_past_due_default(self):
        self.assertFalse(self.xblock.get_is_past_due())

    def test_get_is_past_due_con_show_correctness(self):
        self.xblock.show_correctness = 'always'
        self.xblock.due = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        self.assertTrue(self.xblock.get_is_past_due())

    def test_is_past_due_sin_fecha(self):
        self.assertFalse(self.xblock.is_past_due())

    def test_is_past_due_con_fecha_pasada_sin_graceperiod(self):
        self.xblock.due = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        self.xblock.graceperiod = None
        self.assertTrue(self.xblock.is_past_due())

    def test_is_past_due_con_graceperiod_aun_vigente(self):
        self.xblock.due = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        self.xblock.graceperiod = datetime.timedelta(days=1)
        self.assertFalse(self.xblock.is_past_due())

    def test_workbench_scenarios(self):
        scenarios = tablelonginputXBlock.workbench_scenarios()
        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0][0], 'TliXBlock')


if __name__ == '__main__':
    unittest.main()
