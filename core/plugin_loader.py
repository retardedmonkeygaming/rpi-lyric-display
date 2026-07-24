import os
import glob
import importlib.util
from typing import Dict, Any

class PluginLoader:
    """Scans the 'plugins/' directory and registers extensions on startup."""

    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, Any] = {}
        os.makedirs(self.plugin_dir, exist_ok=True)

    def load_plugins(self) -> Dict[str, Any]:
        plugin_files = glob.glob(os.path.join(self.plugin_dir, "*.py"))
        for filePath in plugin_files:
            name = os.path.basename(filePath)[:-3]
            if name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(name, filePath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_plugins[name] = module
                print(f"[LyricPulse] Loaded Plugin: {name}")
            except Exception as e:
                print(f"[LyricPulse] Failed to load plugin '{name}': {e}")
        return self.loaded_plugins