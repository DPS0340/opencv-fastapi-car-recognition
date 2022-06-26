#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pathlib import Path
import uuid

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import cv2

import os

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="static")

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


@app.post("/predict")
async def predict(video: UploadFile = File()):
    if video is None:
        return {"error": "video not given"}
    if not video.content_type.startswith("video"):
        return {"error": "file is not video"}

    ext = video.filename.split(".")[-1]

    video_id_without_ext = str(uuid.uuid4())

    video_id = f"{video_id_without_ext}.{ext}"

    # making parent folders

    video_folder = Path("videos/original")
    video_folder.mkdir(exist_ok=True, parents=True)

    video_folder = Path("videos/converted")
    video_folder.mkdir(exist_ok=True, parents=True)

    file_location = f"videos/original/{video_id}"
    with open(file_location, "wb+") as file_object:
        file_object.write(video.file.read())

    converted_video_id = detect_cars(video_id_without_ext, file_location)

    return {"videoId": converted_video_id}


def detect_cars(video_id_without_ext: str, file_location: str):
    cascade_src = 'cars.xml'

    video = cv2.VideoCapture(file_location)
    car_cascade = cv2.CascadeClassifier(cascade_src)

    if (video.isOpened() == False):
        print("Error reading video file")

    frame_width = int(video.get(3))
    frame_height = int(video.get(4))

    fps = int(video.get(cv2.CAP_PROP_FPS))

    size = (frame_width, frame_height)

    # webm + VP80
    # https://stackoverflow.com/a/55987868

    video_id = f"{video_id_without_ext}.webm"

    result_location = f"videos/converted/{video_id}"

    result = cv2.VideoWriter(result_location,
                             cv2.VideoWriter_fourcc(*'VP80'),
                             fps, size)

    while True:
        ret, img = video.read()
        if type(img) == type(None) or ret != True:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        cars = car_cascade.detectMultiScale(gray, 1.1, 1)

        for (x, y, w, h) in cars:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)

        result.write(img)

    video.release()
    result.release()

    return video_id


def iterfile(path: str):
    with open(path, mode="rb") as file_like:
        yield from file_like


@app.get("/view/{video_id}")
async def predict(video_id: str, request: Request):
    ext = video_id.split('.')[-1]

    return templates.TemplateResponse(
        'view.html', {'request': request, 'video_id': video_id, 'ext': ext},
        status_code=200
    )


@ app.get("/videos/{video_id}")
async def serve_video(video_id: str, request: Request):
    ext = video_id.split(".")[-1]
    content_type = f"video/{ext}"

    video_path = f"videos/converted/{video_id}"

    return FileResponse(video_path, media_type=content_type)
