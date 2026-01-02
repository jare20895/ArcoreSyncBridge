from typing import Dict, Any, Optional
from uuid import UUID
import operator

class ShardingEvaluator:
    def __init__(self, policy: Dict[str, Any]):
        """
        policy structure:
        {
            "rules": [
                {"if": "status == 'Active'", "target_list_id": "uuid-str"},
                ...
            ],
            "default_target_list_id": "uuid-str"
        }
        """
        self.policy = policy
        self.rules = policy.get("rules", [])
        self.default_target = policy.get("default_target_list_id")

    def _basic_eval(self, condition: str, row: Dict[str, Any]) -> bool:
        """
        Very basic parser for conditions like "field op value".
        Supports: ==, !=, >, <, >=, <=, and
        """
        # Split by ' and ' for basic AND logic
        sub_conditions = condition.split(' and ')
        for sub in sub_conditions:
            if not self._eval_single(sub.strip(), row):
                return False
        return True

    def _eval_single(self, condition: str, row: Dict[str, Any]) -> bool:
        ops = {
            "==": operator.eq,
            "!=": operator.ne,
            ">=": operator.ge,
            "<=": operator.le,
            ">": operator.gt,
            "<": operator.lt
        }
        
        # Find operator
        found_op = None
        for op_str in ops.keys():
            if f" {op_str} " in condition:
                found_op = op_str
                break
        
        if not found_op:
            return False # Invalid syntax
            
        field, val_str = condition.split(f" {found_op} ", 1)
        field = field.strip()
        val_str = val_str.strip()
        
        # Resolve field
        if field not in row:
            return False
        row_val = row[field]
        
        # Parse value type (basic inference)
        comp_val = val_str
        if val_str.startswith("'") and val_str.endswith("'"):
            comp_val = val_str[1:-1]
        elif val_str.isdigit():
            comp_val = int(val_str)
        elif val_str.replace('.', '', 1).isdigit():
            comp_val = float(val_str)
            
        return ops[found_op](row_val, comp_val)

    def evaluate(self, row: Dict[str, Any]) -> Optional[UUID]:
        """
        Evaluates the row against the rules in order.
        Returns the target_list_id of the first matching rule.
        If no rules match, returns the default_target_list_id.
        Returns None if no target can be determined.
        """
        for rule in self.rules:
            condition = rule.get("if")
            target_id = rule.get("target_list_id")
            
            if not condition or not target_id:
                continue

            try:
                if self._basic_eval(condition, row):
                    return UUID(target_id)
            except Exception:
                # Log error or skip rule if evaluation fails
                continue
        
        if self.default_target:
            return UUID(self.default_target)
            
        return None
