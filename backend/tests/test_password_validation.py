"""
Tests for password validation (OWASP compliance)
"""

import pytest
from app.schemas.user_schemas import UserCreate
from pydantic import ValidationError


class TestPasswordValidation:
    """Test suite for password strength validation"""

    def test_valid_password_all_types(self):
        """Test password with all 4 character types"""
        user_data = {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert user.password == "StrongPass123!"

    def test_valid_password_3_types_upper_lower_digit(self):
        """Test password with uppercase, lowercase, and digits"""
        user_data = {
            "email": "test@example.com",
            "password": "Password123456",
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert user.password == "Password123456"

    def test_valid_password_3_types_upper_lower_special(self):
        """Test password with uppercase, lowercase, and special chars"""
        user_data = {
            "email": "test@example.com",
            "password": "Password!@#$%",
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert user.password == "Password!@#$%"

    def test_valid_password_3_types_lower_digit_special(self):
        """Test password with lowercase, digits, and special chars"""
        user_data = {
            "email": "test@example.com",
            "password": "password123!@#",
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert user.password == "password123!@#"

    def test_valid_password_minimum_length(self):
        """Test password with exactly 10 characters"""
        user_data = {
            "email": "test@example.com",
            "password": "Pass123!@#",  # 10 chars
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert len(user.password) == 10

    def test_invalid_password_too_short(self):
        """Test password shorter than 10 characters"""
        user_data = {
            "email": "test@example.com",
            "password": "Pass123!",  # 8 chars
            "role": "student",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("password",)
        assert "at least 10 characters" in errors[0]["msg"]

    def test_invalid_password_only_lowercase(self):
        """Test password with only lowercase letters"""
        user_data = {
            "email": "test@example.com",
            "password": "passwordonly",
            "role": "student",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 3" in errors[0]["msg"]

    def test_invalid_password_only_2_types(self):
        """Test password with only 2 character types"""
        user_data = {
            "email": "test@example.com",
            "password": "password123",  # lowercase + digits only
            "role": "student",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 3" in errors[0]["msg"]

    def test_invalid_password_all_digits(self):
        """Test password with only digits"""
        user_data = {
            "email": "test@example.com",
            "password": "1234567890",
            "role": "student",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "at least 3" in errors[0]["msg"]

    def test_password_with_spaces_and_special_chars(self):
        """Test password with spaces and various special characters"""
        user_data = {
            "email": "test@example.com",
            "password": "My Pass 123!@#",
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert user.password == "My Pass 123!@#"

    def test_password_with_unicode_characters(self):
        """Test password with unicode characters (counted as special)"""
        user_data = {
            "email": "test@example.com",
            "password": "Pässwörd123",  # Contains unicode
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert user.password == "Pässwörd123"

    def test_very_long_password(self):
        """Test very long password (should be accepted)"""
        user_data = {
            "email": "test@example.com",
            "password": "VeryLongPassword123!@#$%^&*()_+-=[]{}|;:,.<>?" * 3,
            "role": "student",
        }
        user = UserCreate(**user_data)
        assert len(user.password) > 50

    def test_password_edge_case_exactly_3_types(self):
        """Test password with exactly 3 character types (minimum required)"""
        test_cases = [
            "Uppercase123",  # Upper + Lower + Digit
            "Uppercase!!!",  # Upper + Lower + Special
            "lowercase123!",  # Lower + Digit + Special
        ]

        for password in test_cases:
            user_data = {
                "email": "test@example.com",
                "password": password,
                "role": "student",
            }
            user = UserCreate(**user_data)
            assert user.password == password


class TestPasswordValidationErrorMessages:
    """Test suite for password validation error messages"""

    def test_error_message_too_short(self):
        """Verify error message for short password"""
        user_data = {
            "email": "test@example.com",
            "password": "short",
            "role": "student",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        error_msg = str(exc_info.value)
        assert "10 characters" in error_msg

    def test_error_message_insufficient_complexity(self):
        """Verify error message for insufficient complexity"""
        user_data = {
            "email": "test@example.com",
            "password": "onlylowercase",
            "role": "student",
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)

        error_msg = str(exc_info.value)
        assert "at least 3" in error_msg
        assert "uppercase" in error_msg.lower()
        assert "lowercase" in error_msg.lower()
        assert "digits" in error_msg.lower()
        assert "special" in error_msg.lower()
