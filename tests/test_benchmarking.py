"""Offline tests for immutable benchmark evidence records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from projectblur.benchmarking import file_evidence, save_benchmark_record


class BenchmarkRecordingTests(unittest.TestCase):
    def test_saves_unique_default_record_and_refuses_overwrite(self) -> None:
        record = {"run_id": "20260717T010203.000000Z", "value": 12.5}
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            output = save_benchmark_record(
                record,
                project_root=project_root,
                filename_prefix="detector/yunet adapter",
            )

            self.assertEqual(
                output,
                project_root
                / "artifacts"
                / "benchmarks"
                / "detector_yunet_adapter_20260717T010203.000000Z.json",
            )
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                record,
            )
            with self.assertRaisesRegex(FileExistsError, "will not be overwritten"):
                save_benchmark_record(
                    record,
                    project_root=project_root,
                    filename_prefix="detector/yunet adapter",
                )

    def test_file_evidence_uses_portable_path_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            model = project_root / "models" / "detector.onnx"
            model.parent.mkdir()
            model.write_bytes(b"projectblur-test-model")

            evidence = file_evidence(model, project_root=project_root)

        self.assertEqual(evidence["path"], "models/detector.onnx")
        self.assertEqual(evidence["bytes"], 22)
        self.assertEqual(
            evidence["sha256"],
            hashlib.sha256(b"projectblur-test-model").hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
