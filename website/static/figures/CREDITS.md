# Detection example credits

## Photos

The photos in `detect-01.jpg` to `detect-08.jpg` come from the public **TrashNet** dataset
(`dataset-resized.zip`, https://huggingface.co/datasets/garythung/trashnet).

- Authors: Gary Thung and Mindy Yang
- Licence: MIT
- Processing: re-encoded as JPEG (quality 82). The source images are already 512 x 384 px, so
  they were not enlarged. No boxes are drawn into the image files.

## Detections

`detections.json` holds the raw output of the MIRA detector, not hand-edited.

- Model: `src/assets/models/detection/mira_exp019.pt` (YOLO11n; classes glass, metal, paper, plastic, trash)
- Inference: Ultralytics 8.4.216, CPU, `conf=0.25`, `iou=0.45`, `imgsz=640`
- Box format: `[x1, y1, x2, y2]`, normalised 0..1 relative to the exported image.
- Detections are run on the exported JPEG itself, so they match the file shown.

## What these examples are, and are not

These photos are public TrashNet images. They are **not guaranteed to be held-out validation
images**: TrashNet is one of the datasets listed in the training recipe for `mira_exp019`
(`mira_exp019.yaml`), and the repository cannot tell which TrashNet images ended up in the
training split. They are therefore **illustrative examples, not evidence of accuracy**.
Accuracy claims should rest on the held-out metrics in the research section only.

Two examples are deliberately not clean successes:

- `detect-07.jpg`: a crushed plastic water bottle with no detection above the 0.25 threshold.
- `detect-08.jpg`: a cardboard box (MIRA has no cardboard class) labelled `paper`.

Most TrashNet photos show a single object filling the frame, and the model usually answers with a
near full-frame box. Real detections on cluttered scenes will look different.
