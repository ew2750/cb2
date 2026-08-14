"""Bake the scanner's 12x12 crop into scenario 0001 materials.

This is a deliberately explicit material migration. It writes an audit report,
rewrites all scenario-0001 condition variants using the same filtering applied
by the scanner runner, and removes scenario 0002/0003 material files.
"""

import argparse
import copy
import json
from pathlib import Path

from cb2game.fmri.scanner_task import (
    PINK_CARD_COLOR,
    _inside_runtime_map,
    _prepare_runtime_materials,
)
from cb2game.server.card_enums import Color, Shape


def _card_description(prop):
    card = prop["card_init"]
    coord = prop["prop_info"]["location"]
    offset_row = 2 * int(coord["r"]) + int(coord["a"])
    return (
        f"ID {int(prop['id'])}: {int(card['count'])} "
        f"{Color(int(card['color'])).name.lower()} "
        f"{Shape(int(card['shape'])).name.lower()}, "
        f"offset cell ({offset_row}, {int(coord['c'])})"
    )


def _target_groups(scenario):
    return [tuple(int(target_id) for target_id in group)
            for group in scenario.get("target_card_ids", [])]


def migrate(materials_dir, report_path):
    materials_dir = Path(materials_dir).resolve()
    run_dirs = sorted(materials_dir.glob("runset_*"))
    if len(run_dirs) != 8:
        raise RuntimeError(f"Expected eight run sets, found {len(run_dirs)}")

    scenario_one_files = sorted(materials_dir.glob("runset_*/scenario_0001_*.json"))
    obsolete_files = sorted(materials_dir.glob("runset_*/scenario_000[23]_*.json"))
    if len(scenario_one_files) != 64 or len(obsolete_files) != 128:
        raise RuntimeError(
            "Migration expects 64 scenario-0001 files and 128 scenario-0002/0003 "
            f"files; found {len(scenario_one_files)} and {len(obsolete_files)}"
        )

    cooked_by_path = {}
    report = [
        "# Scenario 0001: 12x12 material audit",
        "",
        "This report records the permanent conversion of scenario 0001 in run",
        "sets A-H from the original 15x15 layout to the scanner's 12x12 layout.",
        "Cards outside the retained bounds and pink cards are removed. Any",
        "instruction whose target card or required landmark is removed is also",
        "discarded. Scenario 0002 and 0003 material files are removed from this",
        "version of the task.",
        "Pink-house tiles inside the retained map become GROUND_TILE_PATH (asset",
        "ID 28); they no longer function as landmarks.",
        "",
    ]

    for run_dir in run_dirs:
        variants = sorted(run_dir.glob("scenario_0001_*.json"))
        originals = {path: json.loads(path.read_text(encoding="utf-8"))
                     for path in variants}
        representative_path = run_dir / "scenario_0001_t0_l0.json"
        representative = originals[representative_path]
        cards = {
            int(prop["id"]): prop
            for prop in representative.get("prop_update", {}).get("props", [])
            if prop.get("card_init") is not None
        }
        outside_ids = sorted(
            card_id for card_id, prop in cards.items()
            if not _inside_runtime_map(prop.get("prop_info", {}).get("location"))
        )
        pink_inside_ids = sorted(
            card_id for card_id, prop in cards.items()
            if _inside_runtime_map(prop.get("prop_info", {}).get("location"))
            and int(prop["card_init"].get("color", -1)) == PINK_CARD_COLOR
        )

        retained_group_sets = []
        for path, original in originals.items():
            cooked = _prepare_runtime_materials(copy.deepcopy(original), path)
            cooked_by_path[path] = cooked
            retained_group_sets.append(tuple(_target_groups(cooked)))
        if len(set(retained_group_sets)) != 1:
            raise RuntimeError(
                f"Condition variants disagree about retained targets in {run_dir.name}"
            )

        original_groups = _target_groups(representative)
        retained_groups = set(retained_group_sets[0])
        removed_groups = [group for group in original_groups if group not in retained_groups]
        retained_card_ids = {
            int(prop["id"])
            for prop in cooked_by_path[representative_path]
            .get("prop_update", {}).get("props", [])
            if prop.get("card_init") is not None
        }

        report.extend([
            f"## {run_dir.name}",
            "",
            f"- Original cards: {len(cards)}",
            f"- Cards outside 12x12 bounds: {len(outside_ids)}",
            f"- Pink cards inside retained bounds: {len(pink_inside_ids)}",
            f"- Cards retained: {len(retained_card_ids)}",
            f"- Instruction-target pairs retained: {len(retained_groups)} of "
            f"{len(original_groups)}",
            "",
            "### Cards outside the 12x12 map",
            "",
        ])
        report.extend(f"- {_card_description(cards[card_id])}" for card_id in outside_ids)
        report.extend(["", "### Pink cards removed inside the map", ""])
        if pink_inside_ids:
            report.extend(
                f"- {_card_description(cards[card_id])}" for card_id in pink_inside_ids
            )
        else:
            report.append("- None")

        report.extend(["", "### Instruction-target pairs discarded", ""])
        objectives = representative.get("objectives", [])
        for objective, group in zip(objectives, original_groups):
            if group not in removed_groups:
                continue
            missing_target_ids = sorted(set(group) - retained_card_ids)
            if missing_target_ids:
                reason = f"target card removed: {missing_target_ids}"
            else:
                reason = "required landmark removed or excluded"
            report.append(
                f"- Target {list(group)} — {reason}. Instruction: "
                f"{objective.get('text', '').strip()}"
            )
        report.append("")

    report_path = Path(report_path).resolve()
    report_path.write_text("\n".join(report).rstrip() + "\n", encoding="utf-8")

    for path, cooked in cooked_by_path.items():
        path.write_text(json.dumps(cooked, indent=2) + "\n", encoding="utf-8")

    for path in obsolete_files:
        # Paths came from the validated, scenario-specific glob above. Resolve
        # again before deletion to guarantee they remain inside materials_dir.
        resolved = path.resolve()
        if materials_dir not in resolved.parents:
            raise RuntimeError(f"Refusing to delete outside materials: {resolved}")
        resolved.unlink()

    print(f"Rewrote {len(cooked_by_path)} scenario-0001 files")
    print(f"Removed {len(obsolete_files)} scenario-0002/0003 files")
    print(f"Audit report: {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("materials_dir")
    parser.add_argument("report_path")
    args = parser.parse_args()
    migrate(args.materials_dir, args.report_path)


if __name__ == "__main__":
    main()
