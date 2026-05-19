"""
Writes generated scene files into an existing Remotion project.
"""
import os
from utils.file_utils import write_text, ensure_dir


class RemotionWriter:
    def __init__(self, remotion_path: str):
        self.remotion_path = remotion_path
        self.scenes_dir = os.path.join(remotion_path, "src", "scenes")
        self.runtime_dir = os.path.join(remotion_path, "src", "runtime")
        ensure_dir(self.scenes_dir)
        ensure_dir(self.runtime_dir)

        # Estado interno: scenes geradas até agora (para update incremental)
        self._generated_scenes: list = []   # list of {"duration": float}
        self._fps: int = 30
        self._resolution: str = "1080p"

    def ensure_runtime(self):
        """
        Garante que o MotionRuntime.tsx existe no projeto Remotion.
        Chamado uma vez antes da geração das cenas.
        """
        runtime_path = os.path.join(self.runtime_dir, "MotionRuntime.tsx")
        if not os.path.exists(runtime_path):
            from remotion_compiler import generate_motion_runtime
            write_text(runtime_path, generate_motion_runtime())
        return runtime_path

    def write_scene(self, scene_num: int, code: str) -> str:
        filename = f"Scene{scene_num:02d}.tsx"
        filepath = os.path.join(self.scenes_dir, filename)
        write_text(filepath, code)
        return filepath

    def scene_done(self, scene_num: int, duration: float, fps: int = 30, resolution: str = "1080p"):
        """
        Chamado após cada cena gerada.
        Atualiza o Root.tsx imediatamente para que o Remotion Studio
        mostre a composição parcial em tempo real (hot-reload).
        """
        self._fps = fps
        self._resolution = resolution

        # Garante que a lista tem o tamanho certo
        while len(self._generated_scenes) < scene_num:
            self._generated_scenes.append({"duration": 3.0})
        self._generated_scenes[scene_num - 1] = {"duration": duration}

        # Atualiza Root.tsx com as cenas geradas até agora
        self._write_root(self._generated_scenes)

    def update_root(self, scenes: list, fps: int = 30, resolution: str = "1080p"):
        """Update final do Root.tsx com todas as cenas."""
        self._fps = fps
        self._resolution = resolution
        self._generated_scenes = scenes
        self._write_root(scenes)

    def _write_root(self, scenes: list):
        """Gera e salva o Root.tsx com as cenas fornecidas."""
        fps = self._fps
        w, h = self._resolution_to_dims(self._resolution)
        total_duration = max(1, sum(int(s.get("duration", 3) * fps) for s in scenes))

        # Imports das cenas — usa Scene01, Scene02 ...
        scene_imports = "\n".join(
            f"import {{ Scene{i+1:02d} }} from './scenes/Scene{i+1:02d}';"
            for i in range(len(scenes))
        )

        # Sequences com offset acumulado
        offset = 0
        sequences = []
        for i, scene in enumerate(scenes):
            dur = max(1, int(scene.get("duration", 3) * fps))
            sequences.append(
                f"      <Sequence from={{{offset}}} durationInFrames={{{dur}}}>\n"
                f"        <Scene{i+1:02d} />\n"
                f"      </Sequence>"
            )
            offset += dur
        seq_block = "\n".join(sequences)

        root_content = (
            'import "./index.css";\n'
            'import React from \'react\';\n'
            'import { Composition, Sequence } from \'remotion\';\n'
            f'{scene_imports}\n'
            '\n'
            'export const RemotionRoot: React.FC = () => {\n'
            '  return (\n'
            '    <>\n'
            '      <Composition\n'
            '        id="MotionAgent"\n'
            '        component={MotionVideo}\n'
            f'        durationInFrames={{{total_duration}}}\n'
            f'        fps={{{fps}}}\n'
            f'        width={{{w}}}\n'
            f'        height={{{h}}}\n'
            '      />\n'
            '    </>\n'
            '  );\n'
            '};\n'
            '\n'
            'const MotionVideo: React.FC = () => {\n'
            '  return (\n'
            '    <>\n'
            f'{seq_block}\n'
            '    </>\n'
            '  );\n'
            '};\n'
        )

        root_path = os.path.join(self.remotion_path, "src", "Root.tsx")
        write_text(root_path, root_content)
        return root_path

    def _resolution_to_dims(self, resolution: str) -> tuple:
        return {
            "720p":   (1280, 720),
            "1080p":  (1920, 1080),
            "1080v":  (1080, 1920),
            "4k":     (3840, 2160),
            "square": (1080, 1080),
        }.get(resolution, (1920, 1080))
