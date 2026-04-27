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

        self.assertEqual(self.xblock.respondido, False)

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