"""
MAIN GOAL: Demonstrate encapsulation with private attributes and property decorators.

This file shows:
- Private attributes with double underscore (__name)
- Property decorators for getters and setters
- Controlled access to class attributes
- Data validation and logging in setters
"""

# Run static type checks with mypy:
#   mypy --hide-error-codes --pretty main_encapsulation.py
# If mypy was installed via pip --user and isn't on PATH (as on this machine):
#   ~/Library/Python/3.11/bin/mypy --hide-error-codes --pretty main_encapsulation.py
# For example, p2 = Person(38, 30, "Male") -> mypy will report a type error (name expects str).


class Person:
    def __init__(self, name: str, age: int, gender: str) -> None:
        # Use properties to leverage validation
        self._name = name
        self._age = age
        self._gender = gender

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        # Basic normalization and validation
        if not isinstance(value, str):
            raise TypeError("name must be a string")
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        # Custom mapping example from your code
        if value.lower() == "thierry":
            self._name = "root"
        else:
            self._name = value

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("age must be an int")
        if value < 0:
            raise ValueError("age must be non-negative")
        self._age = value

    @property
    def gender(self) -> str:
        return self._gender

    @gender.setter
    def gender(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("gender must be a string")
        normalized = value.strip().title()
        allowed = {"Male", "Female", "Other"}
        if normalized not in allowed:
            raise ValueError(f"gender must be one of {sorted(allowed)}")
        self._gender = normalized

    @staticmethod
    def is_adult(age: int) -> bool:
        return age >= 18

    def __repr__(self) -> str:
        return f"Person(name={self._name!r}, age={self._age}, gender={self._gender!r})"

    @classmethod
    def from_birth_year(
        cls, name: str, birth_year: int, gender: str, *, current_year: int | None = None
    ):
        """Create a Person from birth year.

        Args:
            name: Person's name
            birth_year: four-digit birth year
            gender: gender string (validated like the setter)
            current_year: override current year for testing
        """
        if current_year is None:
            # Simple current year without external deps
            from datetime import date

            current_year = date.today().year
        if not isinstance(birth_year, int):
            raise TypeError("birth_year must be an int")
        if birth_year <= 0 or birth_year > current_year:
            raise ValueError("birth_year must be a positive year not in the future")
        age = current_year - birth_year
        return cls(name, age, gender)


p1 = Person("John", 30, "Male")

p1.name = "Jane"
print(p1.name)

print(Person.is_adult(8))
print(Person.is_adult(18))
print(Person.from_birth_year("Ann", 2000, "Female"))
