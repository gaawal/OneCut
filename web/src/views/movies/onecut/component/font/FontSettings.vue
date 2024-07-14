<template>
  <div class="subtitle-config-container">
    <div class="settings-panel">
      <div class="panel-header">
        <Icon size="24" style="margin-right: 5px">
          <Text />
        </Icon>
        <h3>字幕设置</h3>
      </div>
      <NForm label-placement="left" label-align="left" :label-width="videoStore.labelWidth">
        <NFormItem label="启用字幕">
          <NSwitch v-model:value="videoStore.enableSubtitles" />
        </NFormItem>
        <template v-if="videoStore.enableSubtitles">
          <NFormItem label="字幕字体">
            <NInput v-model:value="videoStore.subtitleFont" placeholder="选择字体文件" />
          </NFormItem>
          <NFormItem label="字幕位置">
            <NSelect
              v-model:value="videoStore.subtitlePosition"
              :options="subtitlePositionOptions"
            />
          </NFormItem>
          <NFormItem label="字幕大小">
            <NSlider v-model:value="videoStore.subtitleSize" :min="50" :max="80" />
          </NFormItem>
          <NFormItem label="字体颜色">
            <NColorPicker v-model:value="videoStore.subtitleColor" />
          </NFormItem>
          <NFormItem label="字体背景颜色">
            <NColorPicker v-model:value="videoStore.subtitleBackgroundColor" />
          </NFormItem>
          <NFormItem label="描边颜色">
            <NColorPicker v-model:value="videoStore.subtitleStrokeColor" />
          </NFormItem>
          <NFormItem label="描边粗细">
            <NSlider v-model:value="videoStore.subtitleStrokeWidth" :min="3" :max="4" step="0.1" />
          </NFormItem>
          <NFormItem label="字体透明度">
            <NSlider v-model:value="videoStore.subtitleOpacity" :min="0.1" :max="1" step="0.1" />
          </NFormItem>
        </template>
      </NForm>
    </div>

    <div class="preview-panel">
      <h3>预览效果</h3>
      <div class="preview-container" :style="previewContainerStyle">
        <div
          v-if="videoStore.enableSubtitles"
          class="subtitle-preview"
          :style="subtitlePreviewStyle"
        >
          这是预览字幕文本
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useVideoStore } from '@/store'
import { Icon } from '@vicons/utils'
import { Text } from '@vicons/ionicons5'
import { subtitlePositionOptions } from '@/config/videoOptions'
import { computed } from 'vue'

const videoStore = useVideoStore()

const previewContainerStyle = computed(() => {
  const aspect = videoStore.videoRatio === '16:9' ? 9 / 16 : 16 / 9
  return {
    width: '100%',
    paddingBottom: `${aspect * 100}%`,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    position: 'relative',
    overflow: 'hidden',
  }
})

const subtitlePreviewStyle = computed(() => {
  const position = {}
  switch (videoStore.subtitlePosition) {
    case 'top':
      position.top = '10px'
      break
    case 'bottom':
      position.bottom = '10px'
      break
    case 'middle':
      position.top = '50%'
      position.transform = 'translate(-50%, -50%)'
      break
  }

  const fontSizeRatio = 0.2
  const strokeWidthRatio = 0.1

  return {
    position: 'absolute',
    left: '50%',
    transform: `translateX(-50%) ${position.transform || ''}`,
    fontFamily: videoStore.subtitleFont || 'Arial',
    fontSize: `${videoStore.subtitleSize * fontSizeRatio}px`,
    color: videoStore.subtitleColor,
    backgroundColor: videoStore.subtitleBackgroundColor,
    padding: '5px',
    textAlign: 'center',
    maxWidth: '90%',
    opacity: videoStore.subtitleOpacity,
    WebkitTextStroke: `${videoStore.subtitleStrokeWidth * strokeWidthRatio}px ${
      videoStore.subtitleStrokeColor
    }`,
    textStroke: `${videoStore.subtitleStrokeWidth * strokeWidthRatio}px ${
      videoStore.subtitleStrokeColor
    }`,
    ...position,
  }
})
</script>

<style scoped>
.subtitle-config-container {
  display: flex;
  width: 100%;
  margin: 10px;
  gap: 20px;
}

.settings-panel {
  flex: 1;
}

.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  color: #e91e63;
  margin-bottom: 15px;
}

.preview-container {
  border: 1px solid #ccc;
  border-radius: 4px;
}

.subtitle-preview {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
