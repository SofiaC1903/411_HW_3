import pytest
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal
from meal_max.utils.random_utils import get_random


@pytest.fixture()
def battle_model():
    """fixture to provide new instance of BattleModel for each test"""
    return BattleModel()


@pytest.fixture
def mock_update_meal_stats(mocker):
    """mock the update_meal_stats function for testing reasons"""
    return mocker.patch("meal_max.models.battle_model.update_meal_stats")


@pytest.fixture
def mock_get_random(mocker):
    """mock the get_random function for testing reasons"""
    return mocker.patch("meal_max.models.battle_model.get_random", return_value=0.5)


@pytest.fixture
def meal_1():
    """fixture for a sample Meal object"""
    return Meal(id=1, meal="Mac and Cheese", cuisine="American", price=6.99, difficulty="LOW")


@pytest.fixture
def meal_2():
    """fixture for another sample Meal object"""
    return Meal(id=2, meal="Quesadillas", cuisine="Mexican", price=9.99, difficulty="LOW")


@pytest.fixture
def prepared_battle(battle_model, meal_1, meal_2):
    """prepare a BattleModel w/t 2 combatants"""
    battle_model.prep_combatant(meal_1)
    battle_model.prep_combatant(meal_2)
    return battle_model

def test_prep_combatant_success(battle_model, meal_1):
    """test successfully adding a combatant to the battle"""
    battle_model.prep_combatant(meal_1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0] == meal_1


def test_prep_combatant_full(battle_model, meal_1, meal_2):
    """test error when trying to add a 3rd combatant"""
    battle_model.prep_combatant(meal_1)
    battle_model.prep_combatant(meal_2)

    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(meal_1)


def test_clear_combatants(prepared_battle):
    """test clearing all combatants"""
    prepared_battle.clear_combatants()
    assert len(prepared_battle.combatants) == 0


def test_get_combatants(prepared_battle):
    """test retrieving the list of combatants"""
    combatants = prepared_battle.get_combatants()
    assert len(combatants) == 2
    assert combatants[0].meal == "Mac and Cheese"
    assert combatants[1].meal == "Quesadillas"

def test_battle_success(prepared_battle, mock_get_random, mock_update_meal_stats):
    """test a successful battle between 2 meals"""
    winner = prepared_battle.battle()
    assert winner in ["Mac and Cheese", "Quesadillas"], "Winner should be one of the combatants."

    mock_update_meal_stats.assert_any_call(1 if winner == "Mac and Cheese" else 2, "win")
    mock_update_meal_stats.assert_any_call(2 if winner == "Mac and Cheese" else 1, "loss")

    assert len(prepared_battle.combatants) == 1
    assert prepared_battle.combatants[0].meal == winner


def test_battle_not_enough_combatants(battle_model):
    """test error when trying to battle with fewer than two combatants"""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()


def test_battle_scores(prepared_battle, mock_get_random):
    """test correct calculation of battle scores"""
    meal_1_score = prepared_battle.get_battle_score(prepared_battle.combatants[0])
    meal_2_score = prepared_battle.get_battle_score(prepared_battle.combatants[1])

    assert isinstance(meal_1_score, float), "Battle score should be a float."
    assert isinstance(meal_2_score, float), "Battle score should be a float."


def test_battle_random_number(prepared_battle, mock_get_random, mock_update_meal_stats):
    """test that the random num is used in determining the winner"""
    prepared_battle.battle()
    mock_get_random.assert_called_once()  

    assert mock_update_meal_stats.call_count == 2

def test_get_battle_score_success(battle_model, meal_1):
    """test calculating the battle score for a meal"""
    score = battle_model.get_battle_score(meal_1)
    expected_score = (meal_1.price * len(meal_1.cuisine)) - 2  
    assert score == expected_score, f"Expected score {expected_score}, got {score}"


def test_get_battle_score_low_difficulty(battle_model, meal_2):
    """test calculating the battle score for a meal wt LOW difficulty"""
    score = battle_model.get_battle_score(meal_2)
    expected_score = (meal_2.price * len(meal_2.cuisine)) - 3  
    assert score == expected_score, f"Expected score {expected_score}, got {score}"

def test_prep_combatant_invalid_type(battle_model):
    """test error when adding a non Meal object to combatants"""
    with pytest.raises(AttributeError):
        battle_model.prep_combatant("Not a Meal")


def test_get_combatants_empty_list(battle_model):
    """test retrieving combatants when list is empty"""
    combatants = battle_model.get_combatants()
    assert len(combatants) == 0


def test_clear_combatants_empty_list(battle_model):
    """test clearing combatants when list is already empty"""
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0
