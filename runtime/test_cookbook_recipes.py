import unittest

from runtime.cookbook_recipes import RECIPE_PACK, deterministic_recipe_acceptance


class CookbookRecipePackTest(unittest.TestCase):
    def test_recipe_pack_has_three_practical_recipes(self) -> None:
        self.assertEqual(len(RECIPE_PACK), 3)

    def test_recipe_pack_acceptance_is_deterministic(self) -> None:
        acceptance = deterministic_recipe_acceptance()

        self.assertTrue(acceptance["first"]["all_passed"])
        self.assertTrue(acceptance["second"]["all_passed"])
        self.assertTrue(acceptance["deterministic_results"])
        self.assertTrue(acceptance["deterministic_replay_ops"])
        self.assertTrue(acceptance["deterministic_replay_events"])

        self.assertEqual(
            [run["actual_result"] for run in acceptance["first"]["runs"]],
            ["25", "true", "135"],
        )


if __name__ == "__main__":
    unittest.main()
