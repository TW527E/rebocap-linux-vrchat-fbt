#!/usr/bin/env python3
"""Make an xrizer bindings file for VRChat where the right thumbstick click jumps.

Reads VRChat's own Touch controller bindings from the local install and writes
<out_dir>/oculustouch.json, the name xrizer looks for in XRIZER_CUSTOM_BINDINGS_DIR.
The right stick click normally sends "Udon Stick Click"; it is replaced by Jump. A still jumps.
Run again after a VRChat update.

usage: make-vrchat-bindings.py [--vrchat DIR] [--out DIR]
"""

import argparse
import json
from pathlib import Path

DEFAULT_VRCHAT = Path.home() / ".local/share/Steam/steamapps/common/VRChat"
DEFAULT_OUT = Path.home() / ".config/xrizer-bindings"
RIGHT_STICK = "/user/hand/right/input/joystick"
JUMP = "/actions/global/in/jump"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vrchat", type=Path, default=DEFAULT_VRCHAT, help="VRChat install directory")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="directory for oculustouch.json")
    args = ap.parse_args()

    src = args.vrchat / "VRChat_Data/StreamingAssets/SteamVR/bindings_oculus_touch.json"
    bindings = json.loads(src.read_text())

    changed = 0
    for source in bindings["bindings"]["/actions/global"]["sources"]:
        click = source.get("inputs", {}).get("click")
        if source["path"] == RIGHT_STICK and click:
            click["output"] = JUMP
            changed += 1
    if changed != 1:
        raise SystemExit(f"expected one right stick click binding in {src}, found {changed}; VRChat changed its bindings")

    bindings["name"] = "VRChat Touch - right stick click jumps"
    args.out.mkdir(parents=True, exist_ok=True)
    dst = args.out / "oculustouch.json"
    dst.write_text(json.dumps(bindings, indent=2))
    print(f"wrote {dst}")
    print(f"VRChat launch options need: XRIZER_CUSTOM_BINDINGS_DIR={args.out} ... %command%")


if __name__ == "__main__":
    main()
