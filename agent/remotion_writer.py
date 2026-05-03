"""
Writes generated scene files into an existing Remotion project.
"""
import os
import re
from utils.file_utils import write_text, read_text, ensure_dir


class RemotionWriter:
    def __init__(self, remotion_path: str):
        self.remotion_path = remotion_path
        self.scenes_dir = os.path.join(remotion_path, "src", "scenes")
        ensure_dir(self.scenes_dir)

    def write_scene(self, scene_num: int, code: str) -> str:
        filename = f"Scene{scene_num}.tsx"
        filepath = os.path.join(self.scenes_dir, filename)
        write_text(filepath, code)
        return filepath

    def update_root(self, scenes: list, fps: int = 30, resolution: str = "1080p"):
        """Update or create src/Root.tsx to include all scenes as a Composition."""
        w, h = self._resolution_to_dims(resolution)
        total_duration = sum(int(s["duration"] * fps) for s in scenes)
        imports = "\n".join(f"import {{ Scene{i+1} }} from './scenes/Scene{i+1}';" for i in range(len(scenes)))

        # Build sequence entries
        offset = 0
        sequences = []
        for i, scene in enumerate(scenes):
            dur = int(scene["duration"] * fps)
            sequences.append(f"""      <Sequence from={{{offset}}} durationInFrames={{{dur}}}>
        <Scene{i+1} />
      </Sequence>""")
            offset += dur
        seq_block = "\n".join(sequences)

        root_content = f"""import {{ Composition, Sequence }} from 'remotion';
{imports}

export const RemotionRoot: React.FC = () => {{
  return (
    <>
      <Composition
        id="MotionAgent"
        component={{MotionVideo}}
        durationInFrames={{{total_duration}}}
        fps={{{fps}}}
        width={{{w}}}
        height={{{h}}}
      />
    </>
  );
}};

const MotionVideo: React.FC = () => {{
  return (
    <>
{seq_block}
    </>
  );
}};
"""
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
