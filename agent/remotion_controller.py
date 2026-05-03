"""
Controls the Remotion CLI process for rendering.
"""
import subprocess
import os
import shutil
from utils.json_streamer import log


class RemotionController:
    def __init__(self, remotion_path: str, output_path: str):
        self.remotion_path = remotion_path
        self.output_path = output_path

    def render(self, composition: str = "MotionAgent", filename: str = "output.mp4",
               fps: int = 30, codec: str = "h264") -> str:
        out_file = os.path.join(self.output_path, filename)
        os.makedirs(self.output_path, exist_ok=True)

        cmd = ["npx", "remotion", "render", composition, out_file,
               f"--fps={fps}", f"--codec={self._map_codec(codec)}"]

        log(f"Renderizando: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=self.remotion_path,
            capture_output=True,
            text=True,
            shell=(os.name == "nt"),
        )

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed:\n{result.stderr}")

        log(f"Vídeo salvo em: {out_file}", level="success")
        return out_file

    def _map_codec(self, codec: str) -> str:
        return {"mp4-h264": "h264", "mp4-h265": "h265", "webm": "vp8", "prores": "prores"}.get(codec, "h264")

    def is_remotion_installed(self) -> bool:
        pkg_path = os.path.join(self.remotion_path, "node_modules", "remotion")
        return os.path.isdir(pkg_path)

    def install_dependencies(self):
        log("Instalando dependências do projeto Remotion...")
        subprocess.run(["npm", "install"], cwd=self.remotion_path,
                       shell=(os.name == "nt"), check=True)
