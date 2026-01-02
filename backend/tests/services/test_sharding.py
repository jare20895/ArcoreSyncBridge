import unittest
from uuid import uuid4
from app.services.sharding import ShardingEvaluator

class TestShardingEvaluator(unittest.TestCase):
    def setUp(self):
        self.target_active = str(uuid4())
        self.target_archived = str(uuid4())
        self.target_default = str(uuid4())
        
        self.policy = {
            "rules": [
                {"if": "status == 'Active'", "target_list_id": self.target_active},
                {"if": "age > 10", "target_list_id": self.target_archived}
            ],
            "default_target_list_id": self.target_default
        }
        self.evaluator = ShardingEvaluator(self.policy)

    def test_match_first_rule(self):
        row = {"status": "Active", "age": 5}
        result = self.evaluator.evaluate(row)
        self.assertEqual(str(result), self.target_active)

    def test_match_second_rule(self):
        row = {"status": "Closed", "age": 15}
        result = self.evaluator.evaluate(row)
        self.assertEqual(str(result), self.target_archived)

    def test_no_match_fallback_default(self):
        row = {"status": "Closed", "age": 5}
        result = self.evaluator.evaluate(row)
        self.assertEqual(str(result), self.target_default)

    def test_missing_column_safe_fail(self):
        # Should skip rule involving missing 'age' and hit default
        row = {"status": "Closed"} 
        result = self.evaluator.evaluate(row)
        self.assertEqual(str(result), self.target_default)

    def test_complex_logic(self):
        policy = {
            "rules": [
                {"if": "count > 100 and type == 'VIP'", "target_list_id": self.target_active}
            ],
            "default_target_list_id": self.target_default
        }
        evaluator = ShardingEvaluator(policy)
        
        self.assertEqual(str(evaluator.evaluate({"count": 101, "type": "VIP"})), self.target_active)
        self.assertEqual(str(evaluator.evaluate({"count": 50, "type": "VIP"})), self.target_default)
