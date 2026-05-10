#!/usr/bin/env python3
"""Create a simple test video for AutoVideoEditor."""

import numpy as np
from moviepy.editor import VideoClip, concatenate_videoclips
import sys

def create_test_video(output_path="test_video.mp4", duration=10):
    """Create a colorful test video."""

    print(f"🎬 Creating test video ({duration}s)...")

    def make_frame(t):
        h, w = 1920, 1080
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Animated gradient based on time
        r = int(128 + 127 * np.sin(t * 0.5))
        g = int(100 + 155 * np.cos(t * 0.3))
        b = int(200 + 55 * np.sin(t * 0.7))

        frame[:, :, 0] = r
        frame[:, :, 1] = g
        frame[:, :, 2] = b

        return frame

    try:
        video = VideoClip(make_frame=make_frame, duration=duration)
        video.fps = 24
        video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        print(f"✅ Video created: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    output = sys.argv[2] if len(sys.argv) > 2 else "test_video.mp4"
    create_test_video(output, duration)
