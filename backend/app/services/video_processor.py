import logging
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
import librosa

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video editing operations."""

    def __init__(self, output_dir: str = "/tmp/output"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    async def detect_silence(
        self, video_path: str, silence_threshold: float = -40
    ) -> list[Tuple[float, float]]:
        """
        Detects silent segments in video audio.
        Returns list of (start_time, end_time) tuples for silence periods.
        """
        try:
            video = VideoFileClip(video_path)
            audio = video.audio

            if audio is None:
                logger.warning("Video has no audio track")
                return []

            # Convert to numpy array
            samples = audio.to_soundarray()
            if len(samples.shape) > 1:
                samples = samples[:, 0]  # Use first channel

            # Compute STFT and convert to dB
            S = librosa.stft(samples.astype(np.float32))
            db = librosa.power_to_db(np.abs(S) ** 2, ref=np.max)
            energy = np.mean(db, axis=0)

            # Find silent frames
            silent_frames = energy < silence_threshold
            hop_length = 512
            times = librosa.frames_to_time(np.arange(len(silent_frames)), sr=audio.fps, hop_length=hop_length)

            # Group consecutive silent frames
            silence_segments = []
            in_silence = False
            silence_start = 0

            for i, is_silent in enumerate(silent_frames):
                if is_silent and not in_silence:
                    silence_start = times[i]
                    in_silence = True
                elif not is_silent and in_silence:
                    silence_end = times[i]
                    if silence_end - silence_start > 0.5:  # Only mark if > 0.5s
                        silence_segments.append((silence_start, silence_end))
                    in_silence = False

            video.close()
            return silence_segments

        except Exception as e:
            logger.error(f"Error detecting silence: {e}")
            return []

    async def remove_silence(
        self, video_path: str, silence_threshold: float = -40
    ) -> str:
        """
        Removes silent segments from video and returns new video path.
        """
        try:
            silence_segments = await self.detect_silence(video_path, silence_threshold)

            if not silence_segments:
                logger.info("No silence detected")
                return video_path

            video = VideoFileClip(video_path)
            clips = []
            current_time = 0

            for silence_start, silence_end in silence_segments:
                # Add the part before silence
                if current_time < silence_start:
                    clip = video.subclipped(current_time, silence_start)
                    if clip.duration > 0:
                        clips.append(clip)

                current_time = silence_end

            # Add remaining part
            if current_time < video.duration:
                clip = video.subclipped(current_time, video.duration)
                if clip.duration > 0:
                    clips.append(clip)

            if not clips:
                logger.warning("No content after removing silence")
                video.close()
                return video_path

            final_video = concatenate_videoclips(clips)
            output_path = os.path.join(self.output_dir, "silence_removed.mp4")
            final_video.write_videofile(
                output_path,
                verbose=False,
                logger=None,
                codec="libx264",
                audio_codec="aac",
            )

            video.close()
            final_video.close()

            return output_path

        except Exception as e:
            logger.error(f"Error removing silence: {e}")
            return video_path

    async def apply_basic_color_grading(
        self, video_path: str, color_params: Dict
    ) -> str:
        """
        Applies basic color grading based on parameters.
        Adjusts saturation, brightness, contrast, etc.
        """
        try:
            video = VideoFileClip(video_path)

            def color_grade_frame(frame):
                frame = frame.astype(np.float32) / 255.0

                # Saturation adjustment
                if "saturation" in color_params:
                    sat = color_params["saturation"]
                    gray = np.mean(frame, axis=2, keepdims=True)
                    frame = gray + (frame - gray) * sat

                # Brightness
                if "brightness" in color_params:
                    frame += color_params["brightness"]

                # Contrast
                if "contrast" in color_params:
                    frame = 0.5 + (frame - 0.5) * color_params["contrast"]

                # Clamp values
                frame = np.clip(frame, 0, 1)
                return (frame * 255).astype(np.uint8)

            graded_video = video.fl_image(color_grade_frame)
            output_path = os.path.join(self.output_dir, "color_graded.mp4")

            graded_video.write_videofile(
                output_path,
                verbose=False,
                logger=None,
                codec="libx264",
                audio_codec="aac",
            )

            video.close()
            graded_video.close()

            return output_path

        except Exception as e:
            logger.error(f"Error applying color grading: {e}")
            return video_path

    async def get_video_metadata(self, video_path: str) -> Dict:
        """
        Extracts basic metadata from video.
        """
        try:
            video = VideoFileClip(video_path)
            metadata = {
                "duration": video.duration,
                "fps": video.fps,
                "width": video.w,
                "height": video.h,
                "file_size": os.path.getsize(video_path),
                "has_audio": video.audio is not None,
                "has_speech": False,  # Would need speech detection
            }
            video.close()
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}

    async def scale_for_platform(
        self, video_path: str, platform: str = "tiktok"
    ) -> str:
        """
        Resizes video for specific platform (Reels, TikTok, Shorts).
        """
        platform_dimensions = {
            "tiktok": (1080, 1920),  # 9:16
            "reels": (1080, 1920),   # 9:16
            "shorts": (1080, 1920),  # 9:16
            "square": (1080, 1080),  # 1:1
        }

        dimensions = platform_dimensions.get(platform, (1080, 1920))

        try:
            video = VideoFileClip(video_path)
            resized = video.resize(height=dimensions[1], width=dimensions[0])
            output_path = os.path.join(self.output_dir, f"scaled_{platform}.mp4")

            resized.write_videofile(
                output_path,
                verbose=False,
                logger=None,
                codec="libx264",
                audio_codec="aac",
            )

            video.close()
            resized.close()

            return output_path

        except Exception as e:
            logger.error(f"Error scaling video: {e}")
            return video_path
