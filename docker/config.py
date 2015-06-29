import json
import os


def getConfiguration(filePath):
    _json = None
    if os.path.exists(filePath):
        with open(filePath) as f:
            data = f.read()
            try:
                _json = json.loads(data)
            except ValueError:
                pass
    return _json
