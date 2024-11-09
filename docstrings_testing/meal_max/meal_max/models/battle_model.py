import logging
from typing import List

from meal_max.models.kitchen_model import Meal, update_meal_stats
from meal_max.utils.logger import configure_logger
from meal_max.utils.random_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class BattleModel:
    """
    A class to manage the combatants of meal battles.

    Attributes:
        combatants(List[Meal]): list of meals that will combat in battle.
    """
    def __init__(self):
        """
        Initializes the BattleModel with an empty list of combatants.
        """
        self.combatants: List[Meal] = []

    def battle(self) -> str:
        """
        Performs a battle between two meals in the combatants list calculating the delta of their battle score
        and comparing it to a randomly generated number to determine the winner.

        Raises: 
            Value Error: If there are not enough(less than two) combatants.
        
        Returns:
            string: The return value is the meal that wins.
        """
        logger.info("Two meals enter, one meal leaves!")

        if len(self.combatants) < 2:
            logger.error("Not enough combatants to start a battle.")
            raise ValueError("Two combatants must be prepped for a battle.")

        combatant_1 = self.combatants[0]
        combatant_2 = self.combatants[1]

        # Log the start of the battle
        logger.info("Battle started between %s and %s", combatant_1.meal, combatant_2.meal)

        # Get battle scores for both combatants
        score_1 = self.get_battle_score(combatant_1)
        score_2 = self.get_battle_score(combatant_2)

        # Log the scores for both combatants
        logger.info("Score for %s: %.3f", combatant_1.meal, score_1)
        logger.info("Score for %s: %.3f", combatant_2.meal, score_2)

        # Compute the delta and normalize between 0 and 1
        delta = abs(score_1 - score_2) / 100

        # Log the delta and normalized delta
        logger.info("Delta between scores: %.3f", delta)

        # Get random number from random.org
        random_number = get_random()

        # Log the random number
        logger.info("Random number from random.org: %.3f", random_number)

        # Determine the winner based on the normalized delta
        if delta > random_number:
            winner = combatant_1
            loser = combatant_2
        else:
            winner = combatant_2
            loser = combatant_1

        # Log the winner
        logger.info("The winner is: %s", winner.meal)

        # Update stats for both combatants
        update_meal_stats(winner.id, 'win')
        update_meal_stats(loser.id, 'loss')

        # Remove the losing combatant from combatants
        self.combatants.remove(loser)

        return winner.meal

    def clear_combatants(self):
        """
        Clears all meals from combatants list.
        """
        logger.info("Clearing the combatants list.")
        self.combatants.clear()

    def get_battle_score(self, combatant: Meal) -> float:
        """
        Gets the battle score of a given meal using the meal's price, cuisine and difficulty.

        Obtains the battle scor of a meal by multiplying the meals price by the length of its cuisine
        and then subtracting the meal's correspondin difficulty, and returning the float number produced
        by this calculation.

        Args:
            combatant(Meal): the combatant meal to get the battle score for.

        Returns:
            float: Returns the battle score of the meal.
        """
        difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}

        # Log the calculation process
        logger.info("Calculating battle score for %s: price=%.3f, cuisine=%s, difficulty=%s",
                    combatant.meal, combatant.price, combatant.cuisine, combatant.difficulty)

        # Calculate score
        score = (combatant.price * len(combatant.cuisine)) - difficulty_modifier[combatant.difficulty]

        # Log the calculated score
        logger.info("Battle score for %s: %.3f", combatant.meal, score)

        return score

    def get_combatants(self) -> List[Meal]:
        """
        Returns the current list of combatants.

        Returns:
            List[Meal]:
        """
        logger.info("Retrieving current list of combatants.")
        return self.combatants

    def prep_combatant(self, combatant_data: Meal):
        """
        Adds the meals and their corresponding data to the combatants list.

        Appends a Meal object to the end of the combatants list unless there are already two combatants,
        in which case it raises a Value Error.

        Args:
            combatant_data(Meal): the cobantant data of individual meals

        Raises:
            Value Error: If the combatants list is full and already has two combatants.

        """
        if len(self.combatants) >= 2:
            logger.error("Attempted to add combatant '%s' but combatants list is full", combatant_data.meal)
            raise ValueError("Combatant list is full, cannot add more combatants.")

        # Log the addition of the combatant
        logger.info("Adding combatant '%s' to combatants list", combatant_data.meal)

        self.combatants.append(combatant_data)

        # Log the current state of combatants
        logger.info("Current combatants list: %s", [combatant.meal for combatant in self.combatants])
