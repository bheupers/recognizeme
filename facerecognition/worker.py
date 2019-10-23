import io
import json
import signal
import pickle
from typing import Tuple, Dict, Any, Optional
import numpy as np

import face_recognition
from PIL import Image


_encodings = None
_detection_method = None


def warm(encodings_path: str, detection_method: str) -> None:
    # should be executed only in child processes
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    global _encodings
    if _encodings is None:
        _encodings = pickle.loads(open(encodings_path, "rb").read())
    global _detection_method
    if _detection_method is None:
        _detection_method = detection_method


def clean() -> None:
    # should be executed only in child processes
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    global _encodings
    global _detection_method
    _encodings = None
    _detection_method = None


def prepare_image(image: Image) -> Image:
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # image = image.resize(target)
    image = np.asarray(image)
    # image = np.expand_dims(image, axis=0)
    # image = imagenet_utils.preprocess_input(image)
    return image


def recognize(raw_data: bytes, encodings: Optional[Any] = None, detection_method: Optional[str] = None) -> bytes:
    if encodings is None:
        encodings = _encodings

    if encodings is None:
        raise RuntimeError('Encodings should be loaded first')

    if detection_method is None:
        detection_method = _detection_method

    if detection_method is None:
        raise RuntimeError('Detection method should be set')

    image = Image.open(io.BytesIO(raw_data))
    data: Dict[str, Any] = {}
    image = prepare_image(image)

    # print("[INFO] recognizing faces...")
    boxes = face_recognition.face_locations(image,model=detection_method)
    # start = elapsed("face_locations", start)
    received_encodings = face_recognition.face_encodings(image, boxes)
    # start = elapsed("face_encodings", start)

    names = []

    # loop over the facial embeddings
    for i, encoding in enumerate(received_encodings):
        # attempt to match each face in the input image to our known
        # encodings
        matches = face_recognition.compare_faces(encodings['encodings'],
                                                 encoding)
        # start = elapsed(f"compare_faces {i}", start)

        name = "Unknown"
        # check to see if we have found a match
        if True in matches:
            # find the indexes of all matched faces then initialize a
            # dictionary to count the total number of times each face
            # was matched
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}

            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchedIdxs:
                name = encodings["names"][i]
                counts[name] = counts.get(name, 0) + 1

            # determine the recognized face with the largest number of
            # votes (note: in the event of an unlikely tie Python will
            # select first entry in the dictionary)
            name = max(counts, key=counts.get)

        # update the list of names
        names.append(name.capitalize())

    recognitions = {}
    for ((top, right, bottom, left), name) in zip(boxes, names):
        recognitions[name] = { 'top': top, 'bottom': bottom, 'right': right, 'left': left}
    data['recognitions'] = recognitions
    data['success'] = True
    return json.dumps(data).encode('utf-8')


def add_face(raw_data: bytes, encodings: Optional[Any]=None) -> bytes:
    if encodings is None:
        encodings = _encodings

    if encodings is None:
        raise RuntimeError('Encodings should be loaded first')

    data: Dict[str, Any] = {}
    data['success'] = True
    return json.dumps(data).encode('utf-8')





