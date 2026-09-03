import os
import sys
import pytest
from dotenv import load_dotenv

if __name__ == "__main__":
    os.environ["CIVIX_JWT_SECRET"] = "test_secret"
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    load_dotenv()
    args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/api/test_entities.py", "-v"]
    sys.exit(pytest.main(args))
