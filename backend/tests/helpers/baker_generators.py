def gen_phone_number() -> str:
    """
    model_bakery has no built-in generator for PhoneNumberField, so tests using
    `_fill_optional` on the user model would fail without one.
    """
    return "+36701234567"
