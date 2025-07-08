import unittest
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from typing import List, Optional


# Pydantic v2-compliant model
class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    is_active: bool = True
    age: int = Field(..., ge=0, le=120)

    @field_validator('email')
    @classmethod
    def email_must_contain_at_symbol(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email address')
        return v

    @model_validator(mode="after")
    def check_name_and_age(self) -> 'User':
        if self.name == "John" and self.age < 18:
            raise ValueError("John must be at least 18")
        return self


class Group(BaseModel):
    name: str
    members: List[User]


# Unit tests
class TestPydanticModels(unittest.TestCase):

    def test_valid_user(self):
        user = User(id=1, name="Alice", age=30, email="alice@example.com")
        self.assertEqual(user.name, "Alice")
        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(user.is_active)

    def test_type_coercion(self):
        user = User(id="2", name="Bob", age="25")
        self.assertEqual(user.id, 2)
        self.assertEqual(user.age, 25)

    def test_default_values(self):
        user = User(id=3, name="Charlie", age=40)
        self.assertTrue(user.is_active)
        self.assertIsNone(user.email)

    def test_invalid_email(self):
        with self.assertRaises(ValidationError) as cm:
            User(id=4, name="Dave", age=50, email="not-an-email")
        self.assertIn('Invalid email address', str(cm.exception))

    def test_age_limits(self):
        with self.assertRaises(ValidationError):
            User(id=5, name="Eve", age=150)

    def test_custom_model_validator(self):
        with self.assertRaises(ValidationError) as cm:
            User(id=6, name="John", age=17)
        self.assertIn("John must be at least 18", str(cm.exception))

    def test_nested_model(self):
        users = [
            User(id=1, name="Alice", age=30),
            User(id=2, name="Bob", age=25)
        ]
        group = Group(name="TestGroup", members=users)
        self.assertEqual(group.name, "TestGroup")
        self.assertEqual(len(group.members), 2)
        self.assertEqual(group.members[0].name, "Alice")


if __name__ == '__main__':
    unittest.main()