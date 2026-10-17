# app/systems/download_system/utils/download_utils.py

import os
import uuid
from pathlib import Path

from platformdirs import user_data_dir


def get_temp_sandbox_folder() -> Path:
    """Create and return a temp sandbox folder under the app data dir."""
    base_temp_dir = Path(user_data_dir("MetaGrab")) / "tmp"
    base_temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate a unique subfolder to isolate this run
    sandbox = base_temp_dir / f"sandbox_{uuid.uuid4().hex}"
    sandbox.mkdir(parents=True, exist_ok=True)

    try:
        os.chmod(sandbox, 0o700)  # 🛡️ Secure permissions
        actual_mode = oct(os.stat(sandbox).st_mode)[-3:]
        if actual_mode != "700":
            print(f"⚠️ Warning: Sandbox {sandbox} permissions are {actual_mode}, expected 700.")
    except Exception as e:
        print(f"⚠️ Warning: Failed to set permissions on sandbox: {e}")

    return sandbox
