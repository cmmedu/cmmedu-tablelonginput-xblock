# -*- coding: utf-8 -*-
"""
Tests unitarios para el XBlock tablelonginput.
"""
import json
import unittest

from mock import Mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xblock.field_data import DictFieldData

from .tablelonginput import number_to_letter, number_to_roman, tablelonginputXBlock


class TestRequest(object):
    """Objeto tipo request para invocar @XBlock.json_handler como en LMS."""

    method = None
    body = None
    success = None


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

    def test_normalize_min_caracter_input(self):
        self.assertEqual(self.X.normalize_min_caracter_input(0), 0)
        self.assertEqual(self.X.normalize_min_caracter_input(500), 500)
        self.assertEqual(self.X.normalize_min_caracter_input(2000), 1000)
        self.assertEqual(self.X.normalize_min_caracter_input('x'), 0)

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

    def test_normalize_header_celdas(self):
        out = self.X.normalize_header_celdas({'0': 'A', '1': 'B'}, 2)
        self.assertEqual(out, {'0': 'A', '1': 'B'})
        out = self.X.normalize_header_celdas({}, 3)
        self.assertEqual(out, {'0': '', '1': '', '2': ''})


class TestTableLongInputXBlock(unittest.TestCase):
    """Pruebas del XBlock con runtime simulado."""

    @classmethod
    def make_an_xblock(cls, **kw):
        course_id = SlashSeparatedCourseKey('foo', 'bar', 'baz')
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
        xblock.max_attempts = kw.get('max_attempts', 10)
        return xblock

    def setUp(self):
        self.xblock = self.make_an_xblock()

    def test_defaults(self):
        self.assertEqual(self.xblock.display_name, 'Table long input XBlock')
        self.assertEqual(self.xblock.attempts, 0)
        self.assertEqual(self.xblock.score, 0.0)
        self.assertFalse(self.xblock.respondido)
        self.assertEqual(self.xblock.get_indicator_class(), 'unanswered')
        self.assertEqual(self.xblock.max_score(), self.xblock.weight)
        self.assertIn('1', self.xblock.preguntas)

    def test_get_problem_progress_unattempted(self):
        self.xblock.weight = 2
        self.xblock.attempts = 0
        self.assertIn('2 puntos posibles', self.xblock.get_problem_progress())

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
        self.assertEqual(body['texto'], self.xblock.texto_correcto)
        self.assertEqual(body['score'], 1.0)
        self.assertEqual(body['intentos'], 1)
        self.assertTrue(self.xblock.respondido)
        self.xblock.runtime.publish.assert_called()

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
        self.assertEqual(self.xblock.attempts, 0)

    def test_responder_max_intentos(self):
        self.xblock.max_attempts = 1
        self.xblock.attempts = 1
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
        self.assertEqual(self.xblock.attempts, 1)

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
            'texto_falso': '',
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

    def test_is_past_due_sin_fecha(self):
        self.assertFalse(self.xblock.is_past_due())


if __name__ == '__main__':
    unittest.main()
