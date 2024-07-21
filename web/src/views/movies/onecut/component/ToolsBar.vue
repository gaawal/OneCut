<template>
  <div class="fixed-header">
    <div class="header-container">
      <!-- 剪辑功能区 -->
      <div class="edit-functions">
        <NPopover
          style="width: 800px; max-height: 80vh"
          :overlap="overlap"
          placement="bottom-start"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="HotSearchIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">热点</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <HotScripts />
          </div>
        </NPopover>
        <NPopover
          style="width: 800px; max-height: 80vh"
          :overlap="overlap"
          placement="bottom-start"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="InspirationIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">灵感</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <Inspires />
          </div>
        </NPopover>
        <NPopover
          style="width: 800px; max-height: 80vh"
          :overlap="overlap"
          placement="bottom-start"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="LinkExtractIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">链接</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <HotScripts />
          </div>
        </NPopover>
        <NPopover :overlap="overlap" placement="bottom-start" trigger="click">
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="MaterialSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">素材</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <MaterialSettings />
          </div>
        </NPopover>

        <NPopover
          :overlap="overlap"
          placement="bottom"
          style="max-width: 1000px; max-height: 100vh"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="AudioSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">音乐</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <AudioSettings />
          </div>
        </NPopover>
        <NPopover
          :overlap="overlap"
          placement="bottom-start"
          style="max-width: 1000px; max-height: 100vh"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="VoiceSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">人声</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <VoiceSettings />
          </div>
        </NPopover>

        <NPopover
          :overlap="overlap"
          style="width: 800px; max-height: 100vh"
          placement="bottom-start"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="FontSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">字幕</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <FontSettings />
          </div>
        </NPopover>
        <NPopover :overlap="overlap" placement="bottom-start" trigger="click">
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="LogoSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">水印</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <FontSettings />
          </div>
        </NPopover>
        <NPopover :overlap="overlap" placement="bottom-start" trigger="click">
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="BackgroudSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">背景</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <FontSettings />
          </div>
        </NPopover>
        <NPopover
          style="width: 800px; max-height: 80vh"
          :overlap="overlap"
          placement="bottom-start"
          trigger="click"
        >
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="ImportDocumentIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">文档</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <HotScripts />
          </div>
        </NPopover>

        <NPopover :overlap="overlap" placement="bottom-start" trigger="click">
          <template #trigger>
            <NButton strong secondary type="primary" class="tool-button">
              <div class="tool-button-container">
                <img :src="SystemSettingsIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">设置</div>
              </div>
            </NButton>
          </template>
          <div class="video-setting-container">
            <FontSettings />
          </div>
        </NPopover>
      </div>
      <!-- 导出功能区 -->
      <div class="export-functions">
        <NButton strong secondary type="success" class="export-button" @click="handleGenerateVideo">
          <div class="tool-button-container">
            <img :src="VideoCreateIcon" alt="icon" class="tool-button-icon" />
            <div class="tool-button-label">生成视频</div>
          </div>
        </NButton>
        <NButton strong secondary type="success" class="export-button" @click="handleExportVideo">
          导出视频
        </NButton>
      </div>
    </div>
  </div>

  <TaskProgressCard />
</template>

<script setup>
import api from '@/api'
import { useVideoStore } from '@/store'
import { TaskState } from '@/config/videoOptions' //导入视频参数表单选项参数

import {
  MaterialSettingsIcon,
  AudioSettingsIcon,
  FontSettingsIcon,
  VoiceSettingsIcon,
  VideoCreateIcon,
  HotSearchIcon,
  LogoSettingsIcon,
  BackgroudSettingsIcon,
  SystemSettingsIcon,
  LinkExtractIcon,
  ImportDocumentIcon,
  InspirationIcon,
} from '@/config/videoIcons' //导入视频图标
import HotScripts from './hotspot/HotScripts.vue'
import Inspires from './inspiration/Inspires.vue'
import MaterialSettings from './material/MaterialSettings.vue'
import AudioSettings from './audio/AudioSettings.vue'
import VoiceSettings from './voice/VoiceSettings.vue'
import FontSettings from './font/FontSettings.vue'
import TaskProgressCard from './task/TaskProgressCard.vue'

const stepsOrder = [
  'generating_script',
  'generating_audio',
  'generating_subtitle',
  'downloading_videos',
  'combining_videos',
  'generating_final_video',
  'final_video_generation_complete',
]

const stepsMap = {
  generating_script: '生成文案',
  script_generation_complete: '文案生成完成',
  generating_audio: '生成音频中...',
  audio_generation_complete: '音频生成完成',
  generating_subtitle: '生成字幕中...',
  subtitle_generation_complete: '字幕生成完成',
  downloading_videos: '下载视频素材中...',
  video_download_complete: '视频素材下载完成',
  combining_videos: '合并视频素材片段中...',
  combined_videos_complete: '素材拼接完成',
  generating_final_video: '多轨合并中...',
  final_video_generation_complete: '视频生成完成',
}

const overlap = ref(false)
const videoStore = useVideoStore()

const handleGenerateVideo = async () => {
  videoStore.showTaskProgressModal = true
  videoStore.progressPercentage = 1
  videoStore.currentStep = 1
  const params = {
    video_subject: videoStore.videoTheme,
    video_script: videoStore.videoScript,
    word_count: videoStore.wordCount,
    video_category: videoStore.videoCategory,
    video_terms: videoStore.videoKeywords,
    video_aspect: videoStore.videoRatio,
    video_concat_mode: videoStore.videoLayout,
    video_clip_duration: videoStore.videoMaxLength,
    video_count: videoStore.videoCount,
    video_source: videoStore.videoSource,
    video_materials: [
      {
        provider: 'pexels',
        url: '',
        duration: 0,
      },
    ],
    video_language: videoStore.scriptLanguage,
    voice_name: videoStore.selectedVoiceLabel,
    voice_volume: 1,
    bgm_type: videoStore.bgmType,
    bgm_file: videoStore.selectedBgmLabel,
    bgm_volume: videoStore.bgmVolume,
    subtitle_enabled: videoStore.enableSubtitles,
    subtitle_position: videoStore.subtitlePosition,
    font_name: videoStore.subtitleFont,
    text_fore_color: videoStore.subtitleColor,
    text_background_color: videoStore.subtitleBackgroundColor,
    font_size: videoStore.subtitleSize,
    stroke_color: videoStore.subtitleBorderColor,
    stroke_width: videoStore.subtitleStrokeWidth,
    n_threads: 8,
    paragraph_number: 1,
    amount: 5,
    weibo_mid: videoStore.weiboMid,
    weibo_title: videoStore.weiboTitle,
  }
  console.log(JSON.stringify(params))
  try {
    const response = await api.createVideos(params)
    console.log('TaskResponse', JSON.stringify(response.data))
    const statusCode = response.code
    console.log('StatusCode', statusCode)
    if (statusCode === 200) {
      videoStore.videoTaskId = response.data.task_id
      $message.success('创建文生视频任务成功')
      pollTaskProgress()
    } else if (statusCode === 400) {
      $message.info(response.data.msg || '请求错误，请检查输入参数')
    } else {
      $message.error(`视频生成失败: ${response.data.msg || '未知错误'}`)
    }
  } catch (error) {
    console.error('生成视频时出错:', error)
    $message.error(`视频生成失败，请重试。错误信息: ${error.message || '未知错误'}`)
  }
}
const handleExportVideo = () => {
  // 实现导出视频的逻辑
}
// 轮训获取任务状态
const pollTaskProgress = () => {
  const interval = setInterval(async () => {
    try {
      const response = await api.getVideoTask(videoStore.videoTaskId)
      if (response.code === 200) {
        const progress = response.data
        const currentStepIndex = stepsOrder.indexOf(progress.detail_state)
        videoStore.currentStep = currentStepIndex + 1
        videoStore.taskDetailState = stepsMap[progress.detail_state] || '正在处理中...'
        videoStore.progressPercentage = progress.progress || 0
        videoStore.progressState = progress.state

        if (progress.state === TaskState.FAILED) {
          clearInterval(interval)
          videoStore.taskDetailState = '视频生成失败'
        } else if (progress.state === TaskState.COMPLETE) {
          clearInterval(interval)
          videoStore.taskDetailState = '视频生成完成'
        }
      } else {
        clearInterval(interval)
        videoStore.taskDetailState = '获取任务进度失败'
      }
    } catch (error) {
      clearInterval(interval)
      videoStore.taskDetailState = '获取任务进度时出错'
    }
  }, 10000) // 每10秒轮询一次
}
</script>
<style scoped>
.video-setting-container {
  display: flex;
  justify-content: flex-start;
  gap: 20px;
}
.fixed-header {
  position: sticky;
  display: flex;
  height: auto;
  justify-content: space-between;
  align-items: center;
  flex-direction: row;
  z-index: 1000;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  padding: 10px;
  margin-bottom: 5px;
}
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.edit-functions {
  display: flex;
  justify-content: flex-start;
  gap: 10px;
}
.tool-button-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: row;
  width: 100%;
}
.tool-button {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 5px;
  transition: all 0.3s ease;
}
.tool-button:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}
.tool-button-icon {
  width: 25px;
  height: 25px;
  margin-left: 1px;
}
.tool-button-label {
  display: flex;
  font-weight: bold;
  align-items: center;
  margin-left: 5px;
}
.export-functions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}
.export-button {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  margin-left: 10px;
}
.export-button:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}
</style>
