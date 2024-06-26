<template>
  <NModal
    v-model:show="videoStore.showTaskProgressModal"
    preset="dialog"
    close-on-esc
    style="width: 85%"
    title="视频生成进度"
  >
    <NCard>
      <div class="task-progress-container">
        <h3>{{ videoStore.videoTitle }}</h3>
        <NSteps
          :current="currentStep"
          :status="progressState"
          size="small"
          style="margin-bottom: 20px"
        >
          <NStep v-for="(step, index) in steps" :key="index" :title="step.title" />
        </NSteps>
        <div class="progress-info">
          <NProgress type="circle" :percentage="progressPercentage" show-info>
            <template #info>
              <div class="progress-info-content">
                <div>{{ progressPercentage }}%</div>
                <div>{{ currentStepTitle }}</div>
              </div>
            </template>
          </NProgress>
        </div>
        <p>{{ taskDetailState }}</p>
      </div>
    </NCard>
  </NModal>
</template>

<script setup>
import { computed } from 'vue'
import { useVideoStore } from '@/store'

const videoStore = useVideoStore()

const steps = [
  { title: '生成文案' },
  { title: '生成音频' },
  { title: '生成字幕' },
  { title: '下载素材' },
  { title: '合并素材' },
  { title: '多轨合成' },
  { title: '完成' },
]

const currentStep = computed(() => videoStore.currentStep)
const progressState = computed(() => videoStore.progressState)
const taskDetailState = computed(() => videoStore.taskDetailState)
const progressPercentage = computed(() => videoStore.progressPercentage)
const currentStepTitle = computed(() => {
  return currentStep.value > 0 && currentStep.value <= steps.length
    ? steps[currentStep.value - 1].title
    : ''
})
</script>

<style scoped>
.task-progress-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.progress-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px;
}

.progress-info-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
