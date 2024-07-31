
import json
import os.path
import re
from os import path
from timeit import default_timer as timer

from faster_whisper import WhisperModel
from loguru import logger
from moviepy.editor import *

from app.constant.video_const import SubtitleProvider
from app.services.factory import voice_generator
from app.settings import movies_config
from app.utils import utils

model_size = movies_config.whisper.get("model_size", "large-v3")
device = movies_config.whisper.get("device", "cpu")
compute_type = movies_config.whisper.get("compute_type", "int8")
model = None
async def generate_subtitle(task_id, params, audio_file, video_script, sub_maker):
    subtitle_path = ""
    if params.subtitle_enabled:
        subtitle_path = path.join(utils.task_dir(task_id), f"subtitle.srt")
        subtitle_provider = movies_config.app.get("subtitle_provider", "").strip().lower()
        logger.info(f"\n\n## generating subtitle, provider: {subtitle_provider}")
        subtitle_fallback = False
        if subtitle_provider == SubtitleProvider.EDGE:
            voice_generator.create_subtitle(text=video_script, sub_maker=sub_maker, subtitle_file=subtitle_path)
            if not os.path.exists(subtitle_path):
                subtitle_fallback = True
                logger.warning("subtitle file not found, fallback to whisper")

        if subtitle_provider == SubtitleProvider.WHISPER or subtitle_fallback:
            create(audio_file=audio_file, subtitle_file=subtitle_path)
            logger.info("\n\n## correcting subtitle")
            correct(subtitle_file=subtitle_path, video_script=video_script)

        subtitle_lines = file_to_subtitles(subtitle_path)
        if not subtitle_lines:
            logger.warning(f"subtitle file is invalid: {subtitle_path}")
            subtitle_path = ""

    return subtitle_path

def create(audio_file, subtitle_file: str = ""):
    global model
    if not model:
        model_path = f"{utils.root_dir()}/models/whisper-{model_size}"
        model_bin_file = f"{model_path}/model.bin"
        if not os.path.isdir(model_path) or not os.path.isfile(model_bin_file):
            model_path = model_size

        logger.info(f"loading model: {model_path}, device: {device}, compute_type: {compute_type}")
        try:
            model = WhisperModel(model_size_or_path=model_path,
                                 device=device,
                                 compute_type=compute_type)
        except Exception as e:
            logger.error(f"failed to load model: {e} \n\n"
                         f"********************************************\n"
                         f"this may be caused by network issue. \n"
                         f"please download the model manually and put it in the 'models' folder. \n"
                         f"see [README.md FAQ](https://github.com/harry0703/MoneyPrinterTurbo) for more details.\n"
                         f"********************************************\n\n")
            return None

    logger.info(f"start, output file: {subtitle_file}")
    if not subtitle_file:
        subtitle_file = f"{audio_file}.srt"

    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    logger.info(f"detected language: '{info.language}', probability: {info.language_probability:.2f}")

    start = timer()
    subtitles = []

    def recognized(seg_text, seg_start, seg_end):
        seg_text = seg_text.strip()
        if not seg_text:
            return

        msg = "[%.2fs -> %.2fs] %s" % (seg_start, seg_end, seg_text)
        logger.debug(msg)

        subtitles.append({
            "msg": seg_text,
            "start_time": seg_start,
            "end_time": seg_end
        })

    for segment in segments:
        words_idx = 0
        words_len = len(segment.words)

        seg_start = 0
        seg_end = 0
        seg_text = ""

        if segment.words:
            is_segmented = False
            for word in segment.words:
                if not is_segmented:
                    seg_start = word.start
                    is_segmented = True

                seg_end = word.end
                # 如果包含标点,则断句
                seg_text += word.word

                if utils.str_contains_punctuation(word.word):
                    # remove last char
                    seg_text = seg_text[:-1]
                    if not seg_text:
                        continue

                    recognized(seg_text, seg_start, seg_end)

                    is_segmented = False
                    seg_text = ""

                if words_idx == 0 and segment.start < word.start:
                    seg_start = word.start
                if words_idx == (words_len - 1) and segment.end > word.end:
                    seg_end = word.end
                words_idx += 1

        if not seg_text:
            continue

        recognized(seg_text, seg_start, seg_end)

    end = timer()

    diff = end - start
    logger.info(f"complete, elapsed: {diff:.2f} s")

    idx = 1
    lines = []
    for subtitle in subtitles:
        text = subtitle.get("msg")
        if text:
            lines.append(utils.text_to_srt(idx, text, subtitle.get("start_time"), subtitle.get("end_time")))
            idx += 1

    sub = "\n".join(lines) + "\n"
    with open(subtitle_file, "w", encoding="utf-8") as f:
        f.write(sub)
    logger.info(f"subtitle file created: {subtitle_file}")


def file_to_subtitles(filename):
    if not filename or not os.path.isfile(filename):
        return []

    times_texts = []
    current_times = None
    current_text = ""
    index = 0
    with open(filename, 'r', encoding="utf-8") as f:
        for line in f:
            times = re.findall("([0-9]*:[0-9]*:[0-9]*,[0-9]*)", line)
            if times:
                current_times = line
            elif line.strip() == '' and current_times:
                index += 1
                times_texts.append((index, current_times.strip(), current_text.strip()))
                current_times, current_text = None, ""
            elif current_times:
                current_text += line
    return times_texts


def correct(subtitle_file, video_script):
    subtitle_items = file_to_subtitles(subtitle_file)
    script_lines = utils.split_string_by_punctuations(video_script)

    corrected = False
    if len(subtitle_items) == len(script_lines):
        for i in range(len(script_lines)):
            script_line = script_lines[i].strip()
            subtitle_line = subtitle_items[i][2]
            if script_line != subtitle_line:
                logger.warning(f"line {i + 1}, script: {script_line}, subtitle: {subtitle_line}")
                subtitle_items[i] = (subtitle_items[i][0], subtitle_items[i][1], script_line)
                corrected = True

    if corrected:
        with open(subtitle_file, "w", encoding="utf-8") as fd:
            for item in subtitle_items:
                fd.write(f"{item[0]}\n{item[1]}\n{item[2]}\n\n")
        logger.info(f"subtitle corrected")
    else:
        logger.success(f"subtitle is correct")


