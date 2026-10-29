import unittest
from jsonschema import Draft202012Validator
from mre_engineer.experiment_agent import BASIS,CRITIC_COMMENT

class BasisContractTests(unittest.TestCase):
    def test_complete_170_character_reason_is_preserved(self):
        text='Review states priority unresolved and gas alone cannot separate collection loss from charge allocation; prerequisites name independent recovery and generation accounting.'
        self.assertEqual(len(text),170)
        self.assertEqual(list(Draft202012Validator(BASIS).iter_errors(text)),[])
        self.assertEqual(CRITIC_COMMENT['properties']['basis'],BASIS)
    def test_empty_wrong_type_and_unbounded_text_still_fail(self):
        validator=Draft202012Validator(BASIS)
        for value in ('',None,123,'x'*1001):
            with self.subTest(value_type=type(value).__name__):self.assertTrue(list(validator.iter_errors(value)))
