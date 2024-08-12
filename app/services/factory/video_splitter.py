import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from pathlib import Path

import librosa
import numpy as np
import webrtcvad
from loguru import logger
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

from app.services.factory.video_generator import get_ffmpeg_params
from app.settings.base_config import base_settings
from app.utils import utils


class VideoSplitter:
    def __init__(self, min_segment_length=5, pause_duration=1, save_dir=utils.cache_weibo_videos_dir(),
                 max_video_length=60,
                 include_audio=True, min_db_level=-45, max_segment_length=15):
        self.semaphore = asyncio.Semaphore(base_settings.max_concurrent_tasks)
        self.min_segment_length = min_segment_length
        self.pause_duration = pause_duration
        self.max_video_length = max_video_length
        self.include_audio = include_audio
        self.min_db_level = min_db_level
        self.max_segment_length = max_segment_length
        self.BASE_DIR = Path(__file__).parent.resolve()
        self.save_dir = self.BASE_DIR / save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)
        self.executor = ThreadPoolExecutor()
        logger.info(f"初始化视频片段分割器，保存目录为: {self.save_dir}")

    def generate_temp_filename(self, has_speech, index=None):
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        label = "speech" if has_speech else "no_speech"
        if index is not None:
            filename = f"{current_time}_{unique_id}_segment_{label}_{index:02d}.mp4"
        else:
            filename = f"{current_time}_{unique_id}_segment_{label}.mp4"
        return filename

    async def extract_audio(self, video_path):
        logger.info(f"从视频中提取音频: {video_path}")
        return await asyncio.get_event_loop().run_in_executor(self.executor, self._extract_audio_sync, video_path)

    def _extract_audio_sync(self, video_path):
        audio_filename = self.generate_temp_filename(has_speech=True).replace(".mp4", ".wav")
        audio_path = self.save_dir / audio_filename

        try:
            with VideoFileClip(str(video_path)) as video:
                if video.audio is None:
                    raise ValueError("视频中不包含音频轨道")
                video.audio.write_audiofile(str(audio_path), codec='pcm_s16le')
            logger.info(f"音频提取完成，保存路径为: {audio_path}")
        except Exception as e:
            logger.error(f"提取音频时出错: {e}")
            raise
        return audio_path

    async def detect_speech(self, audio_path, frame_duration_ms=30):
        logger.info(f"检测音频中的人声活动: {audio_path}")
        return await asyncio.get_event_loop().run_in_executor(self.executor, self._detect_speech_sync, audio_path,
                                                              frame_duration_ms)

    def _detect_speech_sync(self, audio_path, frame_duration_ms=30):
        try:
            audio = AudioSegment.from_wav(audio_path)
        except Exception as e:
            logger.error(f"加载音频文件失败: {e}")
            return []

        audio = audio.set_frame_rate(16000).set_channels(1)
        samples = np.array(audio.get_array_of_samples())
        sample_rate = audio.frame_rate

        frame_length = int(sample_rate * frame_duration_ms / 1000.0)
        segments = []
        is_speech = False
        start_time = 0.0
        last_speech_end_time = 0.0

        for i in range(0, len(samples), frame_length):
            frame = samples[i:i + frame_length].tobytes()
            if len(frame) < frame_length * 2:
                continue
            timestamp = i / sample_rate
            if self.vad.is_speech(frame, sample_rate):
                if not is_speech:
                    start_time = timestamp
                    is_speech = True
            else:
                if is_speech:
                    end_time = timestamp
                    while end_time - start_time > self.max_segment_length:
                        segments.append((start_time, start_time + self.max_segment_length))
                        start_time += self.max_segment_length
                    segment_length = end_time - start_time
                    if self.min_segment_length <= segment_length:
                        pause_time = start_time - last_speech_end_time if segments else 0
                        if segments and pause_time <= self.pause_duration:
                            logger.debug(f"合并片段，停顿时间：{pause_time:.2f}秒")
                            segments[-1] = (segments[-1][0], end_time)
                        else:
                            logger.debug(f"新增片段: {start_time:.2f}秒 - {end_time:.2f}秒")
                            segments.append((start_time, end_time))
                    last_speech_end_time = end_time
                    is_speech = False

        if is_speech:
            end_time = len(samples) / sample_rate
            while end_time - start_time > self.max_segment_length:
                segments.append((start_time, start_time + self.max_segment_length))
                start_time += self.max_segment_length
            if self.min_segment_length <= end_time - start_time:
                segments.append((start_time, end_time))
        logger.info(f"音频分割后的片段: {segments}")
        return segments

    def has_human_voice(self, audio_segment):
        try:
            y = np.array(audio_segment.get_array_of_samples())
            y = y.astype(np.float32) / np.iinfo(y.dtype).max
            sr = audio_segment.frame_rate
            S = np.abs(librosa.stft(y, n_fft=2048))
            freqs = librosa.fft_frequencies(sr=sr)

            min_voice_freq = 85
            max_voice_freq = 255

            for i in range(S.shape[1]):
                spectrum = S[:, i]
                max_freq = freqs[np.argmax(spectrum)]
                if min_voice_freq <= max_freq <= max_voice_freq:
                    return True
            return False
        except Exception as e:
            logger.error(f"检测人声时出错: {e}")
            return False

    async def save_video_segments(self, video_path, segments):
        logger.info(f"保存视频片段，视频路径为: {video_path}")
        return await asyncio.get_event_loop().run_in_executor(self.executor, self._save_video_segments_sync, video_path,
                                                              segments)

    def _save_video_segments_sync(self, video_path, segments):
        segment_paths = []

        try:
            with VideoFileClip(str(video_path)) as video:
                if video.audio is None:
                    raise ValueError("视频中不包含音频轨道")

                for idx, (start, end) in enumerate(segments, start=1):
                    segment_audio = video.audio.subclip(start, end)
                    audio_filename = self.generate_temp_filename(has_speech=True).replace(".mp4", ".wav")
                    audio_path = self.save_dir / audio_filename
                    segment_audio.write_audiofile(str(audio_path), codec='pcm_s16le')

                    audio_segment = AudioSegment.from_wav(audio_path)
                    has_speech = self.has_human_voice(audio_segment)

                    segment_filename = self.generate_temp_filename(has_speech=has_speech, index=idx)
                    segment_path = self.save_dir / segment_filename
                    with video.subclip(start, end) as segment:
                        if not self.include_audio:
                            segment = segment.without_audio()
                        segment.write_videofile(str(segment_path), codec="libx264", audio_codec="aac", logger=None,
                                                ffmpeg_params=get_ffmpeg_params())
                        logger.info(f"视频片段: {segment_path}, 时长: {end - start:.2f}秒, 时间段: {start:.2f}秒 - {end:.2f}秒")
                        segment_paths.append(str(segment_path))
                    os.remove(audio_path)
        except Exception as e:
            logger.error(f"保存视频片段时出错: {e}")
            raise

        return segment_paths

    async def split_video_by_volume(self, audio_path):
        logger.info(f"根据音量变化分割视频: {audio_path}")
        return await asyncio.get_event_loop().run_in_executor(self.executor, self._split_video_by_volume_sync,
                                                              audio_path)

    def _split_video_by_volume_sync(self, audio_path):
        try:
            y, sr = librosa.load(audio_path, sr=None)
        except Exception as e:
            logger.error(f"加载音频文件失败: {e}")
            return []

        hop_length = 512
        frame_length = 2048
        energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        threshold = np.percentile(energy, 20)
        split_indices = np.where(energy < threshold)[0]

        segments = []
        if len(split_indices) == 0:
            duration = librosa.get_duration(y=y, sr=sr)
            for i in range(0, int(duration), 10):
                end = min(i + 10, duration)
                if end - i > self.max_segment_length:
                    end = i + self.max_segment_length
                if self.min_segment_length <= end - i:
                    segments.append((i, end))
            logger.info(f"未检测到有效的音量分割点，按 10 秒分割: {segments}")
        else:
            times = librosa.frames_to_time(split_indices, sr=sr, hop_length=hop_length)
            start_time = 0.0
            for time in times:
                if time - start_time > self.max_segment_length:
                    time = start_time + self.max_segment_length
                if self.min_segment_length <= time - start_time:
                    segments.append((start_time, time))
                    start_time = time
            duration = librosa.get_duration(y=y, sr=sr)
            if duration - start_time > self.max_segment_length:
                start_time = duration - self.max_segment_length
            if self.min_segment_length <= duration - start_time:
                segments.append((start_time, duration))
            else:
                logger.warning(f"不符合时长片段，不进行保存 开始时间：{start_time}，时长：{duration}")
            logger.info(f"音量分割的时间段: {segments}")

        return segments

    async def process_video(self, video_path):
        async with self.semaphore:
            return await self._process_video(video_path)

    async def _process_video(self, video_path):
        logger.info(f"开始处理视频: {video_path}")
        saved_segments = []  # 初始化 saved_segments
        try:
            video = await asyncio.get_event_loop().run_in_executor(self.executor, VideoFileClip, str(video_path))
            if video.duration > self.max_video_length:
                logger.info(f"视频长度超过{self.max_video_length}秒，只保留前{self.max_video_length}秒")
                trimmed_video_filename = self.generate_temp_filename(has_speech=True)
                trimmed_video_path = self.save_dir / trimmed_video_filename
                trimmed_video = video.subclip(0, self.max_video_length)
                write_videofile_partial = partial(trimmed_video.write_videofile, str(trimmed_video_path),
                                                  codec="libx264", audio_codec="aac", fps=video.fps)
                await asyncio.get_event_loop().run_in_executor(self.executor, write_videofile_partial)
                video_path = trimmed_video_path
                video = await asyncio.get_event_loop().run_in_executor(self.executor, VideoFileClip, str(video_path))

            audio_path = await self.extract_audio(video_path)
            segments = await self.detect_speech(audio_path)

            if not segments:
                segments = await self.split_video_by_volume(audio_path)
                os.remove(audio_path)

            saved_segments = await self.save_video_segments(video_path, segments)

            if video.duration > self.max_video_length:
                os.remove(video_path)

            logger.success("视频片段智能分割处理完成")
        except Exception as e:
            logger.error(f"处理视频时出现错误: {str(e)}")
            raise e

        return saved_segments
