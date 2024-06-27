<template>
  <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  audioData: {
    type: Array,
    required: true,
  },
  canvasId: {
    type: String,
    required: true,
  },
})

const waveformCanvas = ref(null)

const drawWaveform = () => {
  const canvas = waveformCanvas.value
  const context = canvas.getContext('2d')

  // 设置canvas大小为高分辨率
  const width = canvas.offsetWidth
  const height = canvas.offsetHeight
  const devicePixelRatio = window.devicePixelRatio || 1

  canvas.width = width * devicePixelRatio
  canvas.height = height * devicePixelRatio
  context.scale(devicePixelRatio, devicePixelRatio)

  // 清除画布
  context.clearRect(0, 0, width, height)

  // 设置样式
  context.fillStyle = '#333'
  context.fillRect(0, 0, width, height)
  context.lineWidth = 2 // 增加线条宽度
  context.strokeStyle = '#7e6fd0'

  const sliceWidth = width / (props.audioData.length / 4) // 减少绘制的点数，增加稀疏度
  const centerY = height / 2

  context.beginPath()
  let x = 0
  for (let i = 0; i < props.audioData.length; i += 4) {
    // 每4个数据点绘制一次
    const v = props.audioData[i]
    const y = centerY + v * centerY

    context.moveTo(x, centerY)
    context.lineTo(x, y)
    context.moveTo(x, centerY)
    context.lineTo(x, centerY - (y - centerY))

    x += sliceWidth
  }

  context.stroke()
}

onMounted(() => {
  drawWaveform()
})

watch(
  () => props.audioData,
  () => {
    nextTick(drawWaveform)
  }
)
</script>

<style scoped>
.waveform-canvas {
  width: 100%;
  height: 80px;
  background: #333;
  border-radius: 5px;
}
</style>
