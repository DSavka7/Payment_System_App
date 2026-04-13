
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_user_collection():
    """Мок-колекція users для MongoDB."""
    col = MagicMock()
    col.find_one = AsyncMock(return_value=None)
    col.insert_one = AsyncMock()
    col.find_one_and_update = AsyncMock(return_value=None)
    col.delete_one = AsyncMock()
    return col


@pytest.fixture
def mock_account_collection():
    """Мок-колекція accounts для MongoDB."""
    col = MagicMock()
    col.find_one = AsyncMock(return_value=None)
    col.insert_one = AsyncMock()
    col.find_one_and_update = AsyncMock(return_value=None)
    col.delete_one = AsyncMock()
    col.find = MagicMock(return_value=MagicMock(
        to_list=AsyncMock(return_value=[])
    ))
    return col


@pytest.fixture
def mock_tx_collection():
    """Мок-колекція transactions для MongoDB."""
    col = MagicMock()
    col.find_one = AsyncMock(return_value=None)
    col.insert_one = AsyncMock()
    col.count_documents = AsyncMock(return_value=0)
    col.find = MagicMock(return_value=MagicMock(
        sort=MagicMock(return_value=MagicMock(
            skip=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    to_list=AsyncMock(return_value=[])
                ))
            ))
        ))
    ))
    return col