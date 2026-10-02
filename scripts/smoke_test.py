"""Import each built package and use its compiled code, the way Fuzzy Macro does.

Run with the Python the wheel was installed into: smoke_test.py opencv-python
"""

import sys


def opencv():
    import cv2
    import numpy as np

    screen = np.zeros((120, 160, 4), dtype=np.uint8)
    screen[40:60, 50:80] = (255, 255, 255, 255)
    bgr = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    template = gray[35:65, 45:85].copy()
    _, score, _, location = cv2.minMaxLoc(cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED))
    assert score > 0.99 and location == (45, 35), (score, location)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))
    count = cv2.connectedComponentsWithStats(mask)[0]
    assert count == 2, count
    # AI gather runs its ONNX models through cv2.dnn
    blob = cv2.dnn.blobFromImage(bgr, 1 / 255.0, (64, 64), swapRB=True)
    assert blob.shape == (1, 3, 64, 64), blob.shape
    assert hasattr(cv2.dnn, "readNetFromONNX")
    ok, encoded = cv2.imencode(".png", bgr)
    assert ok and cv2.imdecode(encoded, cv2.IMREAD_COLOR).shape == bgr.shape
    print(f"cv2 {cv2.__version__}: template matching, colour conversion, components, dnn blobs and PNG work")


def aiohttp():
    import aiohttp
    from aiohttp import _frozenlist, _helpers, _http_parser, _http_writer, _websocket  # noqa: F401  compiled modules

    print(f"aiohttp {aiohttp.__version__}; C extensions load")


TESTS = {"opencv-python": opencv, "aiohttp": aiohttp}

if __name__ == "__main__":
    TESTS[sys.argv[1]]()
