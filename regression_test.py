import contextlib
import io
import os
import random
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.abspath(__file__))

PARTS = [
    "Advanced Text Adventure Part 1 - Hero Class.py",
    "Advanced Text Adventure Part 2 - Enemy Class & Enemy Generator.py",
    "Advanced Text Adventure Part 3.py",
    "Advanced Text Adventure Part 4.py",
    "Advanced Text Adventure Part 5 COMPLETE.py",
]

PART5 = PARTS[4]
STDIN_FEED = "1\n" * 100000

failures = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print("[%s] %s%s" % (status, name, (" - " + detail) if detail else ""))
    if not condition:
        failures.append(name)

def snapshot_repo():
    state = {}
    for name in os.listdir(REPO):
        path = os.path.join(REPO, name)
        if os.path.isfile(path):
            stat = os.stat(path)
            state[name] = (stat.st_size, stat.st_mtime_ns)
    return state

def run_part(part_name, cwd, stdin_feed=STDIN_FEED):
    return subprocess.run(
        [sys.executable, os.path.join(REPO, part_name)],
        cwd=cwd,
        input=stdin_feed,
        text=True,
        capture_output=True,
        timeout=120,
    )

def exec_part(part_name):
    source = open(os.path.join(REPO, part_name)).read()
    namespace = {"__name__": "__regression__"}
    previous_cwd = os.getcwd()
    os.chdir(REPO)
    previous_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("")
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                exec(compile(source, part_name, "exec"), namespace)
            except EOFError:
                pass
    finally:
        sys.stdin = previous_stdin
        os.chdir(previous_cwd)
    return namespace

def test_parts_exit_independently():
    for part_name in PARTS:
        result = run_part(part_name, REPO)
        check(
            "%s exits on its own" % part_name,
            result.returncode == 0 and "Traceback" not in result.stderr,
            "returncode=%s" % result.returncode,
        )
        result = run_part(part_name, REPO)
        check(
            "%s exits cleanly on a repeated run" % part_name,
            result.returncode == 0 and "Traceback" not in result.stderr,
            "returncode=%s" % result.returncode,
        )

def test_no_global_state_pollution(before):
    check("no files created or modified in the repo", before == snapshot_repo())
    check(
        "no __pycache__ left behind",
        not os.path.isdir(os.path.join(REPO, "__pycache__")),
    )

def test_empty_enemy_lists():
    temp_dir = tempfile.mkdtemp(prefix="adv_text_empty_")
    try:
        shutil.copy(os.path.join(REPO, PARTS[1]), os.path.join(temp_dir, PARTS[1]))
        for file_name in ("adjective.txt", "animal.txt"):
            open(os.path.join(temp_dir, file_name), "w").close()
        result = run_part(PARTS[1], temp_dir)
        check(
            "enemyGen survives empty name lists",
            result.returncode == 0 and "Traceback" not in result.stderr,
            "returncode=%s stderr=%s" % (result.returncode, result.stderr.strip()),
        )
        check(
            "empty lists fall back to a safe default name",
            "Mysterious Creature" in result.stdout,
        )
    finally:
        shutil.rmtree(temp_dir)

def test_generator_interface_and_seeds():
    namespace = exec_part(PARTS[1])
    enemy_gen = namespace["enemyGen"]
    random.seed(7)
    first = vars(enemy_gen(False))
    random.seed(7)
    second = vars(enemy_gen(False))
    check("repeated seed reproduces the same enemy", first == second)
    random.seed(7)
    first_boss = vars(enemy_gen(True))
    random.seed(7)
    second_boss = vars(enemy_gen(True))
    check("repeated seed reproduces the same boss", first_boss == second_boss)
    check("boss keeps the final-version interface", "superMove" in first_boss)
    attacks = []
    for seed in range(200):
        random.seed(seed)
        attacks.append(enemy_gen(False).getAttack())
    check(
        "normal enemy attack matches Part 5 (10-15, no interface drift)",
        min(attacks) == 10 and max(attacks) == 15,
        "min=%s max=%s" % (min(attacks), max(attacks)),
    )

def test_battle_rules():
    namespace = exec_part(PARTS[3])
    enemy_attack = namespace["enemyAttack"]
    with contextlib.redirect_stdout(io.StringIO()):
        loss = enemy_attack(10, 5, "test enemy", 20)
    check("enemy damage never goes negative", loss == 0, "loss=%s" % loss)

    hero_class = namespace["hero"]
    enemy_class = namespace["enemy"]
    battle = namespace["battle"]
    with contextlib.redirect_stdout(io.StringIO()):
        dead_hero_outcome = battle(enemy_class(100, 10, 10, 10, "Alive"),
                                   hero_class(0, 10, 10, 10, 1, 10, "Dead"))
        dead_enemy_outcome = battle(enemy_class(0, 10, 10, 10, "Dead"),
                                    hero_class(100, 10, 10, 10, 1, 10, "Alive"))
    check("dead hero cannot keep acting", dead_hero_outcome is False)
    check("dead enemy cannot keep acting", dead_enemy_outcome is True)

def test_level_generator_bounds():
    namespace = exec_part(PART5)
    level_generator = namespace["levelGenerator"]
    hero_class = namespace["hero"]
    character = hero_class(100, 10, 10, 10, 1, 10, "Lee")
    level_generator(character, 0)
    check("level 0 spawns no battles without crashing", True)
    level_generator(character, -1)
    check("negative level spawns no battles without crashing", True)

    dead_character = hero_class(0, 10, 10, 10, 1, 10, "Dead")
    stopped = False
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            level_generator(dead_character, 10 ** 6)
        except SystemExit:
            stopped = True
    check("a dead hero stops the huge level instead of continuing to fight", stopped)

def test_create_class_question():
    namespace = exec_part(PART5)
    create_class = namespace["createClass"]
    previous_stdin = sys.stdin
    sys.stdin = io.StringIO("1\n\n2\nBob\n")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            data = create_class()
    finally:
        sys.stdin = previous_stdin
    check(
        "archer/magic answer is used instead of the first answer",
        data[2] == 5 and data[4] == 10,
        "ranged=%s magic=%s" % (data[2], data[4]),
    )

def test_health_upgrade():
    namespace = exec_part(PARTS[2])
    loot = namespace["loot"]
    hero_class = namespace["hero"]
    sampled = False
    for seed in range(2000):
        character = hero_class(100, 10, 5, 10, 1, 10, "Lee")
        random.seed(seed)
        with contextlib.redirect_stdout(io.StringIO()):
            loot(character.getLuck(), character)
        if character.getHealth() != 100:
            sampled = True
            check(
                "health potion adds to current health, not luck",
                character.getHealth() == 110,
                "health=%s" % character.getHealth(),
            )
            break
    check("a health potion was sampled for the upgrade test", sampled)

def main():
    os.chdir(REPO)
    before = snapshot_repo()
    test_parts_exit_independently()
    test_no_global_state_pollution(before)
    test_empty_enemy_lists()
    test_generator_interface_and_seeds()
    test_battle_rules()
    test_level_generator_bounds()
    test_create_class_question()
    test_health_upgrade()

if __name__ == "__main__":
    main()
    if failures:
        print("\n%d check(s) failed" % len(failures))
        sys.exit(1)
    print("\nAll regression checks passed.")
