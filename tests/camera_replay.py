"""Independent Windows WebView2 replay for Q9, R-09, and AC-17.

Change contract: operation = rotate, zoom, switch candidates, switch to a
coordinate-free component, and restart; input = the invented two-residue
synthetic example; output = screenshots plus the measured eight-value 3Dmol
view vectors and persisted project state; subject = view persistence only.
Normal case = rotate and zoom Example A, switch to Example B and back, restart.
Boundary cases = first view of a candidate with no saved camera and a selected
component without coordinates.

Mouse drag and wheel events are sent to the actual Edge WebView2 canvas through
Playwright's CDP connection. No product code or the general replay is changed.
"""
import argparse
from contextlib import contextmanager
import json
import math
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from antibody_insight import example, project, structures


def create_case(path):
    project.create_project(path)
    example.populate(path)
    # Give Example B its own structure so the candidate switch exercises two
    # independent camera keys. The coordinate fixture is explicitly synthetic.
    overview = project.summary(path)
    target = next(row for row in overview["components"]
                  if row["candidate"] == next(c["id"] for c in overview["candidates"]
                                              if c["label"] == "Example B")
                  and row["label"] == "Peptide")
    source = ROOT / "examples" / "synthetic-peptide.pdb"
    packet = structures.preview(source, project.component_detail(path, target["id"]))
    structures.save(path, packet, "A", "Unknown")


def camera(page):
    values = page.evaluate("viewer.getView()")
    assert isinstance(values, list) and len(values) == 8, values
    assert all(isinstance(value, (int, float)) and math.isfinite(value)
               for value in values), values
    return [float(value) for value in values]


def same_camera(actual, expected, tolerance=1e-6):
    return (len(actual) == len(expected) == 8 and
            all(abs(a - e) <= tolerance for a, e in zip(actual, expected)))


def wait_for_saved(path, key, expected, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = project.summary(path)["state"]
        saved = state.get("cameras", {}).get(key)
        if saved and same_camera(saved, expected):
            return saved
        time.sleep(.1)
    raise AssertionError(f"Camera state for structure {key} was not persisted: {saved!r}")


@contextmanager
def launch(path, executable=None):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    code = ("import sys,webview; from antibody_insight.desktop import launch; "
            "webview.settings['REMOTE_DEBUGGING_PORT']=int(sys.argv[1]); launch(sys.argv[2])")
    env = os.environ.copy()
    if executable:
        env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={port}"
    command = ([str(executable.resolve()), str(path)] if executable else
               [sys.executable, "-c", code, str(port), str(path)])
    child = subprocess.Popen(command, cwd=path.parent if executable else ROOT, env=env)
    try:
        with sync_playwright() as pw:
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline and child.poll() is None:
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=.4):
                        break
                except OSError:
                    time.sleep(.2)
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.wait_for_event("page")
            yield page, browser
    finally:
        child.terminate()
        child.wait(timeout=15)


def run(path, out, executable=None):
    errors = []
    result = {"requirements": ["Q9", "R-09", "AC-17"],
              "scope": "structure camera persistence only",
              "boundary_cases": {}}
    with launch(path, executable) as (page, browser):
        page.on("pageerror", lambda error: errors.append(str(error)))
        expect(page.locator("#identity")).to_contain_text("Example A / Peptide", timeout=20000)
        expect(page.locator("#coordinate")).to_contain_text("Chain A")
        page.locator("#molecule canvas").wait_for()
        result["webview2_runtime"] = browser.version
        result["structure_a"] = page.locator("#model").input_value()
        baseline = camera(page)

        # Direct mouse drag in the visible molecular canvas.
        box = page.locator("#molecule canvas").bounding_box()
        assert box and box["width"] > 80 and box["height"] > 80, box
        start_x, start_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(start_x, start_y)
        page.mouse.down()
        for step in range(1, 9):
            page.mouse.move(start_x + 120 * step / 8, start_y + 72 * step / 8)
        page.mouse.up()
        rotated = camera(page)
        assert max(abs(rotated[i] - baseline[i]) for i in range(4, 8)) > 1e-4, (baseline, rotated)
        page.screenshot(path=str(out / "camera-rotated.png"))

        # Wheel zoom is also a real pointer input on the canvas.
        page.mouse.wheel(0, -480)
        page.wait_for_timeout(350)
        zoomed = camera(page)
        assert abs(zoomed[3] - rotated[3]) > 1e-4, (rotated, zoomed)
        page.screenshot(path=str(out / "camera-zoomed.png"))
        expected_a = zoomed
        saved_a = wait_for_saved(path, result["structure_a"], expected_a)
        result["camera_a"] = {
            "component_order": ["modelGroup.x", "modelGroup.y", "modelGroup.z",
                                "rotationGroup.position.z", "quaternion.x", "quaternion.y",
                                "quaternion.z", "quaternion.w"],
            "baseline": baseline,
            "after_mouse_rotation": rotated,
            "after_wheel_zoom": zoomed,
            "saved_before_switch": saved_a,
        }

        # Boundary 1: the alternate candidate has no stored camera yet.
        groups = page.locator("#tree .candidate")
        expect(groups.nth(1).locator(".part").filter(has_text="Peptide")).to_have_count(1)
        groups.nth(1).locator(".part").filter(has_text="Peptide").click()
        expect(page.locator("#identity")).to_contain_text("Example B / Peptide")
        expect(page.locator("#coordinate")).to_contain_text("Chain A")
        result["structure_b"] = page.locator("#model").input_value()
        assert result["structure_a"] != result["structure_b"]
        state_before_b_input = project.summary(path)["state"].get("cameras", {})
        assert result["structure_b"] not in state_before_b_input, state_before_b_input
        camera_b_initial = camera(page)
        assert max(abs(a-b) for a,b in zip(camera_b_initial[4:8],[0,0,0,1]))<1e-6, camera_b_initial
        result["boundary_cases"]["first_view_without_saved_camera"] = {
            "candidate": "Example B / Peptide",
            "structure_key_distinct": True,
            "stored_camera_before_view": False,
            "camera": camera_b_initial,
            "camera_is_finite_eight_values": True,
        }

        # Give B a different actual mouse and wheel input, then verify that
        # both candidate-specific eight-value states survive round trips.
        box_b = page.locator("#molecule canvas").bounding_box()
        assert box_b and box_b["width"] > 80 and box_b["height"] > 80, box_b
        start_x_b = box_b["x"] + box_b["width"] / 2
        start_y_b = box_b["y"] + box_b["height"] / 2
        page.mouse.move(start_x_b, start_y_b)
        page.mouse.down()
        for step in range(1, 7):
            page.mouse.move(start_x_b - 90 * step / 6, start_y_b + 38 * step / 6)
        page.mouse.up()
        rotated_b = camera(page)
        page.mouse.wheel(0, 360)
        page.wait_for_timeout(350)
        zoomed_b = camera(page)
        assert max(abs(zoomed_b[i] - camera_b_initial[i]) for i in range(4, 8)) > 1e-4
        assert abs(zoomed_b[3] - rotated_b[3]) > 1e-4
        saved_b = wait_for_saved(path, result["structure_b"], zoomed_b)
        page.screenshot(path=str(out / "camera-candidate-b.png"))
        result["camera_b"] = {
            "initial_without_stored_camera": camera_b_initial,
            "after_mouse_rotation": rotated_b,
            "after_wheel_zoom": zoomed_b,
            "saved": saved_b,
        }

        # Switch back and forth; compare all eight values for both structures.
        groups.nth(0).locator(".part").filter(has_text="Peptide").click()
        expect(page.locator("#identity")).to_contain_text("Example A / Peptide")
        restored_after_switch = camera(page)
        assert same_camera(restored_after_switch, expected_a), (expected_a, restored_after_switch)
        result["camera_a"]["after_candidate_round_trip"] = restored_after_switch
        groups.nth(1).locator(".part").filter(has_text="Peptide").click()
        expect(page.locator("#identity")).to_contain_text("Example B / Peptide")
        restored_b = camera(page)
        assert same_camera(restored_b, zoomed_b), (zoomed_b, restored_b)
        result["camera_b"]["after_candidate_round_trip"] = restored_b
        groups.nth(0).locator(".part").filter(has_text="Peptide").click()
        expect(page.locator("#identity")).to_contain_text("Example A / Peptide")
        restored_a_again = camera(page)
        assert same_camera(restored_a_again, expected_a), (expected_a, restored_a_again)

        # Boundary 2: select a valid component with no registered coordinates,
        # then return. The camera is retained and the viewer stays usable.
        groups.nth(0).locator(".part").filter(has_text="Reporter").click()
        expect(page.locator("#identity")).to_contain_text("Example A / Reporter")
        expect(page.locator("#coordinate")).to_contain_text("No coordinates registered")
        result["boundary_cases"]["coordinate_free_component"] = {
            "component": "Example A / Reporter",
            "visible_status": page.locator("#coordinate").inner_text(),
        }
        groups.nth(0).locator(".part").filter(has_text="Peptide").click()
        expect(page.locator("#identity")).to_contain_text("Example A / Peptide")
        after_no_coordinates = camera(page)
        assert same_camera(after_no_coordinates, expected_a), (expected_a, after_no_coordinates)
        result["camera_a"]["after_coordinate_free_round_trip"] = after_no_coordinates
        assert not errors, errors

    # Reopen exactly the same synthetic project in a new WebView2 process.
    with launch(path, executable) as (page, browser):
        page.on("pageerror", lambda error: errors.append(str(error)))
        expect(page.locator("#identity")).to_contain_text("Example A / Peptide", timeout=20000)
        expect(page.locator("#coordinate")).to_contain_text("Chain A")
        after_restart = camera(page)
        assert same_camera(after_restart, expected_a), (expected_a, after_restart)
        page.screenshot(path=str(out / "camera-after-restart.png"))
        result["webview2_runtime_after_restart"] = browser.version
        result["camera_a"]["after_process_restart"] = after_restart
        assert not errors, errors

    persisted = project.summary(path)["state"].get("cameras", {}).get(result["structure_a"])
    assert persisted and same_camera(persisted, expected_a), persisted
    result["persisted_after_restart"] = persisted
    result["comparison"] = {
        "components_per_view": 8,
        "tolerance": 1e-6,
        "candidate_round_trip_a": same_camera(result["camera_a"]["after_candidate_round_trip"], expected_a),
        "candidate_round_trip_b": same_camera(result["camera_b"]["after_candidate_round_trip"], zoomed_b),
        "return_to_a_after_b": same_camera(restored_a_again, expected_a),
        "coordinate_free_round_trip": same_camera(result["camera_a"]["after_coordinate_free_round_trip"], expected_a),
        "process_restart": same_camera(after_restart, expected_a),
        "errors": errors,
    }
    assert all(result["comparison"][key] for key in
               ("candidate_round_trip_a", "candidate_round_trip_b", "return_to_a_after_b",
                "coordinate_free_round_trip", "process_restart"))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--executable", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="antibody-camera-") as tmp:
        path = Path(tmp) / "Synthetic camera persistence.ais"
        create_case(path)
        result = run(path, args.output, args.executable)
    (args.output / "camera-state.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
