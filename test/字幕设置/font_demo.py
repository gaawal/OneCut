from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip

def generate_subtitle_preview(
    input_video_path,
    output_video_path,
    subtitle_text="这是预览字幕文本",
    subtitle_font_path="MyCustomFont.ttf",  # 自定义字体文件路径
    subtitle_size=30,
    subtitle_color="white",
    subtitle_background_color=None,
    subtitle_stroke_color="black",
    subtitle_stroke_width=1,
    subtitle_position="center",
    subtitle_opacity=1.0
):
    # 创建视频剪辑对象
    video_clip = VideoFileClip(input_video_path)

    # 打印调试信息
    print(f"视频分辨率: {video_clip.size}")
    print(f"视频帧率: {video_clip.fps}")

    # 创建文本剪辑对象
    text_clip = TextClip(
        subtitle_text,
        font=subtitle_font_path,
        fontsize=subtitle_size,
        color=subtitle_color,
        stroke_color=subtitle_stroke_color,
        stroke_width=subtitle_stroke_width,
        bg_color=subtitle_background_color,
    )

    # 设置字幕透明度
    text_clip = text_clip.set_opacity(subtitle_opacity)

    # 设置字幕位置
    if subtitle_position == "top":
        text_clip = text_clip.set_position(("center", "10%"))
    elif subtitle_position == "bottom":
        text_clip = text_clip.set_position(("center", "10%"))
    elif subtitle_position == "center":
        text_clip = text_clip.set_position("center")

    # 打印字幕剪辑信息
    print(f"字幕剪辑信息: {text_clip.size}")

    # 截取第一帧视频并添加字幕
    frame = video_clip.get_frame(0)
    frame_duration = 1.0 / video_clip.fps
    frame_clip = ImageClip(frame).set_duration(frame_duration)
    result = CompositeVideoClip([frame_clip, text_clip.set_duration(frame_duration)])

    # 保存输出视频
    result.write_videofile(output_video_path, codec="libx264", fps=video_clip.fps)

    print("视频生成完成！")

# 示例调用
generate_subtitle_preview(
    input_video_path="demo.mp4",
    output_video_path="output_demo.mp4",
    subtitle_text="这是预览字幕文本缓和缓和缓和缓和缓和缓和缓和缓和",
    subtitle_font_path="MicrosoftYaHeiBold.ttc",  # 替换为你的自定义字体文件路径
    subtitle_size=60,  # 调整字体大小
    subtitle_color="yellow",
    subtitle_background_color="#66a7de",
    subtitle_stroke_color="#040a52",
    subtitle_stroke_width=3,
    subtitle_position="center",
    subtitle_opacity=1  # 确保透明度为1.0
)
