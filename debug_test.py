import asyncio
import pytest
from tests.api.test_leads import test_get_leads_integration
import os

async def main():
    os.environ["CIVIX_JWT_SECRET"] = "test_secret"
    pytest.main(["tests/api/test_leads.py::test_get_leads_integration", "-v", "-s"])

if __name__ == "__main__":
    asyncio.run(main())
