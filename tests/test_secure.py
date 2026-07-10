import base64
import unittest

from src.api.secure import Pass, SecurePlan, _forward, _reverse, signed_token


def encoded(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


class SecureTransformTests(unittest.TestCase):
    def setUp(self):
        table = bytes(range(256))
        self.pass_config = Pass(encoded(table), encoded(b"test-key"), 73)
        self.plan = SecurePlan(
            signing_passes=(self.pass_config, self.pass_config, self.pass_config),
            response_passes=(self.pass_config, self.pass_config, self.pass_config),
            token_parameter="_",
            request_separator="?",
        )

    def test_forward_and_reverse_pass_are_exact_inverses(self):
        plaintext = bytes(range(256)) + b"browser-free"
        encrypted = _forward(plaintext, self.pass_config)
        self.assertEqual(_reverse(encrypted, self.pass_config), plaintext)

    def test_signed_token_round_trips_to_normalized_path_and_params(self):
        token = signed_token(
            "https://comix.to/api/v1/chapters/42",
            {"page": 2, "filters": {"lang": "en"}, "_": "old"},
            self.plan,
        )
        data = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        for config in reversed(self.plan.signing_passes):
            data = _reverse(data, config)
        self.assertEqual(data.decode(), '/chapters/42?filters[lang]="en"&page=2')


if __name__ == "__main__":
    unittest.main()
