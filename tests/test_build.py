import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build as builder


class BuildTests(unittest.TestCase):
    def test_commands_use_repo_root_and_local_cache(self):
        with patch.object(builder.subprocess, "run") as run:
            builder.run(["python", "-V"])
            self.assertEqual(run.call_args.kwargs["cwd"], builder.PROJECT_ROOT)
            self.assertEqual(
                run.call_args.kwargs["env"]["PYINSTALLER_CONFIG_DIR"],
                str(builder.PROJECT_ROOT / "build/cache"),
            )

    def test_ide_paths_and_interpreter_overrides_are_removed(self):
        with patch.dict(
            builder.os.environ,
            {
                "PYTHONPATH": "/ide/helpers",
                "PYTHONHOME": "/wrong/python",
                "PYCHARM_HOSTED": "1",
                "PYDEVD_LOAD_VALUES_ASYNC": "1",
                "JETBRAINS_CLIENT": "1",
                "VIRTUAL_ENV": "/development/venv",
                "__PYVENV_LAUNCHER__": "/wrong/launcher",
            },
        ):
            environment = builder.build_environment()
        for key in (
            "PYTHONPATH",
            "PYTHONHOME",
            "PYCHARM_HOSTED",
            "PYDEVD_LOAD_VALUES_ASYNC",
            "JETBRAINS_CLIENT",
            "VIRTUAL_ENV",
            "__PYVENV_LAUNCHER__",
        ):
            self.assertNotIn(key, environment)
        self.assertEqual(environment["PYTHONNOUSERSITE"], "1")
        self.assertIn("PATH", environment)

    def test_missing_environment_gives_setup_instruction(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(builder, "BUILD_PYTHON", Path(directory) / "missing"),
        ):
            with self.assertRaisesRegex(RuntimeError, "--setup"):
                builder.check_environment()

    def test_build_preserves_spec_and_uses_explicit_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "dist/MetaGrab.app/Contents/MacOS/MetaGrab"
            executable.parent.mkdir(parents=True)
            executable.touch()
            spec = root / "MetaGrab.spec"
            spec.write_text("# tracked configuration")
            with (
                patch.object(builder, "PROJECT_ROOT", root),
                patch.object(builder, "SPEC_FILE", spec),
                patch.object(builder, "run") as run,
            ):
                builder.build()
                command = run.call_args.args[0]
                self.assertIn(str(spec), command)
                self.assertIn(str(root / "dist"), command)
                self.assertEqual(spec.read_text(), "# tracked configuration")
                self.assertNotIn("install", command)

    def test_check_does_not_build_or_install(self):
        with (
            patch.object(builder.sys, "argv", ["build.py", "--check"]),
            patch.object(builder.platform, "system", return_value="Darwin"),
            patch.object(builder, "setup_environment") as setup,
            patch.object(builder, "check_environment") as check,
            patch.object(builder, "build") as build,
        ):
            self.assertEqual(builder.main(), 0)
            check.assert_called_once()
            setup.assert_not_called()
            build.assert_not_called()
