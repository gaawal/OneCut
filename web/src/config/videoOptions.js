import tiktokImg from '@/assets/icon/genre/TikTok.jpg'
import horrorImg from '@/assets/icon/genre/TikTok.jpg'
import briskImg from '@/assets/icon/genre/TikTok.jpg'
import funnyImg from '@/assets/icon/genre/TikTok.jpg'
import kidsImg from '@/assets/icon/genre/TikTok.jpg'
import foodImg from '@/assets/icon/genre/TikTok.jpg'
import dynamicImg from '@/assets/icon/genre/TikTok.jpg'
import relieveImg from '@/assets/icon/genre/TikTok.jpg'
import retroImg from '@/assets/icon/genre/TikTok.jpg'
import cuteImg from '@/assets/icon/genre/TikTok.jpg'
import sportImg from '@/assets/icon/genre/TikTok.jpg'
import makeupImg from '@/assets/icon/genre/TikTok.jpg'
import healImg from '@/assets/icon/genre/TikTok.jpg'
import petImg from '@/assets/icon/genre/TikTok.jpg'
import coolImg from '@/assets/icon/genre/TikTok.jpg'
import freshImg from '@/assets/icon/genre/TikTok.jpg'
import montageImg from '@/assets/icon/genre/TikTok.jpg'
import gameImg from '@/assets/icon/genre/TikTok.jpg'
import instrumentalImg from '@/assets/icon/genre/Instrumental.jpg'
import beatImg from '@/assets/icon/genre/Beat.jpg'
import vlogImg from '@/assets/icon/genre/Vlog.jpg'
import travelImg from '@/assets/icon/genre/Travel.jpg'
import genericImg from '@/assets/icon/style/generic.png'
import viralImg from '@/assets/icon/style/viralImg.png'
import painPointImg from '@/assets/icon/style/painPointImg.png'
import explosiveInfoImg from '@/assets/icon/style/explosiveInfoImg.png'
import positiveResultImg from '@/assets/icon/style/positive_result.png'
import illustrativeQuotesImg from '@/assets/icon/style/illustrativeQuotesImg.png'
import industryRevealImg from '@/assets/icon/style/industryRevealImg.png'
import benefitTransferImg from '@/assets/icon/style/benefits.png'
import opinionSharingImg from '@/assets/icon/style/opinion_sharing.png'
import knowledgeSharingImg from '@/assets/icon/style/knowledgeSharingImg.png'
import commonEndingImg from '@/assets/icon/style/commonEndingImg.png'
import Maikease from '@/assets/icon/inspire/Maikease.png'

// 工具栏图标
import HotSearchIcon from '@/assets/icon/tools/HotSearchIcon.png'
import MaterialSettingsIcon from '@/assets/icon/tools/MaterialSettingsIcon.png'
import AudioSettingsIcon from '@/assets/icon/tools/AudioSettingsIcon.png'
import FontSettingsIcon from '@/assets/icon/tools/FontSettingsIcon.png'
import VoiceSettingsIcon from '@/assets/icon/tools/VoiceSettingsIcon.png'
import VideoCreateIcon from '@/assets/icon/tools/VideoCreateIcon.png'

// 脚本语音
const scriptLanguageOptions = [
  { label: '自动检测', value: 'auto-detect' },
  { label: '中文', value: 'zh' },
  { label: '英文', value: 'en' },
]

// 新的文案风格选项
const videoStyleOptions = [
  {
    label: '麦克阿瑟',
    value: 'maikease',
    description: '不是文案想不起，而是麦克阿瑟体更有性价比',
    img: Maikease,
  },
  {
    label: '观点分享',
    value: 'opinion_sharing',
    description: '事实+个人感受+问题+观点+故事+总结',
    img: opinionSharingImg,
  },
  {
    label: '爆款开头',
    value: 'generic',
    description: '爆款+万能开头',
    img: genericImg,
  },
  {
    label: '精简有趣',
    value: 'viral_script',
    description: '精简+有趣+节奏+视觉冲击',
    img: viralImg,
  },
  {
    label: '共鸣痛点',
    value: 'pain_point',
    description: '现象+危害+原因+解决方法',
    img: painPointImg,
  },
  {
    label: '炸裂信息',
    value: 'explosive_info',
    description: '炸裂开头+立人设+高密度盘点+动式结尾',
    img: explosiveInfoImg,
  },
  {
    label: '积极结果',
    value: 'positive_result',
    description: '积极结果获得感+方案+互动式结尾',
    img: positiveResultImg,
  },
  {
    label: '例证金句',
    value: 'illustrative_quotes',
    description: '列金句+佐证+列金句+佐证',
    img: illustrativeQuotesImg,
  },
  {
    label: '行业揭秘',
    value: 'industry_reveal',
    description: '行业揭秘+塑造期待+解决方案',
    img: industryRevealImg,
  },
  {
    label: '利益传递',
    value: 'benefit_transfer',
    description: '利益传递+强化期待+解决办法+结尾',
    img: benefitTransferImg,
  },

  {
    label: '知识分享',
    value: 'knowledge_sharing',
    description: '问题描述+问题拆解+答案描述+答案拆解',
    img: knowledgeSharingImg,
  },
  {
    label: '常见结尾',
    value: 'common_ending',
    description: '互动式/共情式/Slogan/反转式',
    img: commonEndingImg,
  },
]
// 视频素材来源
const videoSourceOptions = [
  { label: 'Pexels', value: 'pexels' },
  { label: 'Pixabay', value: 'pixabay' },
  { label: '抖音', value: 'douyin' },
  { label: 'Youtube', value: 'youtube' },
  { label: '微博', value: 'weibo' },
]
//视频比例
const videoRatioOptions = [
  { label: '竖屏 9:16', value: '9:16' },
  { label: '横屏 16:9', value: '16:9' },
  { label: '4:3', value: '4:3' },
]
// 视频拼接方式
const videoLayoutOptions = [
  { label: 'AI拼接', value: 'random' },
  { label: '顺序拼接', value: 'asc' },
]
// 背景音乐类型
const bgmTypeOptions = [
  { label: 'AI自动选择风格', value: 'random' },
  { label: '曲库选取', value: 'customize' },
]
// 字幕所在位置
const subtitlePositionOptions = [
  { label: '顶部', value: 'top' },
  { label: '底部 (推荐)', value: 'bottom' },
  { label: '中间', value: 'middle' },
]

const voiceLanguages = {
  en: '英文',
  zh: '中文',
}
const voiceCountry = {
  US: '美语',
  TW: '台湾',
  CN: '普通话',
  HK: '粤语',
}
const voiceNames = {
  Xiaoxiao: '晓晓',
  Xiaoyi: '晓艺',
  Yunjian: '云健',
  Yunxi: '云希',
  Yunxia: '云夏',
  Yunyang: '云阳',
  'liaoning-Xiaobei': '辽宁-小贝',
  'shaanxi-Xiaoni': '陕西-小妮',
  HiuGaai: '希盖',
  HiuMaan: '希曼',
  WanLung: '王朗',
  HsiaoChen: '何晓晨',
  HsiaoYu: '萧宇',
  YunJhe: '尹杰',
}
// 音乐风格
const genreOptions = [
  { label: '全部', value: '', img: tiktokImg },
  { label: '抖音', value: 'TikTok', img: tiktokImg },
  { label: '纯音乐', value: 'Instrumental', img: instrumentalImg },
  { label: '卡点', value: 'Beat', img: beatImg },
  { label: 'Vlog', value: 'Vlog', img: vlogImg },
  { label: '旅行', value: 'Travel', img: travelImg },
  { label: '悬疑', value: 'Horror', img: horrorImg },
  { label: '轻快', value: 'Brisk', img: briskImg },
  { label: '搞怪', value: 'Funny', img: funnyImg },
  { label: '儿歌', value: 'Kids', img: kidsImg },
  { label: '美食', value: 'Food', img: foodImg },
  { label: '动感', value: 'Dynamic', img: dynamicImg },
  { label: '舒缓', value: 'Relieve', img: relieveImg },
  { label: '国风', value: 'Retro', img: retroImg },
  { label: '可爱', value: 'Cute', img: cuteImg },
  { label: '运动', value: 'Sport', img: sportImg },
  { label: '美妆', value: 'Makeup', img: makeupImg },
  { label: '伤感', value: 'Sad', img: tiktokImg },
  { label: '治愈', value: 'Heal', img: healImg },
  { label: '萌宠', value: 'Pet', img: petImg },
  { label: '酷炫', value: 'Cool', img: coolImg },
  { label: '清新', value: 'Fresh', img: freshImg },
  { label: '混剪', value: 'Montage', img: montageImg },
  { label: '游戏', value: 'Game', img: gameImg },
]
// 人声页面菜单导航栏类型
const VoiceNavBarType = Object.freeze({
  ONLINE: 'online',
  VIP: 'vip',
  RECENT: 'recent',
  CLONE: 'clones',
})
// 音乐页面菜单导航栏类型
const AudioNavBarType = Object.freeze({
  ONLINE: 'online',
  MYMUSIC: 'myMusic',
  RECENT: 'recent',
  FAVORITES: 'favorites',
})
// 播放的音乐类型
const MusicType = Object.freeze({
  VOICE: 'voice',
  BGM: 'bgm',
})
// 播放的音乐类型
const BgmType = Object.freeze({
  Random: 'random',
  NoBackgroundMusic: '',
  Customize: 'customize',
})
const TaskState = Object.freeze({
  FAILED: 'error',
  COMPLETE: 'finish',
  WAITING: 'wait',
  PROCESSING: 'process',
})
export {
  genreOptions,
  scriptLanguageOptions,
  videoSourceOptions,
  videoRatioOptions,
  videoLayoutOptions,
  subtitlePositionOptions,
  voiceLanguages,
  voiceCountry,
  MusicType,
  bgmTypeOptions,
  BgmType,
  voiceNames,
  videoStyleOptions,
  TaskState,
  MaterialSettingsIcon,
  AudioSettingsIcon,
  FontSettingsIcon,
  VoiceSettingsIcon,
  VideoCreateIcon,
  HotSearchIcon,
  VoiceNavBarType,
  AudioNavBarType,
}
