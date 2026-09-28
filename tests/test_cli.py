from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from taxbot.cli import main


class CliTests(unittest.TestCase):
    def test_synthetic_init_and_redacted_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic"
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(["--root", str(root), "--mode", "synthetic", "init"]), 0
                )
            initialized = json.loads(output.getvalue())
            self.assertEqual(initialized["integrity"], "ok")
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(["--root", str(root), "--mode", "synthetic", "status"]), 0
                )
            status = json.loads(output.getvalue())
            self.assertEqual(status["ledger_revision"], 0)
            self.assertEqual(status["journal_entries"], 0)
            self.assertNotIn(str(root), status)


if __name__ == "__main__":
    unittest.main()
