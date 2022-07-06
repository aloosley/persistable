from unittest import TestCase
from persistable.util.os_util import default_standard_filename, parse_standard_filename





class DefaultStandardFilename(TestCase):
    nonparameterized_filename_test = default_standard_filename("test", fn_ext="test")
    parameterized_filename_test = default_standard_filename(
        "test", fn_ext="test", list_1=["c", "b", 4], list_2=["test1", ["set", "element"]], string="a", float_=2.52
    )
    filename_with_set_test = default_standard_filename("test", fn_ext="test", set1={"el1", "el2", "another_el"})

    def test_default_standard_filename(self):

        # Test simple filename:
        nonparameterized_filename_expected = 'test{}.test'
        self.assertEqual(self.nonparameterized_filename_test, nonparameterized_filename_expected)

        # Test filename parameterized with int, str, float, and list parameters:
        parameterized_filename_expected = "test{float_=2.52,list_1=['c', 'b', 4],list_2=['test1', ['set', 'element']],string='a'}.test"
        self.assertEqual(self.parameterized_filename_test, parameterized_filename_expected)

        # Test that set parameters are converted to sorted lists for the filename
        # (non-deterministic set repr breaks the persistable model):

        filename_with_set_execpted = "test{set1=['another_el', 'el1', 'el2']}.test"
        self.assertEqual(self.filename_with_set_test, filename_with_set_execpted)

    def test_parse_standard_filename(self):
        # Check parsing:
        nonparameterized_filename_parsed = parse_standard_filename(self.nonparameterized_filename_test)
        nonparameterized_filename_parsed_expected = ('test', '.test', {})
        self.assertListEqual(list(nonparameterized_filename_parsed), list(nonparameterized_filename_parsed_expected))

        parameterized_filename_parsed = parse_standard_filename(self.parameterized_filename_test)
        parameterized_filename_parsed_expected = (
            'test', '.test',  {'float_': '2.52', 'list_1': "['c','b',4]", 'list_2': "['test1',['set','element']]", 'string': "'a'"}
        )
        self.assertListEqual(list(parameterized_filename_parsed), list(parameterized_filename_parsed_expected))