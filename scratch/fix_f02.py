import re
with open("tests/api/test_rls.py", "r") as f:
    content = f.read()

# Replace app.dependency_overrides.clear() with targeted pop
content = content.replace("app.dependency_overrides.clear()", 
                         "app.dependency_overrides.pop(get_db_session, None)\n        app.dependency_overrides.pop(get_current_user_from_token, None)")

with open("tests/api/test_rls.py", "w") as f:
    f.write(content)
print("Updated test_rls.py")
