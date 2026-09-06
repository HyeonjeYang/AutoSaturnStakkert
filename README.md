# AutoSaturnStakkert

Lightweight planetary video preprocessing tools for automatic tracking, centering, and AutoStakkert!-ready output.

- `autosaturnstakkert.py` → uncompressed **RGB24 AVI**
- `cvsaturnstakkert.py` → **SER**

Both scripts detect a bright planetary target, track it frame-by-frame, keep it centered, and crop it to a configurable ROI.

## Requirements

- Python 3
- OpenCV
- NumPy
- FFmpeg *(AVI version only)*

Install Python dependencies:

```bash
py -m pip install opencv-python numpy
```

For `autosaturnstakkert.py`, FFmpeg must also be installed and available in your system `PATH`.

## Usage

### AVI output

```bash
py autosaturnstakkert.py "C:\path\to\video.mp4"
```

Output:

```text
video_centered_AS4.avi
```

### SER output

```bash
py cvsaturnstakkert.py "C:\path\to\video.mp4"
```

Output:

```text
video_centered.ser
```

## Options

Examples:

```bash
py autosaturnstakkert.py "video.mp4" --roi 400
```

```bash
py autosaturnstakkert.py "video.mp4" --roi 500x350 --threshold 160
```

```bash
py cvsaturnstakkert.py "video.mp4" --roi 400x300 --max-jump 200
```

Show all options:

```bash
py autosaturnstakkert.py --help
```

```bash
py cvsaturnstakkert.py --help
```

## Workflow

```text
Input video
    ↓
Target detection & tracking
    ↓
Centering + ROI crop
    ↓
AVI or SER
    ↓
AutoStakkert!
```

These scripts are preprocessing tools only. Alignment, stacking, and sharpening are performed separately.

<img width="839" height="562" alt="image" src="https://github.com/user-attachments/assets/11cd57e5-02e3-4631-b1bd-5bc7b0f05469" />
