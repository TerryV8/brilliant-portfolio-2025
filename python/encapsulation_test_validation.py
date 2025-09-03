from main_encapsulation import Person

# Test 1: Invalid age during creation (should work with your current code)
try:
    p = Person("John", -5, "Male")  # Negative age
    print(f"Created person with invalid age: {p}")
except Exception as e:
    print(f"Validation caught during creation: {e}")

# Test 2: Invalid age via property (should fail)
try:
    p = Person("John", 30, "Male")
    p.age = -5  # This should fail
    print(f"Set invalid age via property: {p}")
except Exception as e:
    print(f"Validation caught via property: {e}")

# Test 3: Invalid gender during creation
try:
    p = Person("John", 30, "InvalidGender")
    print(f"Created person with invalid gender: {p}")
except Exception as e:
    print(f"Validation caught during creation: {e}")


# THE RESULT :
#   Person(name='Ann', age=25, gender='Female')
#   Created person with invalid age: Person(name='John', age=-5, gender='Male')
#   Validation caught via property: age must be non-negative
#   Created person with invalid gender: Person(name='John', age=30, gender='InvalidGender')
