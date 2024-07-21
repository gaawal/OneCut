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
        <div v-if="progressPercentage !== 100">
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
            <p>{{ taskDetailState }}</p>
          </div>
        </div>
        <div v-if="progressPercentage === 100" class="video-container">
          <video ref="videoPlayer" :src="videoUrl" controls style="width: 100%"></video>
        </div>
      </div>
    </NCard>
  </NModal>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import axios from 'axios'
import { useVideoStore } from '@/store'
import { getToken } from '@/utils'

const videoStore = useVideoStore()
const videoUrl = ref('')

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

// Watcher to detect when video generation is complete
watch(progressPercentage, async (newPercentage) => {
  if (newPercentage === 100) {
    try {
      const response = await axios.get(`/api/v1/video/stream_video`, {
        headers: { token: getToken() },
        params: { task_id: videoStore.videoTaskId },
        responseType: 'blob',
      })
      videoUrl.value = URL.createObjectURL(response.data)
    } catch (error) {
      console.error('Error fetching video:', error)
    }
  }
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

.video-container {
  margin-top: 20px;
  width: 100%;
}
</style>
