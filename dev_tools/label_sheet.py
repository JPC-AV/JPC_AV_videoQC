#!/usr/bin/env python3
"""
label_sheet.py: a blind labeling sheet for weighing QCTools tags in period selection.

The corpus ground truth (active-area BRNG/TOUT/VREP) is the same signal period selection
already scores, so it cannot credit a tag that is not scored yet. An operator's eye can. This
picks ~12 bins per tape, each 10 s long:

  - random analyzable bins as controls (the base rate each tag's hit rate is compared against)
  - the bin where each candidate tag peaks (CANDIDATES, below: new tags and today's scored ones)
  - the evidence bins of today's selection (replayed at 6 x 30, the app default)
  - the 2nd-ranked bin of each new candidate, while room remains

and writes them to $AVSPEX_CORPUS/labels/ as

  sheet_<name>.csv   video_id, tc_in, tc_out (the file's own NDF/DF timecode, matching the NLE),
                     blind_id, and empty defect / severity / notes columns to fill in
  key_<name>.json    which selector(s) put each bin on the sheet. Don't open it while labeling.

Rows are sorted by tape and timecode so each tape is one pass through the NLE; nothing on the
sheet says why a bin is there. Bins already labeled in an earlier sheet (or seed_labels.csv)
are skipped, so a second round only asks about new bins.

    python3 dev_tools/label_sheet.py period-study-2026-10 --probe          # first time; drives mounted
    python3 dev_tools/label_sheet.py period-study-2026-10 --name round1

--probe reads each package's start timecode from its source video (package.json "source") and
caches it in labels/timecode.json. Without a cached start timecode a tape's rows are written
from 00:00:00:00 and flagged in the notes column.

Filling in: defect is one of DEFECTS (separate several with '+', e.g. dropout+noise), severity 0
(nothing worth a period), 1 (visible) or 2 (obvious/serious). A row left blank counts as unlabeled.
"""
import argparse
import csv
import json
import logging
import random
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "replays"))
from bin_table import find_packages, package_rows  # noqa: E402
from _selection import load_package  # noqa: E402

from AV_Spex.checks.qct_parse import _tc_format_timecode, _tc_parse_start_timecode
from AV_Spex.utils import ffprobe_probe
from AV_Spex.utils.log_setup import logger

import os
LABELS = Path(os.environ.get("AVSPEX_CORPUS", "~/git/JPC_AV/avspex_corpus")).expanduser() / "labels"
BIN = 10.0

DEFECTS = ("none", "dropout", "head_switching_tracking", "sync_loss_roll", "illegal_levels",
           "chroma_error", "noise", "signal_loss_freeze", "graphics_slate_only", "other")

# (column in bin_table's output, direction): '+' means high is suspicious, '-' low.
# New tags chosen from the `bin_table.py --screen` of period-study-2026-10 (present in every
# report, not flat, not redundant with a scored metric, not a luma/motion proxy):
NEW_CANDIDATES = (
    ("udif_max", "+"),          # chroma temporal spike, U   (rho vs YDIF 0.44)
    ("vdif_max", "+"),          # chroma temporal spike, V   (0.45)
    ("ydif_max", "+"),          # single-frame luma jump: sync loss / roll, but also hard cuts
    ("psnr_psnr_y_min", "-"),   # worst inter-field PSNR: fields disagreeing
    ("satlow_mean", "+"),       # raised chroma floor (noise/chroma error); ~independent of luma/motion
    ("tout_max", "+"),          # TOUT spike, beside the scored mean
    ("brng_min", "+"),          # illegal levels sustained through the whole bin
)
# Today's scored metrics, so their weights can be judged on the same labels.
SCORED_CANDIDATES = (
    ("bp_brng_mean", "+"), ("bp_satmax_max", "+"), ("bp_tout_mean", "+"),
    ("bp_vrep_mean", "+"), ("bp_deflicker_absmax", "+"),
)
CANDIDATES = NEW_CANDIDATES + SCORED_CANDIDATES


def selector(col, direction):
    return f"{col}{direction}"


def ranked_bins(rows, col, direction):
    """Analyzable bins best-first for one tag; empty when the tag has no spread on this tape."""
    vals = [(r[col], r["bin_start"]) for r in rows if r.get(col) is not None]
    if len(vals) < 2 or min(v for v, _ in vals) == max(v for v, _ in vals):
        return []
    sign = -1 if direction == "+" else 1
    return [b for _, b in sorted(vals, key=lambda vb: (sign * vb[0], vb[1]))]


def choose_bins(rows, per_tape, n_controls, rng, skip):
    """{bin_start: [selectors]} for one tape. Every selector a chosen bin qualifies for is
    recorded, so a bin picked as a control that is also a tag's peak counts for both."""
    rows = [r for r in rows if r["analyzable"]]
    pool = [r["bin_start"] for r in rows if r["bin_start"] not in skip]
    qualifies = {}
    tops, seconds = [], []
    for col, d in CANDIDATES:
        ranked = [b for b in ranked_bins(rows, col, d) if b not in skip]
        if ranked:
            qualifies.setdefault(ranked[0], []).append(f"top:{selector(col, d)}")
            tops.append(ranked[0])
        if len(ranked) > 1 and (col, d) in NEW_CANDIDATES:
            qualifies.setdefault(ranked[1], []).append(f"2nd:{selector(col, d)}")
            seconds.append(ranked[1])
    evidence = [r["bin_start"] for r in rows if r["evidence"] and r["bin_start"] not in skip]
    for b in evidence:
        qualifies.setdefault(b, []).append("evidence")

    chosen = {}
    for b in rng.sample(pool, min(n_controls, len(pool))):
        chosen[b] = ["control"]
    for b in tops + evidence + seconds:
        if len(chosen) >= per_tape:
            break
        chosen.setdefault(b, [])
    for b in chosen:
        chosen[b] = sorted(set(chosen[b] + qualifies.get(b, [])))
    return chosen


def probe_timecodes(pkgs, cache):
    for pkg in pkgs:
        info = json.loads((pkg / "package.json").read_text())
        vid = info["video_id"]
        if vid in cache:
            continue
        video = Path(info.get("source") or "") / (info.get("video_file") or "")
        if not video.is_file():
            print(f"{vid}: source video not reachable ({video}); start timecode not probed", file=sys.stderr)
            continue
        tc = ffprobe_probe.start_timecode(str(video))
        cache[vid] = {"start_timecode": tc, "fps": ffprobe_probe.frame_rate(str(video))}
        print(f"{vid}: start timecode {tc or 'none (00:00:00:00)'}", file=sys.stderr)
    return cache


def labeled_bins():
    """(video_id, bin_start) already labeled, in any filled sheet or the seed file."""
    done = set()
    for sheet in LABELS.glob("sheet_*.csv"):
        key_path = sheet.with_name(sheet.name.replace("sheet_", "key_", 1)).with_suffix(".json")
        if not key_path.exists():
            continue
        key = json.loads(key_path.read_text())
        for row in csv.DictReader(open(sheet)):
            if (row.get("defect") or "").strip() and row["blind_id"] in key:
                k = key[row["blind_id"]]
                done.add((k["video_id"], float(k["bin_start"])))
    seed = LABELS / "seed_labels.csv"
    if seed.exists():
        for row in csv.DictReader(open(seed)):
            done.add((row["video_id"], float(row["bin_start"])))
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--name", default=date.today().isoformat())
    ap.add_argument("--per-tape", type=int, default=12)
    ap.add_argument("--controls", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--probe", action="store_true", help="read start timecodes from the source videos")
    args = ap.parse_args()
    logger.setLevel(logging.ERROR)
    LABELS.mkdir(parents=True, exist_ok=True)

    pkgs = find_packages(args.runs)
    tc_path = LABELS / "timecode.json"
    tc_cache = json.loads(tc_path.read_text()) if tc_path.exists() else {}
    if args.probe:
        tc_cache = probe_timecodes(pkgs, tc_cache)
        tc_path.write_text(json.dumps(tc_cache, indent=2, sort_keys=True))

    sheet_path = LABELS / f"sheet_{args.name}.csv"
    key_path = LABELS / f"key_{args.name}.json"
    if sheet_path.exists():
        sys.exit(f"{sheet_path} exists; pick another --name (it may already hold labels)")

    skip = labeled_bins()
    sheet, key = [], {}
    for pkg in pkgs:
        ctx = load_package(pkg)
        rows, _ = package_rows(ctx, 6, 30)
        rng = random.Random(f"{args.seed}:{ctx.name}")
        chosen = choose_bins(rows, args.per_tape, args.controls, rng,
                             {b for v, b in skip if v == ctx.name})
        tc = tc_cache.get(ctx.name) or {}
        fps = tc.get("fps") or ctx.meta.get("fps")
        start_frames, drop = _tc_parse_start_timecode(tc.get("start_timecode"), max(1, round(fps or 30)))
        note = "" if ctx.name in tc_cache else "start TC not probed: positions from 00:00:00:00"
        for i, b in enumerate(sorted(chosen), 1):
            blind = f"{ctx.name[-5:]}-{i:02d}"
            sheet.append({"video_id": ctx.name, "tc_in": _tc_format_timecode(b, fps, start_frames, drop),
                          "tc_out": _tc_format_timecode(b + BIN, fps, start_frames, drop),
                          "blind_id": blind, "defect": "", "severity": "", "notes": note})
            key[blind] = {"video_id": ctx.name, "bin_start": b, "selectors": chosen[b]}
        print(f"{ctx.name}: {len(chosen)} bins", file=sys.stderr)

    with open(sheet_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["video_id", "tc_in", "tc_out", "blind_id", "defect", "severity", "notes"])
        w.writeheader()
        w.writerows(sheet)
    key_path.write_text(json.dumps(key, indent=1))
    print(f"\nWrote {len(sheet)} bins to {sheet_path}\nKey (don't open while labeling): {key_path}")
    print(f"defect values: {', '.join(DEFECTS)}; severity 0/1/2")


if __name__ == "__main__":
    main()
