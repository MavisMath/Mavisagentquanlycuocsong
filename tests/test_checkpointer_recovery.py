import unittest
from unittest.mock import patch
from agents.graph import build_graph


class TestCheckpointerRecovery(unittest.TestCase):
    def test_ensure_user_state_loaded_populates_empty_checkpointer(self):
        agent = build_graph()
        config = {"configurable": {"thread_id": "test_restore_user"}}
        
        # Ban đầu checkpointer hoàn toàn trống
        init_state = agent.get_state(config)
        self.assertFalse(bool(init_state and init_state.values))
        
        # Kích hoạt khôi phục
        result = agent.ensure_user_state_loaded("test_restore_user")
        self.assertTrue(result)
        
        # Sau khi khôi phục, checkpointer đã được nạp đầy đủ các key ngữ cảnh
        loaded_state = agent.get_state(config)
        self.assertTrue(bool(loaded_state and loaded_state.values))
        self.assertEqual(loaded_state.values.get("username"), "test_restore_user")
        self.assertIn("goals", loaded_state.values)
        self.assertIn("profile", loaded_state.values)
        self.assertIn("resources", loaded_state.values)
        self.assertIn("roadmap", loaded_state.values)


if __name__ == "__main__":
    unittest.main()
