import argparse
import math
import os
import struct
import sys

import cv2
import numpy as np


SER_HEADER = struct.Struct("<14s7I40s40s40s2q")  # 178-byte SER v3 header
FRAME_COUNT_OFFSET = 38  # byte offset of the FrameCount field
COLOR_RGB = 100


def parse_roi(s):
    s = s.lower()
    if "x" in s:
        w, h = map(int, s.split("x", 1))
    else:
        w = h = int(s)
    if w <= 0 or h <= 0:
        raise argparse.ArgumentTypeError("ROI must be positive.")
    return w, h


def candidates(gray, threshold, min_area, ox=0, oy=0):
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    n, _, stats, centers = cv2.connectedComponentsWithStats(mask, 8)

    out = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            out.append((centers[i][0] + ox, centers[i][1] + oy, area))
    return out


def choose(cands, prev, max_jump):
    if not cands:
        return None
    if prev is None:
        x, y, _ = max(cands, key=lambda c: c[2])
        return x, y

    px, py = prev
    valid = []
    for x, y, area in cands:
        d = math.hypot(x - px, y - py)
        if d <= max_jump:
            valid.append((d, -area, x, y))

    if not valid:
        return None
    _, _, x, y = min(valid)
    return x, y


def detect(gray, prev, threshold, min_area, max_jump, search_margin):
    h, w = gray.shape

    if prev is None:
        return choose(candidates(gray, threshold, min_area), None, max_jump)

    px, py = prev
    x1 = max(0, int(px - search_margin))
    y1 = max(0, int(py - search_margin))
    x2 = min(w, int(px + search_margin + 1))
    y2 = min(h, int(py + search_margin + 1))

    local = gray[y1:y2, x1:x2]
    found = choose(
        candidates(local, threshold, min_area, x1, y1),
        prev,
        max_jump,
    )
    if found is not None:
        return found

    return choose(candidates(gray, threshold, min_area), prev, max_jump)


def crop(frame, center, roi_w, roi_h):
    h, w = frame.shape[:2]
    cx, cy = center
    x1 = int(round(cx - roi_w / 2))
    y1 = int(round(cy - roi_h / 2))
    x2, y2 = x1 + roi_w, y1 + roi_h

    pl, pt = max(0, -x1), max(0, -y1)
    pr, pb = max(0, x2 - w), max(0, y2 - h)

    if pl or pt or pr or pb:
        frame = cv2.copyMakeBorder(
            frame, pt, pb, pl, pr,
            cv2.BORDER_CONSTANT, value=(0, 0, 0)
        )
        x1 += pl
        y1 += pt

    out = frame[y1:y1 + roi_h, x1:x1 + roi_w]
    if out.shape[:2] != (roi_h, roi_w):
        raise RuntimeError("Unexpected crop size.")
    return out


def write_ser_header(f, width, height, color_id, bit_depth=8):
    # frame_count written as 0, patched at the end via patch_frame_count
    f.write(SER_HEADER.pack(
        b"LUCAM-RECORDER", 0, color_id, 0,
        width, height, bit_depth, 0,
        b"", b"", b"", 0, 0,
    ))


def patch_frame_count(f, count):
    f.seek(FRAME_COUNT_OFFSET)
    f.write(struct.pack("<I", count))


def main():
    p = argparse.ArgumentParser(
        description="Track, center and crop a planetary video into a SER file for AutoStakkert! 4."
    )
    p.add_argument("input", help="Input video path")
    p.add_argument("--roi", type=parse_roi, default=(300, 300),
                   help="Crop size: 300 or 500x350 (default: 300x300)")
    p.add_argument("--threshold", type=int, default=180,
                   help="Brightness threshold 0-255 (default: 180)")
    p.add_argument("--max-jump", type=float, default=150,
                   help="Maximum frame-to-frame movement in px (default: 150)")
    p.add_argument("--search-margin", type=int, default=120,
                   help="Local search margin in px (default: 120)")
    p.add_argument("--max-failures", type=int, default=10,
                   help="Allowed consecutive tracking failures (default: 10)")
    p.add_argument("--min-area", type=int, default=3,
                   help="Minimum bright-object area in px (default: 3)")
    p.add_argument("-o", "--output", help="Custom output .ser path")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()

    if not 0 <= args.threshold <= 255:
        p.error("--threshold must be between 0 and 255.")
    if not os.path.isfile(args.input):
        sys.exit(f"ERROR: input file not found:\n{args.input}")

    input_path = os.path.abspath(args.input)
    stem, _ = os.path.splitext(input_path)
    output_path = os.path.abspath(args.output) if args.output else stem + "_centered_AS4.ser"

    if os.path.exists(output_path) and not args.overwrite:
        sys.exit(f"ERROR: output already exists:\n{output_path}\nUse --overwrite to replace it.")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        sys.exit("ERROR: could not open input video.")

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    roi_w, roi_h = args.roi

    f = open(output_path, "wb")
    write_ser_header(f, roi_w, roi_h, COLOR_RGB)

    prev = None
    failures = 0
    written = 0
    frame_no = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_no += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            center = detect(
                gray, prev,
                args.threshold,
                args.min_area,
                args.max_jump,
                args.search_margin,
            )

            if center is None:
                failures += 1
                if prev is None:
                    continue
                if failures > args.max_failures:
                    raise RuntimeError(f"Tracking lost at frame {frame_no}.")
                center = prev
            else:
                prev = center
                failures = 0

            frame = crop(frame, center, roi_w, roi_h)

            # OpenCV = BGR, SER color_id=100 expects RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.ascontiguousarray(frame)

            f.write(frame.tobytes())
            written += 1

            if total > 0:
                print(
                    f"\rProcessing {frame_no}/{total} "
                    f"({frame_no / total * 100:5.1f}%)",
                    end="",
                )

    except (KeyboardInterrupt, Exception) as e:
        cap.release()
        patch_frame_count(f, written)
        f.close()
        if isinstance(e, KeyboardInterrupt):
            sys.exit("\nCancelled.")
        sys.exit(f"\nERROR: {e}")

    cap.release()
    patch_frame_count(f, written)
    f.close()

    if written == 0:
        sys.exit("\nERROR: no frames were written.")

    print(f"\nDone: {output_path}")
    print(f"Frames: {written} | ROI: {roi_w}x{roi_h} | Format: SER (RGB, 8-bit)")


if __name__ == "__main__":
    main()
