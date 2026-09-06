# AutoSaturnStakkert

A lightweight planetary video preprocessor for automatic tracking, centering, and AutoStakkert!-compatible RGB AVI generation.

It tracks a bright planetary target, keeps it centered, crops the video to a configurable ROI, and outputs an **uncompressed RGB24 AVI** for AutoStakkert! 4.

## Requirements

- Python 3
- FFmpeg
- OpenCV
- NumPy

Install Python dependencies:

```bash
py -m pip install opencv-python numpy
```

FFmpeg must be installed and available in your system `PATH`.

## Usage

```bash
py autosaturnstakkert.py "C:\path\to\your-video.mp4"
```

The default output is:

```text
your-video_centered_AS4.avi
```

### Default parameters

| Option | Default | Description |
|---|---:|---|
| `--roi` | `300x300` | Output crop size |
| `--threshold` | `180` | Detection threshold |
| `--max-jump` | `150` | Maximum movement between frames (px) |
| `--search-margin` | `120` | Local search margin (px) |
| `--max-failures` | `10` | Allowed consecutive tracking failures |
| `--min-area` | `3` | Minimum detected object area |

## Examples

Larger square ROI:

```bash
py autosaturnstakkert.py "video.mp4" --roi 400
```

Rectangular ROI:

```bash
py autosaturnstakkert.py "video.mp4" --roi 500x350
```

Adjust detection and tracking:

```bash
py autosaturnstakkert.py "video.mp4" --threshold 160 --max-jump 200
```

Combine options:

```bash
py autosaturnstakkert.py "video.mp4" --roi 400x300 --threshold 160 --max-jump 200
```

Show all options:

```bash
py autosaturnstakkert.py --help
```

## Output

```text
Input video
    ↓
Target detection & tracking
    ↓
Centering + ROI crop
    ↓
Uncompressed RGB24 AVI
    ↓
AutoStakkert! 4
```

AutoSaturnStakkert is a **preprocessing tool only**. Alignment, stacking, and sharpening are performed separately.


<img width="839" height="562" alt="image" src="https://github.com/user-attachments/assets/11cd57e5-02e3-4631-b1bd-5bc7b0f05469" />

[C0002_centered_AS4_lapl5_ap1.tif](https://github.com/user-attachments/files/31881264/C0002_centered_AS4_lapl5_ap1.tif)
