<template>
  <div class="main-container">
    <!-- 左侧文案输入区 -->
    <div class="llm-left-container">
      <NForm label-placement="top" label-align="left">
        <NGradientText style="padding: 5px" :size="14" type="danger">
          *描述您的创作主题或想要表达的内容
        </NGradientText>
        <NInput
          v-model:value="videoStore.videoTheme"
          type="textarea"
          autosize
          placeholder="输入视频主题"
          style="max-height: 8vh; max-width: 90%"
        />
        <NGradientText style="padding: 5px" :size="14" type="danger">
          请选择生成的文案风格
        </NGradientText>

        <div class="video-category-container">
          <div class="radio-buttons-container">
            <NButton
              v-for="option in videoStyleOptions"
              :key="option.value"
              :class="['radio-button', { selected: videoStore.videoCategory === option.value }]"
              strong
              secondary
              type="primary"
              class="radio-button"
              @click="videoStore.videoCategory = option.value"
            >
              <div class="radio-top">
                <img :src="option.img" alt="icon" class="radio-icon" />
                <div class="radio-label">{{ option.label }}</div>
              </div>
              <div class="radio-description">
                {{ option.description }}
              </div>
            </NButton>
          </div>
        </div>

        <div class="llm-left-buttom">
          <div class="word-count-label">
            <NGradientText style="padding: 5px" :size="14" type="danger"> 字数 </NGradientText>
            <NInputNumber v-model:value="videoStore.wordCount" />
          </div>

          <div class="script-button-group">
            <NButton
              strong
              secondary
              type="success"
              class="tool-button"
              @click="videoStore.handleGenerateScript"
            >
              <div class="tool-button-container">
                <img :src="GenerateTextIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">生成文案</div>
              </div>
            </NButton>

            <NButton
              strong
              secondary
              type="warning"
              class="tool-button"
              @click="videoStore.handleResetScript"
            >
              <div class="tool-button-container">
                <img :src="CancelIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">清空文案</div>
              </div>
            </NButton>
          </div>
        </div>
      </NForm>
    </div>

    <!-- 右侧文案生成区 -->
    <div class="llm-right-container">
      <div class="llm-preview-container">
        <div class="video-title-area">
          <NGradientText :size="24" type="warning">
            {{ videoStore.videoTitle }}
          </NGradientText>
        </div>
        <div class="input-container">
          <NInput
            v-model:value="videoStore.videoScript"
            class="paragraph-card"
            placeholder="生成的文案在此展示"
            type="textarea"
            autosize
            style="font-size: 16px"
          />
          <div v-if="videoStore.loadingScript" class="loading-script-container">
            <NSpin />
            <div class="loading-text">文案努力生成中...</div>
          </div>
          <div class="keywords-container">
            <div :class="['word-count', { exceeded: videoStore.wordCountExceeded }]">
              {{ videoStore.videoScript.length }}/{{ videoStore.wordCount }}
            </div>
          </div>
          <div class="action-buttons">
            <NButton
              strong
              secondary
              type="primary"
              class="tool-button"
              @click="videoStore.handleAIRefinementSciprt"
              @mouseover="showTooltip('AI润色消耗10积分')"
              @mouseleave="hideTooltip"
              ><div class="tool-button-container">
                <img :src="AIRefinementIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">AI润色</div>
              </div>
            </NButton>
            <NButton
              strong
              secondary
              type="primary"
              class="tool-button"
              @click="videoStore.handleAIContinueSciprt"
              @mouseover="showTooltip('AI续写消耗20积分')"
              @mouseleave="hideTooltip"
              ><div class="tool-button-container">
                <img :src="AIContinueIcon" alt="icon" class="tool-button-icon" />
                <div class="tool-button-label">AI续写</div>
              </div>
            </NButton>
            <div v-if="tooltip.visible" class="tooltip">{{ tooltip.text }}</div>
          </div>
        </div>

        <div v-if="videoStore.videoKeywords.length" class="keywords">
          <NGradientText :size="14" type="danger"> 关键词 </NGradientText>
          <span v-for="(keyword, index) in videoStore.videoKeywords" :key="index">
            <div class="keyword">
              <NGradientText :size="14" type="danger"> {{ keyword }} </NGradientText>
            </div>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useVideoStore } from '@/store'
import { videoStyleOptions } from '@/config/videoOptions'
import { GenerateTextIcon, CancelIcon, AIRefinementIcon, AIContinueIcon } from '@/config/videoIcons'

const videoStore = useVideoStore()

const tooltip = ref({
  visible: false,
  text: '',
})

const showTooltip = (text) => {
  tooltip.value.text = text
  tooltip.value.visible = true
}

const hideTooltip = () => {
  tooltip.value.visible = false
}
</script>

<style scoped>
.video-title-area {
  margin-top: 20px;
  display: flex;
  width: 45%;
}
.main-container {
  display: flex;
  width: 100%;
  height: 100vh;
  gap: 5px;
}
.llm-left-container {
  height: auto;
  width: 45%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: orange transparent;
}
.llm-left-container::-webkit-scrollbar {
  width: 8px;
}
.llm-left-container::-webkit-scrollbar-thumb {
  background-color: orange;
  border-radius: 10px;
}
.llm-left-container::-webkit-scrollbar-track {
  background: transparent;
}
.video-category-container {
  display: flex;
  height: 55vh;
  overflow-y: auto;
  flex-wrap: wrap;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: orange transparent;
  margin-bottom: 20px;
}
.video-category-container::-webkit-scrollbar {
  width: 8px;
}
.video-category-container::-webkit-scrollbar-thumb {
  background-color: orange;
  border-radius: 10px;
}
.video-category-container::-webkit-scrollbar-track {
  background: transparent;
}
.radio-buttons-container {
  display: flex;
  justify-content: flex-start;
  height: 50vh;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px;
}
.radio-button {
  padding: 15px;
  border-radius: 10px;
  display: flex;
  justify-content: flex-start;
  flex-direction: column;
  align-items: flex-start;
  width: 45%;
  height: auto;
  z-index: 1000;
  backdrop-filter: blur(10px);
  transition: all 0.4s ease;
  box-shadow: 0 4px 5px rgba(0, 0, 0, 0.2);
}
.radio-button:hover {
  transform: translateY(-5px);
}
.radio-button:active {
  transform: translateY(2px);
}
.radio-button.selected {
  border: 2px solid #ff3e3e;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.radio-top {
  display: flex;
  align-items: center;
  width: 100%;
}
.radio-icon {
  width: 40px;
  height: 40px;
  margin-right: 10px;
}
.radio-label {
  font-size: 14px;
  font-weight: bold;
  color: #f4511e;
}
.radio-description {
  font-size: 12px;
  color: rgba(142, 148, 155, 0.87);
  text-align: center;
  white-space: normal;
  word-wrap: break-word;
  height: auto;
}
.llm-left-buttom {
  height: 8vh;
  width: 90%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 5px;
}
.word-count-label {
  display: flex;
  width: 30%;
  justify-content: flex-start;
  align-items: center;
  gap: 1px;
}
.llm-right-container {
  width: 55%;
  height: 75vh;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.llm-preview-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  scrollbar-width: thin;
  scrollbar-color: orange transparent;
}
.llm-preview-container::-webkit-scrollbar {
  width: 8px;
}
.llm-preview-container::-webkit-scrollbar-thumb {
  background-color: orange;
  border-radius: 10px;
}
.llm-preview-container::-webkit-scrollbar-track {
  background: transparent;
}
.loading-script-container {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  z-index: 1000;
}
.loading-text {
  margin-top: 10px;
  padding: 10px;
  font-size: 16px;
  color: #d55874;
  animation: pulse 1.5s infinite, scale 1.5s infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
@keyframes scale {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(0.9);
  }
}
.input-container {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 40%;
}
.word-count {
  position: absolute;
  right: 10px;
  bottom: 10px;
  font-size: 12px;
  color: rgba(187, 187, 187, 0.98);
}
.word-count.exceeded {
  color: rgba(255, 0, 0, 0.71);
}
.paragraph-card {
  width: 100%;
  flex: 1;
  padding: 5px;
  border-radius: 10px;
  overflow-y: hidden;
  overflow-x: hidden;
  white-space: normal;
  word-wrap: break-word;
  position: relative;
  padding-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.paragraph-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}
.keywords-container {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.keywords {
  padding: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.keyword {
  color: #e91e63;
  border-radius: 4px;
}
.script-button-group {
  display: flex;
  justify-content: flex-end;
  width: 50%;
  gap: 10px;
}
.tool-button-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: row;
  width: 100%;
}
.tool-button-icon {
  width: 20px;
  height: 20px;
  margin-left: 3px;
}
.tool-button {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  transition: all 0.3s ease;
}
.tool-button:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}
.tool-button-label {
  display: flex;
  font-weight: bold;
  align-items: center;
  margin-left: 5px;
}
.action-buttons {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}
.tooltip {
  position: absolute;
  bottom: 40px;
  left: 10px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 5px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 1001;
}
</style>
