from utils import strip_code_fences


def test_strip_code_fences():
    cases = [
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
        ('  {"a": 1}  ', '{"a": 1}'),
    ]
    for raw, expected in cases:
        assert strip_code_fences(raw) == expected, f"failed for {raw!r}"
