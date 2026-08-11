from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_credit_card_variants() -> None:
    cards = (
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        "4111111111111111",
    )

    for card in cards:
        out = scrub_text(f"Card: {card}")
        assert card not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_vietnamese_passport() -> None:
    passports = ("A1234567", "B1234567", "C1234567")

    for passport in passports:
        out = scrub_text(f"Passport: {passport}")
        assert passport not in out
        assert "REDACTED_PASSPORT_VN" in out


def test_scrub_vietnamese_address_house_number() -> None:
    addresses = ("số 12 đường Nguyễn Trãi", "Số 34/5 Lê Lợi", "so 7 Hai Bà Trưng")

    for address in addresses:
        out = scrub_text(address)
        assert "REDACTED_ADDRESS_VN" in out
