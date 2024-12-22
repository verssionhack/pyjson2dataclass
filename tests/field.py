import unittest
import sys
sys.path.append('..')

from src.field import _pack_field, _unpack_field, Field


class TestField(unittest.TestCase):

    def test_unpack_pack(self):
        ei1 = ('Optional[List[Dict[str, int]]]', -1)
        eo1 = (['Optional', 'List', 'Dict'], 'int', None)
        ei2 = ('Optional[List[Dict[str, int]]]', 1)
        eo2 = (['Optional'], 'List[Dict[str, int]]', 'List')

        reo1 = _unpack_field(*ei1)
        reo2 = _unpack_field(*ei2)

        # print(f'unpack_reo1: {reo1}')
        # print(f'unpack_reo2: {reo2}')

        self.assertTupleEqual(eo1, reo1)
        self.assertTupleEqual(eo2, reo2)

    def test_pack(self):
        ei1 = ('int', ['Optional', 'List', 'Dict'])
        eo1 = ('Optional[List[Dict[str, int]]]')
        ei2 = ('List[Dict[str, int]]', ['Optional'])
        eo2 = ('Optional[List[Dict[str, int]]]')

        reo1 = _pack_field(*ei1)
        reo2 = _pack_field(*ei2)

        # print(f'pack_reo1: {reo1}')
        # print(f'pack_reo2: {reo2}')

        self.assertEqual(eo1, reo1)
        self.assertEqual(eo2, reo2)

    def test_field(self):
        field1 = Field('int', ['Optional', 'List', 'Dict'])

        self.assertEqual(field1.field, 'int')
        self.assertEqual(field1.pack,
                         'Optional[List[Dict[str, int]]]')
        self.assertTrue(field1.layers.outer_optional)

        field2 = Field('broken#$-name', ['Optional', 'List', 'Dict'])

        self.assertEqual(field2.repair.field, 'broken_name')
        self.assertEqual(field2.repair.pack,
                         'Optional[List[Dict[str, broken_name]]]')
        self.assertEqual(field2.repair.pack,
                         'Optional[List[Dict[str, broken_name]]]')
        self.assertTrue(field2.layers.outer_optional)


if __name__ == '__main__':
    unittest.main()
