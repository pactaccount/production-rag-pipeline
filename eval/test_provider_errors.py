import unittest

from app.api.errors import provider_http_error


class ProviderErrorTest(unittest.TestCase):
    def test_quota_is_retryable_without_provider_details(self):
        error = provider_http_error(RuntimeError("Gemini API 429 quota exceeded; project private-id"))
        self.assertEqual(error.status_code, 429)
        self.assertEqual(error.headers["Retry-After"], "60")
        self.assertNotIn("private-id", error.detail)

    def test_other_failure_is_generic(self):
        error = provider_http_error(RuntimeError("Qdrant URL private-host unavailable"))
        self.assertEqual(error.status_code, 502)
        self.assertNotIn("private-host", error.detail)


if __name__ == "__main__":
    unittest.main()
