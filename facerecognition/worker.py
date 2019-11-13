import datetime
import io
import json
import logging
import os
import signal
import pickle
from typing import Tuple, Dict, Any, Optional
import numpy as np
import random

from PIL import Image

_encodings = None
_detection_method = None
_encodings_path = None
_encodings_length = 0

MAX_EXTRA_ENCODINGS = 16

_logger = logging.getLogger(__name__)

def warm(encodings_path: str, detection_method: str) -> None:
    # should be executed only in child processes
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    random.seed()
    global _encodings_path
    _encodings_path = encodings_path
    global _encodings_length
    global _encodings
    if _encodings is None:
        if os.path.isfile(encodings_path):
            _encodings = pickle.loads(open(encodings_path, "rb").read())
        else:
            _encodings = {
                'encodings': [],
                'names':[]
            }
        _encodings_length = len(_encodings['encodings'])

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


def recognize(file_data: bytes, encodings: Optional[Any] = None, detection_method: Optional[str] = None) -> bytes:
    # face_recognition cannot be imported at the top because
    # CUDA dependency can only be active in one process at the same
    import face_recognition
    if encodings is None:
        encodings = _encodings

    if encodings is None:
        raise RuntimeError('Encodings should be loaded first')

    if detection_method is None:
        detection_method = _detection_method

    if detection_method is None:
        raise RuntimeError('Detection method should be set')

    image = Image.open(io.BytesIO(file_data))
    data: Dict[str, Any] = {}
    image = prepare_image(image)

    # print("[INFO] recognizing faces...")
    boxes = face_recognition.face_locations(image, model=detection_method)
    # start = elapsed("face_locations", start)
    received_encodings = face_recognition.face_encodings(image, boxes)
    # start = elapsed("face_encodings", start)

    names = []

    # loop over the facial embeddings
    for i, encoding in enumerate(received_encodings):
        # attempt to match each face in the input image to our known encodings
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
        names.append(name.title())

    recognitions = {}
    for ((top, right, bottom, left), name) in zip(boxes, names):
        recognitions[name] = {'top': top, 'bottom': bottom, 'right': right, 'left': left}
    data['recognitions'] = recognitions
    data['success'] = True
    _logger.info(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Recognized : {names}")
    return json.dumps(data).encode('utf-8')


def add_face(name: str, file_data: bytes, encodings: Optional[Any] = None,
             detection_method: Optional[str] = None) -> bytes:
    import face_recognition

    if encodings is None:
        encodings = _encodings

    if encodings is None:
        raise RuntimeError('Encodings should be loaded first')

    if detection_method is None:
        detection_method = _detection_method

    if detection_method is None:
        raise RuntimeError('Detection method should be set')

    image = Image.open(io.BytesIO(file_data))
    data: Dict[str, Any] = {}
    image = prepare_image(image)
    name = name.lower()

    boxes = face_recognition.face_locations(image, model=detection_method)
    if boxes and len(boxes) == 1:
        # compute the facial embedding for the face
        received_encodings = face_recognition.face_encodings(image, boxes)
        # We should have only one face in the image
        if len(encodings['encodings']) > _encodings_length + MAX_EXTRA_ENCODINGS:
            # Replace on of the extra encodings
            index = _encodings_length + random.randrange(_encodings_length, _encodings_length + MAX_EXTRA_ENCODINGS)
        else:
            index = _encodings_length
        encodings['encodings'].insert(index, received_encodings[0])
        encodings["names"].insert(index, name)
        # Write encodings to file. For now we do not write
        # After restart everything is gone
        # f = open(_encodings_path, "wb")
        # f.write(pickle.dumps(data))
        # f.close()
        data['faces_added'] = [name.title()]
        data['message'] = 'one face added'
        data['success'] = True
    else:
        data['faces_added'] = []
        data['message'] = 'no faces found in image' if len(boxes) == 0 else 'more then one face found'
        data['success'] = False
    _logger.info(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} Add face: {data['message']}, ({str(data['faces_added'])})")
    return json.dumps(data).encode('utf-8')
