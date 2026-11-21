# tests/test_oauth_redirect.py
import unittest
from tools.google_calendar import (
    DEFAULT_STATIC_REDIRECT_URI,
    OAuthExchangeResult,
    get_default_redirect_uri,
)

class TestOAuthRedirect(unittest.TestCase):
    def test_default_redirect_uri(self):
        uri = get_default_redirect_uri()
        self.assertTrue(uri.startswith("http"))
        self.assertFalse(uri.endswith("/"))
        # Default should match the static production URI
        self.assertEqual(uri, DEFAULT_STATIC_REDIRECT_URI)
        self.assertEqual(DEFAULT_STATIC_REDIRECT_URI, "https://mavisagentquanlycuocsong-252.streamlit.app")

    def test_oauth_exchange_result(self):
        res_ok = OAuthExchangeResult(True, None)
        self.assertTrue(bool(res_ok))
        ok, err = res_ok
        self.assertTrue(ok)
        self.assertIsNone(err)

        res_err = OAuthExchangeResult(False, "Lỗi xác thực")
        self.assertFalse(bool(res_err))
        ok2, err2 = res_err
        self.assertFalse(ok2)
        self.assertEqual(err2, "Lỗi xác thực")

if __name__ == "__main__":
    unittest.main()
