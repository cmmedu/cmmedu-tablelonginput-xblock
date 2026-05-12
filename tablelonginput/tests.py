"""
Module To Test VoF XBlock
"""
import json
import unittest

from mock import MagicMock, Mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey

from xblock.field_data import DictFieldData

from .tablelonginput import tablelonginputXBlock

class TestRequest(object):
    # pylint: disable=too-few-public-methods
    """
    Module helper for @json_handler
    """
    method = None
    body = None
    success = None

class TliIXblockTestCase(unittest.TestCase):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """
    A complete suite of unit tests for the VoF XBlock
    """

    @classmethod
    def make_an_xblock(cls, **kw):
        """
        Helper method that creates a VoF XBlock
        """
        course_id = SlashSeparatedCourseKey('foo', 'bar', 'baz')
        runtime = Mock(
            course_id=course_id,
            service=Mock(
                return_value=Mock(_catalog={}),
            ),
        )
        scope_ids = Mock()
        field_data = DictFieldData(kw)
        xblock = tablelonginputXBlock(runtime, field_data, scope_ids)
        xblock.xmodule_runtime = runtime
        return xblock

    def setUp(self):
        """
        Creates an xblock
        """
        self.xblock = TliIXblockTestCase.make_an_xblock()

    def test_validate_field_data(self):
        """
        Reviso si se creo bien el xblock por defecto, sin intentos y sin respuestas.
        """
        self.assertEqual(self.xblock.attempts, 0)
        self.assertEqual(self.xblock.score, 0.0)
        self.assertEqual(self.xblock.texto_verdadero, 'V')
        self.assertEqual(self.xblock.area_height, '116px')
        self.assertEqual(self.xblock.numbering_type, 'none')
        self.assertEqual(self.xblock.pretext_num, '')
        self.assertEqual(self.xblock.postext_num, '. ')
        self.assertEqual(self.xblock.color_de_celdas_completadas, '#008801')

        self.assertEqual(self.xblock.respondido, False)

    def test_normalize_color_de_celdas_completadas(self):
        self.assertEqual(
            tablelonginputXBlock.normalize_color_de_celdas_completadas('#f00'),
            '#f00',
        )
        self.assertEqual(
            tablelonginputXBlock.normalize_color_de_celdas_completadas('#ff0011'),
            '#ff0011',
        )
        self.assertEqual(
            tablelonginputXBlock.normalize_color_de_celdas_completadas('not-a-color'),
            '#008801',
        )

    def test_basic_answer(self):
        #pruebo respuestas buenas y malas con el problema default
        request = TestRequest()
        request.method = 'POST'

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'verdadero'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 1)

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'falso'}, {'name': '2', 'value': 'falso'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 2)

    def test_basic_answer2(self):
        #pruebo respuestas buenas y malas con el problema default
        request = TestRequest()
        request.method = 'POST'

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'falso'}, {'name': '2', 'value': 'verdadero'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 1)

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'verdadero'}, {'name': '2', 'value': 'falso'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 2)

    def test_min_length_rejection_does_not_consume_attempt(self):
        """
        Si no se cumple el mínimo de caracteres (mismo criterio que la vista),
        no debe incrementarse attempts ni publicarse nota.
        """
        self.xblock.min_caracter_input = 10
        self.xblock.preguntas = {
            '1': {'tipo_celda': 'input', 'texto_input': 'P1'},
            '2': {'tipo_celda': 'texto', 'texto_celda': 'Solo texto'},
        }
        self.xblock.attempts = 0
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps(
            {'respuestas': [{'name': '1', 'value': 'corto'}]}
        ).encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(self.xblock.attempts, 0)
        self.assertTrue(response.json_body.get('min_chars_error'))

    def test_min_length_numeric_question_id_still_validates(self):
        """name numérico en JSON debe alinearse con claves string en preguntas."""
        self.xblock.min_caracter_input = 5
        self.xblock.preguntas = {'1': {'tipo_celda': 'input', 'texto_input': 'Una'}}
        self.xblock.attempts = 0
        request = TestRequest()
        request.method = 'POST'
        request.body = json.dumps(
            {'respuestas': [{'name': 1, 'value': 'xx'}]}
        ).encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(self.xblock.attempts, 0)
        self.assertTrue(response.json_body.get('min_chars_error'))

    def test_add_questions(self):
        #pruebo agregar preguntas
        request = TestRequest()
        request.method = 'POST'

        data = json.dumps({'preguntas': [
                                        {'id': '1', 'enunciado':'pregunta verdadera', 'valor': 'V'},
                                        {'id': '2', 'enunciado':'pregunta verdadera 2', 'valor': 'V'},
                                        {'id': '3', 'enunciado':'pregunta falsa', 'valor': 'F'}
                                        ]})
        request.body = data.encode('utf-8')
        response = self.xblock.studio_submit(request)
        self.assertEqual(response.json_body['result'], 'success')
        preguntas = {'1': {'valor': True, 'enunciado': 'pregunta verdadera'}, '2': {'valor': True, 'enunciado': 'pregunta verdadera 2'}, '3': {'valor': False, 'enunciado': 'pregunta falsa'}}
        self.assertEqual(self.xblock.preguntas, preguntas)

    def test_area_height_normalization(self):
        request = TestRequest()
        request.method = 'POST'

        data = json.dumps({
            'display_name': 'test',
            'texto_verdadero': 'V',
            'texto_falso': 'Respuesta',
            'texto_header': '',
            'texto_header_num': 'Nº',
            'weight': 1,
            'nro_de_intentos': 1,
            'numbering_type': 'letters',
            'pretext_num': '[',
            'postext_num': '] ',
            'area_height': '140',
            'preguntas': [{'id': '1', 'enunciado': 'pregunta', 'valor': 'V'}]
        })
        request.body = data.encode('utf-8')
        response = self.xblock.studio_submit(request)

        self.assertEqual(response.json_body['result'], 'success')
        self.assertEqual(self.xblock.area_height, '140px')
        self.assertEqual(self.xblock.numbering_type, 'letters')
        self.assertEqual(self.xblock.pretext_num, '[')
        self.assertEqual(self.xblock.postext_num, '] ')
        self.assertEqual(self.xblock.texto_header_num, 'Nº')

    def test_answers_with_more_questions(self):
        #agrego preguntas
        request = TestRequest()
        request.method = 'POST'

        data = json.dumps({'preguntas': [
                                        {'id': '1', 'enunciado':'pregunta verdadera', 'valor': 'V'},
                                        {'id': '2', 'enunciado':'pregunta verdadera 2', 'valor': 'V'},
                                        {'id': '3', 'enunciado':'pregunta falsa', 'valor': 'F'}
                                        ],
                            'nro_de_intentos':4})
        request.body = data.encode('utf-8')
        response = self.xblock.studio_submit(request)

        #pruebo respuestas buenas y malas con el problema con nuevas preguntas
        request = TestRequest()
        request.method = 'POST'

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'verdadero'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 1)

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'falso'}, {'name': '2', 'value': 'falso'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 2)

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'falso'}, {'name': '2', 'value': 'verdadero'}, {'name': '3', 'value': 'verdadero'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 3)

        data = json.dumps({'respuestas': [{'name': '1', 'value': 'verdadero'}, {'name': '2', 'value': 'verdadero'}, {'name': '3', 'value': 'falso'}]})
        request.body = data.encode('utf-8')
        response = self.xblock.responder(request)
        self.assertEqual(response.json_body['intentos'], 4)