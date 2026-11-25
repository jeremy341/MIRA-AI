"""Batch input API. Owner and contract: docs/dashboard-v2/CONTRACT.md."""

from __future__ import annotations

import math
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

import cv2
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile

from .. import batch_runner, model_runner

router = APIRouter(tags=["Batch input"])

MAX_VIDEO_BYTES = 500 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_MULTIPART_IMAGES = 200
MAX_DIRECTORY_IMAGES = 2000
UPLOAD_CHUNK_BYTES = 1024 * 1024
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def _cleanup(path: Path | None) -> None:
    if path is not None:
        shutil.rmtree(path, ignore_errors=True)


def _validate_common(model_name: object, confidence: object, name: object) -> tuple[str, float, str | None]:
    if not isinstance(model_name, str) or not model_name.strip():
        raise HTTPException(status_code=422, detail="model_name is required.")
    model_name = model_name.strip()
    try:
        model_runner.resolve_model_path(model_name)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        if isinstance(confidence, bool):
            raise ValueError
        parsed_confidence = float(confidence)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="confidence must be between 0.05 and 1.") from exc
    if not math.isfinite(parsed_confidence) or not 0.05 <= parsed_confidence <= 1:
        raise HTTPException(status_code=422, detail="confidence must be between 0.05 and 1.")

    if name is not None and not isinstance(name, str):
        raise HTTPException(status_code=422, detail="name must be a string.")
    return model_name, parsed_confidence, name.strip() if isinstance(name, str) and name.strip() else None


def _natural_key(path: Path, root: Path) -> list[tuple[int, int | str]]:
    relative = path.relative_to(root).as_posix().casefold()
    return [(0, int(part)) if part.isdigit() else (1, part) for part in re.split(r"(\d+)", relative)]


def _directory_images(directory: object, recursive: object) -> list[Path]:
    if not isinstance(directory, str) or not directory.strip():
        raise HTTPException(status_code=422, detail="directory is required.")
    if not isinstance(recursive, bool):
        raise HTTPException(status_code=422, detail="recursive must be true or false.")
    root = Path(directory).expanduser()
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise HTTPException(status_code=422, detail="directory paths must not traverse symbolic links.")
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=422, detail="directory must exist and be a directory.")

    images: list[Path] = []
    if recursive:
        for folder_name, directory_names, filenames in os.walk(root, followlinks=False):
            folder = Path(folder_name)
            directory_names[:] = [name for name in directory_names if not (folder / name).is_symlink()]
            for filename in filenames:
                path = folder / filename
                if not path.is_symlink() and path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                    images.append(path)
                    if len(images) > MAX_DIRECTORY_IMAGES:
                        raise HTTPException(
                            status_code=413, detail="A directory batch can contain at most 2000 images."
                        )
    else:
        for path in root.iterdir():
            if not path.is_symlink() and path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                images.append(path)
                if len(images) > MAX_DIRECTORY_IMAGES:
                    raise HTTPException(status_code=413, detail="A directory batch can contain at most 2000 images.")

    images.sort(key=lambda path: _natural_key(path, root))
    if not images:
        raise HTTPException(status_code=422, detail="No JPEG or PNG images were found in the directory.")
    return images


async def _save_upload(upload: UploadFile, destination: Path, maximum_bytes: int) -> None:
    if upload.size is not None and upload.size > maximum_bytes:
        raise HTTPException(status_code=413, detail=f"{upload.filename or 'File'} exceeds the size limit.")
    written = 0
    with destination.open("wb") as target:
        while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
            written += len(chunk)
            if written > maximum_bytes:
                raise HTTPException(status_code=413, detail=f"{upload.filename or 'File'} exceeds the size limit.")
            target.write(chunk)
    if written == 0:
        raise HTTPException(status_code=422, detail=f"{upload.filename or 'File'} is empty.")


@router.post("/batch/video", status_code=202)
async def batch_video(
    video: Annotated[UploadFile, File()],
    model_name: Annotated[str, Form()],
    confidence: Annotated[float, Form(ge=0.05, le=1)] = 0.25,
    frame_stride: Annotated[int, Form(ge=1, le=120)] = 5,
    name: Annotated[str | None, Form()] = None,
) -> dict[str, str]:
    extension = Path(video.filename or "").suffix.lower()
    if extension not in VIDEO_SUFFIXES:
        await video.close()
        raise HTTPException(status_code=415, detail="Choose an MP4, AVI, MOV, or MKV video.")
    try:
        model_name, confidence, name = _validate_common(model_name, confidence, name)
    except HTTPException:
        await video.close()
        raise
    if video.size is not None and video.size > MAX_VIDEO_BYTES:
        await video.close()
        raise HTTPException(status_code=413, detail="Choose a video no larger than 500 MB.")

    temporary_path = Path(tempfile.mkdtemp(prefix="mira-batch-video-"))
    video_path = temporary_path / f"input{extension}"
    capture = None
    try:
        await _save_upload(video, video_path, MAX_VIDEO_BYTES)
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise HTTPException(status_code=422, detail="The video could not be opened or decoded.")
        raw_frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(round(raw_frame_count)) if math.isfinite(raw_frame_count) else 0
        first_frame_ok, first_frame = capture.read()
        if frame_count <= 0:
            raise HTTPException(status_code=422, detail="The video contains no frames.")
        if not first_frame_ok or first_frame is None or width <= 0 or height <= 0 or not math.isfinite(fps) or fps <= 0:
            raise HTTPException(status_code=422, detail="The video could not be decoded or has invalid frame metadata.")
        capture.release()
        capture = None
        job, session_id = batch_runner.submit_video(
            temporary_path=temporary_path,
            video_path=video_path,
            model_name=model_name,
            confidence=confidence,
            frame_stride=frame_stride,
            name=name,
            frame_count=frame_count,
            fps=fps,
        )
        return {"job_id": job.id, "session_id": session_id}
    except HTTPException:
        _cleanup(temporary_path)
        raise
    except (OSError, cv2.error) as exc:
        _cleanup(temporary_path)
        raise HTTPException(status_code=422, detail=f"The video could not be decoded: {exc}") from exc
    except Exception:
        _cleanup(temporary_path)
        raise
    finally:
        if capture is not None:
            capture.release()
        await video.close()


@router.post("/batch/images", status_code=202)
async def batch_images(request: Request) -> dict[str, str]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    temporary_path: Path | None = None
    try:
        if content_type == "application/json":
            try:
                body = await request.json()
            except ValueError as exc:
                raise HTTPException(status_code=422, detail="The JSON body is invalid.") from exc
            if not isinstance(body, dict):
                raise HTTPException(status_code=422, detail="The request body must be a JSON object.")
            if "images" in body:
                raise HTTPException(status_code=422, detail="Choose either uploaded images or a directory.")
            model_name, confidence, name = _validate_common(
                body.get("model_name"), body.get("confidence", 0.25), body.get("name")
            )
            image_paths = _directory_images(body.get("directory"), body.get("recursive", False))
        elif content_type == "multipart/form-data":
            try:
                form = await request.form()
            except Exception as exc:
                raise HTTPException(status_code=422, detail="The multipart form could not be read.") from exc
            uploads = form.getlist("images")
            if form.get("directory") is not None:
                raise HTTPException(status_code=422, detail="Choose either uploaded images or a directory.")
            if not uploads:
                raise HTTPException(status_code=422, detail="Upload at least one JPEG or PNG image.")
            if len(uploads) > MAX_MULTIPART_IMAGES:
                raise HTTPException(status_code=413, detail="A multipart batch can contain at most 200 images.")
            model_name, confidence, name = _validate_common(
                form.get("model_name"), form.get("confidence", 0.25), form.get("name")
            )

            temporary_path = Path(tempfile.mkdtemp(prefix="mira-batch-images-"))
            image_paths = []
            for index, upload in enumerate(uploads):
                if not isinstance(upload, StarletteUploadFile):
                    raise HTTPException(status_code=422, detail="Each images field must contain an uploaded file.")
                original_name = Path(upload.filename or "image").name
                extension = Path(original_name).suffix.lower()
                if extension not in IMAGE_SUFFIXES:
                    raise HTTPException(status_code=415, detail=f"{original_name} is not a JPEG or PNG image.")
                safe_name = f"{index:04d}_{original_name}"
                destination = temporary_path / safe_name
                await _save_upload(upload, destination, MAX_IMAGE_BYTES)
                try:
                    batch_runner.decode_image(destination)
                except ValueError as exc:
                    raise HTTPException(status_code=422, detail=f"{original_name}: {exc}") from exc
                image_paths.append(destination)
        else:
            raise HTTPException(status_code=415, detail="Use multipart form data or a JSON directory request.")

        job, session_id = batch_runner.submit_images(
            temporary_path=temporary_path,
            image_paths=image_paths,
            model_name=model_name,
            confidence=confidence,
            name=name,
        )
        return {"job_id": job.id, "session_id": session_id}
    except HTTPException:
        _cleanup(temporary_path)
        raise
    except OSError as exc:
        _cleanup(temporary_path)
        raise HTTPException(status_code=422, detail=f"The image batch could not be read: {exc}") from exc
    except Exception:
        _cleanup(temporary_path)
        raise
    finally:
        if content_type == "multipart/form-data":
            try:
                await request.close()
            except Exception:
                pass
