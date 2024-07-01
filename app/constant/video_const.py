PUNCTUATIONS = [
    "?", ",", ".", "、", ";", ":", "!", "…",
    "？", "，", "。", "、", "；", "：", "！", "...",
]


class TaskState:
    FAILED = 'error'
    COMPLETE = 'finish'
    WAITING = 'wait'
    PROCESSING = 'process'


class TaskDetailState:
    GENERATING_SCRIPT = "generating_script"
    SCRIPT_GENERATION_COMPLETE = "script_generation_complete"
    GENERATING_AUDIO = "generating_audio"
    AUDIO_GENERATION_COMPLETE = "audio_generation_complete"
    GENERATING_SUBTITLE = "generating_subtitle"
    SUBTITLE_GENERATION_COMPLETE = "subtitle_generation_complete"
    DOWNLOADING_VIDEOS = "downloading_videos"
    VIDEO_DOWNLOAD_COMPLETE = "video_download_complete"
    COMBINING_VIDEOS = "combining_videos"
    COMBINED_VIDEOS_COMPLETE = "combined_videos_complete"
    GENERATING_FINAL_VIDEO = "generating_final_video"
    FINAL_VIDEO_GENERATION_COMPLETE = "final_video_generation_complete"


class TaskFailureReason:
    FAILED_GENERATING_SCRIPT = "failed_generating_script"
    FAILED_GENERATING_AUDIO = "failed_generating_audio"
    FAILED_GENERATING_SUBTITLE = "failed_generating_subtitle"
    FAILED_DOWNLOADING_VIDEOS = "failed_downloading_videos"
    FAILED_COMBINING_VIDEOS = "failed_combining_videos"
    FAILED_GENERATING_FINAL_VIDEO = "failed_generating_final_video"
    VALUE_ERROR = "value_error"


class FileTypes:
    VIDEOS = ['mp4', 'mov', 'mkv', 'webm']
    IMAGES = ['jpg', 'jpeg', 'png', 'bmp']

    @classmethod
    def is_video(cls, file_extension):
        return file_extension in cls.VIDEOS

    @classmethod
    def is_image(cls, file_extension):
        return file_extension in cls.IMAGES


class SubtitleProvider:
    # 音频识别字幕的提供商
    EDGE = 'edge'
    WHISPER = 'whisper'


VIDEO_STYLE_MAP = {
    'generic': {
        'structure': '钩子开头+塑造期待+解决方案+结尾（完成闭环）',
        'example': """参考以下话术案例，选择最能符合当前语境的模板进行仿写文案，如
        1.揭秘好奇型话术举例：我今天给大家揭秘一下xxx，先收藏，以免以后找不到!
                     本质就是利用人性的好奇心+视频的划走成本，让你觉得看了也不亏。
        2.千万叛逆型话术举例：千万不要再相信那些博主说xxxxx! 
                     本质就是利用了人的规避心态以及风险倾向，觉得可以避开这些坑。
        3.被上了一课型举例:举例我今天真的被水果店老板上了一课，50元5个橘子你敢相信嘛?
                     本质就是这样的开头非常合适叙述故事作为开端，用起来非常自然。
        4.你有xx经历型话术举例子：你有xxxx的经历吗?
                     话术原理就是经历这个词就能让人产生共鸣，如果再表现出来，那效果就太好了!
        5.经历体验型举例:我第一次一个人拿着500块去北京找工作是一种什么样的体验。话术原理就是这种开头合适作为VLOG为开头，更加的贴近现实生活。 
        6.避雷干货型举例:宝马的这个通病你要是了解，肯定能为你省下不少冤枉钱...话术原理就是给用户获得价值+获得感，看了这个视频就觉得赚了。"""
    },
    'viral_script': {
        'structure': '精简+有趣+节奏+视觉冲击',
        'example': """【短视频脚本文案越精简越好,不要有废话,时长能少一秒是一秒】 这个结构原理就是快速精简说明：短视频作为娱乐性平台更加强调有趣放松的属性，然后脚本也要寓教于乐，视频节奏较快,前3秒一定要抓人眼球,中间节奏也要控制好每5秒一个亮点，保证抓住观众不划走，好的脚本需要找到匹配的视觉呈现形式"""
    },
    'pain_point': {
        'structure': '现象（目标人群+痛点/共鸣式钩子）+危害+原因+解决方法',
        'example': """比如文案【黄皮肤女孩买衣服太难选颜色了，挑错显脸又黑又老，但是皮肤颜色很多时候又是天生的，这三种颜色不仅显白，还超级显气质..] 1、先说明现象黄皮肤女孩买衣服太难选颜色，2、再说明危害：挑错了颜色显得脸又黑又老，3、之后透露原因：是因为天生就黄皮肤不好配色，4、最后给出解决方法：分享出作者的三种颜色不仅显白还超级显气质..5、最后吸引人点赞关注"""
    },
    'explosive_info': {
        'structure': '炸裂式的开头（反差类钩子）+人设信息（塑造期待）+高密度的信息盘点（罗列相关信息）+动式结尾',
        'example': """1、先构造炸裂开头【还有人不知道手机拍照是可以赚钱的吗】 2、再立人设塑造期待：好多家人们已经来报喜赚钱了 3、再罗列高密度信息说明具体操作：将拍到的照片上传网站门户网站赚钱 4、结尾再呼吁大家关注自己：关注我给生活增添更多惊喜"""
    },
    'positive_result': {
        'structure': '积极结果获得感(利益性结果前置)+方案+互动式结尾',
        'example': """先列出积极的结果开头引人先关注:家人们!我爆单赚钱啦!上两期讲的爆款公式火,当月单个广告变现一条带货视频就有分佣,宝子们评论区留言分享公式~ 然后给出你是怎么做的方案:上两期讲的爆款公式火了，当月单个广告变现 文案结尾吸引人评论关注:宝子们评论区留言分享公式!"""
    },
    'illustrative_quotes': {
        'structure': '列金句(连续递进式) +佐证 +列金句+佐证',
        'example': """1、先列出切合的金句比如方言才是创作的母体啊! 2、然后进行举例子：“芙蓉路的妹陀,岳阳的臊子”你们听,这两句方言一出，就勾勒出两地青年的画像,长沙女孩个子小小,绵软可爱，岳阳的青年混不吝充满了干劲,方言带来的画面感极易引起共鸣! 3、再列出金句名言:方言才是创作的母体啊! 4、再给出佐证例子:你们听，这两句方言一出.."""
    },
    'industry_reveal': {
        'structure': '行业揭秘 +塑造期待+解决方案',
        'example': """1、先选择你的行业，然后分享一个揭秘的案例卖关子吸引人先看前文如：讲一个专业编导一般都不太愿意讲的爆款内容脚本结构，我不敢保证说你使用完之后能百分之百出爆款，但是你的完播率翻上一倍……，这个结构的叫... 2、之后再揭秘:我是跟一个演讲高手学的! 3、分享你的收益点：家人们!我爆单啦!  4、接着塑造期待使观众感到对他有好处:会让你的完播率翻上一倍 5、最后：给出你的方案原理:这个结构叫..我是跟一个演讲高手学的!"""
    },
    'benefit_transfer': {
        'structure': '利益传递(利益传递类钩子)+强化期待 +解决办法+结尾',
        'example': """1、给出利好观众的一些开头：如教你一条万能的短视频文案公式，播放收益上万！，2、举例强化一下期待：你刷到的很多点赞几百W的视频文案都是这样写的，其实一点也不难...，3、分享你的方法：直接套用模板就好而且非常百搭....,4：吸引人点赞收藏你的方法：记得点赞收藏! """
    },
    'opinion_sharing': {
        'structure': '事实+个人感受+发现问题+引出观点+故事+总结观点',
        'example': """1、先摆出事实:最近发生了一个什么事 2、然后说出你自己的感受:让我产生了...3：描述你发现的问题:这背后存在一个……问题， 4：开始提出观点:我觉得问题的答案是....…  5：强化举例故事证明:一个能证明我观点的故事.... 最后总结:所以应该...… 再吸引人点赞关注"""
    },
    'knowledge_sharing': {
        'structure': '问题描述+问题的拆解+答案描述+答案拆解',
        'example': """1、提出问题:我知道你遇到了……的问题 2、开始拆解:我已经找到了你的问题所在.. 开始描述:我来给你看看我的解决方案...... 给出这么做的原因答案:为什么这个办法能解决你的问题"""
    },
    "common_ending": {
        "structure": "互动式/IP型/共情式/反转式",
        "example": "互动式:在视频结束时引导用户进行互动，例如关注、点赞或评论。例如: '如果你喜欢这个视频，请不要忘记点赞和评论哦！' IP型:通过个性化的Slogan来增强个人品牌IP属性。例如: '记住，这里是[你的名字]，每周更新不见不散！' 共情式:留下能够引起用户共鸣的哲理名句、诗句等，升华视频的情感层次。例如: '生活就像一场旅行，不在乎目的地，只在乎沿途的风景。' 反转式:利用前后文的反差形成强烈的情绪冲击，加深用户的印象。例如: '刚才的故事只是一个开始，接下来你将看到真正的奇迹。'"
    }

}
