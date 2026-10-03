"""Cross-file regression checks for the Advanced Text Adventure tutorial.

Verifies that all five parts run standalone and exit cleanly, that running
or importing them does not pollute global state, and that the shared game
logic (enemy generator, loot, battle, levelling) behaves correctly.
"""

import builtins
import contextlib
import importlib.util
import io
import os
import random
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))

PART_1 = "Advanced Text Adventure Part 1 - Hero Class.py"
PART_2 = "Advanced Text Adventure Part 2 - Enemy Class & Enemy Generator.py"
PART_3 = "Advanced Text Adventure Part 3.py"
PART_4 = "Advanced Text Adventure Part 4.py"
PART_5 = "Advanced Text Adventure Part 5 COMPLETE.py"
PARTS = [PART_1, PART_2, PART_3, PART_4, PART_5]

STANDALONE_INPUT = {
    PART_1: "",
    PART_2: "",
    PART_3: "",
    PART_4: "1\n" * 500,
    PART_5: "1\n\n1\nRegressionBot\n" + "1\n" * 100000,
}


def load_module(filename):
    path = os.path.join(HERE, filename)
    name = "tutorial_" + os.path.splitext(filename)[0]
    name = "".join(ch if ch.isalnum() else "_" for ch in name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print("PASS:", label)


def snapshot_dir():
    return sorted(os.listdir(HERE))


def test_standalone_runs():
    for part in PARTS:
        before = snapshot_dir()
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, part)],
            input=STANDALONE_INPUT[part],
            cwd=HERE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=300,
            text=True,
        )
        check(part + " exits with code 0 (stderr: " + result.stderr[-200:] + ")",
              result.returncode == 0)
        check(part + " leaves the working directory untouched",
              snapshot_dir() == before)


def test_imports_have_no_side_effects():
    before = snapshot_dir()
    for part in PARTS:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            load_module(part)
        check(part + " imports silently (no game code runs on import)",
              stream.getvalue() == "")
    check("importing all parts creates no files", snapshot_dir() == before)


def test_enemy_generator_robustness():
    module = load_module(PART_5)

    random.seed(99)
    first = module.enemyGen(False)
    random.seed(99)
    second = module.enemyGen(False)
    check("repeated seeds generate identical enemies without crashing",
          vars(first) == vars(second))

    normal = [module.enemyGen(False) for _ in range(50)]
    check("normal enemies keep the Part 5 attack range (10-15)",
          all(10 <= e.getAttack() <= 15 for e in normal))
    bosses = [module.enemyGen(True) for _ in range(20)]
    check("boss generation still works", all(hasattr(b, "getSuper") for b in bosses))

    old_cwd = os.getcwd()
    try:
        empty_dir = tempfile.mkdtemp()
        open(os.path.join(empty_dir, "adjective.txt"), "w").close()
        open(os.path.join(empty_dir, "animal.txt"), "w").close()
        os.chdir(empty_dir)
        fallback = module.enemyGen(False)
        check("empty name lists fall back instead of crashing",
              fallback.getName() == "Mysterious Stranger")

        missing_dir = tempfile.mkdtemp()
        os.chdir(missing_dir)
        fallback = module.enemyGen(True)
        check("missing name files fall back instead of crashing",
              fallback.getName() == "Mysterious Stranger")
    finally:
        os.chdir(old_cwd)


def test_interface_drift():
    modules = [load_module(part) for part in (PART_2, PART_3, PART_4, PART_5)]
    for part, module in zip((PART_2, PART_3, PART_4, PART_5), modules):
        attacks = [module.enemyGen(False).getAttack() for _ in range(50)]
        check(part + " normal enemy attack matches the Part 5 range",
              all(10 <= attack <= 15 for attack in attacks))


def test_level_generator_edge_levels():
    module = load_module(PART_5)
    character = module.hero(100, 10, 10, 10, 10, 10, "Edge")

    calls = []
    real_battle = module.battle
    module.battle = lambda enemy, hero: calls.append(enemy) or True
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            check("level 0 spawns an empty enemy list without crashing",
                  module.levelGenerator(character, 0) is True and len(calls) == 0)
            check("negative level spawns an empty enemy list without crashing",
                  module.levelGenerator(character, -3) is True and len(calls) == 0)
            check("large level generates the full enemy list",
                  module.levelGenerator(character, 40) is True and len(calls) == 200)
    finally:
        module.battle = real_battle

    module.battle = lambda enemy, hero: False
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            check("level stops spawning battles once the hero is dead",
                  module.levelGenerator(character, 4) is False)
    finally:
        module.battle = real_battle


def test_enemy_attack_never_negative():
    for part in (PART_3, PART_4, PART_5):
        module = load_module(part)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            loss = module.enemyAttack(10, 5, "Test Enemy", 99)
        check(part + " clamps damage when defence exceeds attack",
              loss == 0)


def scripted_randint(sequence):
    values = iter(sequence)
    return lambda low, high: next(values)


def test_loot_level_up():
    module = load_module(PART_5)
    real_randint = random.randint
    try:
        character = module.hero(100, 10, 8, 10, 10, 10, "Lucky")
        random.randint = scripted_randint([0, 0, 1])
        with contextlib.redirect_stdout(io.StringIO()):
            module.loot(10, character)
        check("health potion raises health, not luck-based overflow",
              character.getHealth() == 110 and character.getLuck() == 8)

        random.randint = scripted_randint([0, 0, 0])
        with contextlib.redirect_stdout(io.StringIO()):
            module.loot(10, character)
        check("luck is capped at 10 when levelling up",
              character.getLuck() == 10)
    finally:
        random.randint = real_randint


def test_battle_settlement_and_death():
    module = load_module(PART_5)
    real_input = builtins.input
    try:
        builtins.input = lambda *args: "1"

        winner = module.hero(100, 999, 10, 10, 10, 10, "Strong")
        weak_enemy = module.enemy(10, 1, 0, 0, "Weak")
        with contextlib.redirect_stdout(io.StringIO()):
            result = module.battle(weak_enemy, winner)
        check("overkill clamps enemy health at zero",
              result is True and weak_enemy.getHealth() == 0)

        loser = module.hero(5, 0, 0, 0, 0, 0, "Fragile")
        strong_enemy = module.enemy(10, 999, 0, 10, "Strong")
        with contextlib.redirect_stdout(io.StringIO()):
            result = module.battle(strong_enemy, loser)
        check("dead hero stops acting and health never goes negative",
              result is False and loser.getHealth() == 0)
    finally:
        builtins.input = real_input


def test_create_class_input_routing():
    module = load_module(PART_5)
    real_input = builtins.input
    answers = iter(["maybe", "1", "", "archer?", "2", "Tester"])
    try:
        builtins.input = lambda *args: next(answers)
        with contextlib.redirect_stdout(io.StringIO()):
            class_data = module.createClass()
    finally:
        builtins.input = real_input
    check("invalid answers re-prompt inside the same section",
          class_data[5] == "Tester")
    check("archer/magic choice uses its own answer, not the first section",
          class_data[2] == 5 and class_data[4] == 10)


def main():
    tests = [
        test_imports_have_no_side_effects,
        test_enemy_generator_robustness,
        test_interface_drift,
        test_level_generator_edge_levels,
        test_enemy_attack_never_negative,
        test_loot_level_up,
        test_battle_settlement_and_death,
        test_create_class_input_routing,
        test_standalone_runs,
    ]
    for test in tests:
        test()
    check("no global state pollution after the whole run",
          snapshot_dir() == sorted(f for f in os.listdir(HERE)))
    print("All regression checks passed.")


if __name__ == "__main__":
    main()
