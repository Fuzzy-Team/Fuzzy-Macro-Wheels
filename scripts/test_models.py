"""Load and run every ONNX model used by Fuzzy Macro on older Macs.

Pin the model repository commit and verify each Git blob hash before loading it.
This checks the model engine on the runner; it cannot prove Sierra runtime support.
"""

import hashlib
from pathlib import Path
import subprocess
import tempfile


MODEL_COMMIT = "a24479524a9269efde9e26cafbcc381a14b92660"
MODEL_URL = "https://raw.githubusercontent.com/Fuzzy-Team/fuzzymacroaimodels/" + MODEL_COMMIT
MODELS = (
    ("token_detection_standard.onnx", "16643fa1de1f2c6a094ec801d8a44f65671c17c3", 480, 992, "end2end"),
    ("sprinkler_detection_standard.onnx", "3aa6e46d9d6a10eb6919504b232a2bd5cd1d6d65", 736, 736, "end2end"),
    ("bloom_detection_standard.onnx", "6e95bef8ec1913adfa89adbba89bd10102330373", 960, 960, "classic"),
    ("bloom_detection_light.onnx", "f0ad9db78cffe818853ef831a3d13055607c17af", 768, 768, "classic"),
    ("bloom_detection_mini.onnx", "17eb020cb2e4936bbd25fc71cf5bdfe8baf9e156", 512, 512, "classic"),
)


def opencv_models():
    import cv2
    import numpy as np

    with tempfile.TemporaryDirectory(prefix="fuzzy-onnx-") as tmp:
        for name, expected_hash, height, width, output_kind in MODELS:
            path = Path(tmp) / name
            subprocess.run(["curl", "-fsSL", "--retry", "3", "--max-time", "180",
                            "-o", str(path), MODEL_URL + "/" + name], check=True)
            data = path.read_bytes()
            actual_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if actual_hash != expected_hash:
                raise RuntimeError("Model content hash mismatch: " + name)
            del data
            model = cv2.dnn.readNetFromONNX(str(path))
            model.setInput(np.zeros((1, 3, height, width), dtype=np.float32))
            output = model.forward()
            assert output.ndim == 3 and output.shape[0] == 1, (name, output.shape)
            if output_kind == "end2end":
                assert output.shape[2] == 6, (name, output.shape)
            else:
                assert output.shape[1] == 5, (name, output.shape)
            assert output.size and np.isfinite(output).all(), name
            print("cv2 {}: {} loads and runs, output {} ({})".format(
                cv2.__version__, name, output.shape, output_kind), flush=True)


if __name__ == "__main__":
    opencv_models()
