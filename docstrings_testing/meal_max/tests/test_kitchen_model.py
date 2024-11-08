from contextlib import contextmanager
import re
import sqlite3
import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_leaderboard,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats
)

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    @contextmanager
    def mock_get_db_connection():
        yield mock_conn

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor

def test_create_meal_success(mock_cursor):
    """Test creating a new meal successfully."""

    create_meal(meal="Pasta", cuisine="Italian", price=15.99, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    expected_args = ("Pasta", "Italian", 15.99, "MED")
    actual_args = mock_cursor.execute.call_args[0][1]
    assert expected_args == actual_args, "Query arguments do not match."

def test_create_meal_invalid_price():
    """Test error raised when creating a meal with an invalid price."""
    with pytest.raises(ValueError, match="Invalid price: -10. Price must be a positive number."):
        create_meal(meal="Pasta", cuisine="Italian", price=-10, difficulty="MED")

def test_create_meal_invalid_difficulty():
    """Test error raised when creating a meal with an invalid difficulty."""
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal( meal="Pasta", cuisine="Italian", price=10.99, difficulty="EASY")

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate meal."""

    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meal.meal")

    with pytest.raises(ValueError, match="Meal with name 'Pasta' already exists"):
        create_meal(meal="Pasta", cuisine="Italian", price=10.99, difficulty="LOW")

def test_clear_meals(mock_cursor, mocker):
    """Test clearing the meals database."""

    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_song_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    clear_meals()

    mock_open.assert_called_once_with('sql/create_song_table.sql', 'r')

    mock_cursor.executescript.assert_called_once()

def test_delete_meal_success(mock_cursor):
    """Test deleting a meal successfully."""
    mock_cursor.fetchone.return_value = ([False])  # Meal is not deleted
    delete_meal(1)

    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

    expected_select_args = (1,)
    expected_update_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    assert  actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"The UPDATE query arguments did not match. Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_already_deleted(mock_cursor):
    """Test error raised when trying to delete an already deleted meal."""
    mock_cursor.fetchone.return_value = ([True])  # Meal is already deleted

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        delete_meal(1)

def test_delete_meal_not_found(mock_cursor):
    """Test error raised when trying to delete a non-existent meal."""
    mock_cursor.fetchone.return_value = None  # Meal does not exist

    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        delete_meal(1)

def test_get_leaderboard_success(mock_cursor):
    """Test retrieving the leaderboard successfully."""
    mock_cursor.fetchall.return_value = [
        (1, "Pasta", "Italian", 15.99, "MED", 10, 8, 0.8),
        (2, "Pizza", "Italian", 12.99, "LOW", 5, 3, 0.6)
    ]

    result = get_leaderboard(sort_by="wins")
    expected = [
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 15.99, "difficulty": "MED", "battles": 10, "wins": 8, "win_pct": 80.0},
        {"id": 2, "meal": "Pizza", "cuisine": "Italian", "price": 12.99, "difficulty": "LOW", "battles": 5, "wins": 3, "win_pct": 60.0}
    ]
    assert result == expected, "Leaderboard results do not match."

def test_get_leaderboard_invalid_sort_by():
    """Test error raised when an invalid sort_by parameter is provided."""
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
        get_leaderboard(sort_by="invalid_sort")

def test_get_meal_by_id_success(mock_cursor):
    """Test retrieving a meal by ID successfully."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 15.99, "MED", False)

    result = get_meal_by_id(1)
    expected = Meal(1, "Pasta", "Italian", 15.99, "MED")
    assert result == expected, "Retrieved meal does not match the expected meal."

def test_get_meal_by_id_not_found(mock_cursor):
    """Test error raised when retrieving a meal by a non-existent ID."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_already_deleted(mock_cursor):
    """Test error raised when retrieving a meal that has already been deleted."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 15.99, "MED", True)
    
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)


def test_get_meal_by_name_success(mock_cursor):
    """Test retrieving a meal by name successfully."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 15.99, "MED", False)

    result = get_meal_by_name("Pasta")
    expected = Meal(1, "Pasta", "Italian", 15.99, "MED")
    assert result == expected, "Retrieved meal does not match the expected meal."

def test_get_meal_by_name_not_found(mock_cursor):
    """Test error raised when retrieving a meal by a non-existent name."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with name Pasta not found"):
        get_meal_by_name("Pasta")

def test_get_meal_by_name_already_deleted(mock_cursor):
    """Test error raised when retrieving a meal that has already been deleted."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 15.99, "MED", True)
    
    with pytest.raises(ValueError, match="Meal with name Pasta has been deleted"):
        get_meal_by_name("Pasta")


def test_update_meal_stats_win(mock_cursor):
    """Test updating meal stats for a win."""
    mock_cursor.fetchone.return_value = ([False])  # Meal is not deleted
    update_meal_stats(1, "win")

    expected_query = "UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?"
    actual_query = mock_cursor.execute.call_args_list[1][0][0]
    assert expected_query in actual_query, "SQL query for win update does not match."

def test_update_meal_stats_already_deleted(mock_cursor):
    """Test error raised when updating meal stats for a meal that has already been deleted."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 15.99, "MED", True)
    
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")

def test_update_meal_stats_not_found(mock_cursor):
    """Test error raised when updating meal stats for a meal that cannot be found."""
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        update_meal_stats(1, "win")

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test error raised when providing an invalid result."""
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 15.99, "MED", False)

    with pytest.raises(ValueError, match="Invalid result: banana. Expected 'win' or 'loss'."):
        update_meal_stats(1, "banana")
