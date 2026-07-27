import json
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from unittest.mock import patch

import numpy as np

import server


class FakeTTS:
    def synthesize(self, text, *, speed, variation, seed):
        assert text == "Test speech."
        assert (speed, variation, seed) == (1.0, 0.667, 0)
        return 8_000, np.zeros(80, dtype=np.float32)


def test_speak():
    server.tts = FakeTTS()
    httpd = server.HTTPServer(("127.0.0.1", 0), server.SpeakHandler)
    worker = Thread(target=httpd.handle_request)

    with patch("server.subprocess.run") as play:
        worker.start()
        connection = HTTPConnection("127.0.0.1", httpd.server_port)
        connection.request(
            "POST",
            "/speak",
            json.dumps({"text": "Test speech"}),
            {"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        assert response.status == 200
        assert json.load(response) == {"status": "played"}
        worker.join(timeout=2)

    assert not worker.is_alive()
    assert not Path(play.call_args.args[0][1]).exists()
    httpd.server_close()


if __name__ == "__main__":
    test_speak()
    print("server check passed")
