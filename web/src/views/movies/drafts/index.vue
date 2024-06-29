<script setup>
import { ref, onMounted } from 'vue'
import ToolsBar from '../onecut/component/ToolsBar.vue'
const scenes = ref([])
const selectedScene = ref(null)
const videoKey = ref(0)

onMounted(async () => {
  // Mock data based on the provided structure
  const response = {
    code: 1,
    msg: 'SUCCESS',
    data: {
      title: '胡塞武装为何如此强大？',
      scenes: [
        {
          sceneId: '112128484224975782',
          script:
            '胡塞武装为什么这么厉害？这是一个让人好奇的问题。胡塞武装，又称也门胡塞武装，是也门内战中的重要力量。他们凭什么能够在这场战争中如此强大呢？',
          duration: 11808,
          startTime: '00:00',
          endTime: '00:11',
          keywords: ['胡塞武装', '军事武器'],
          materials: [
            {
              mediaId: '6964833549132267520',
              videoUrl: '/videos/video1.mp4',
              videoId: ['6964833549132267520', '6964833549132267520'],
              pictureUrl: '/thumbnail/demo.png',
            },
          ],
        },
        {
          sceneId: '112128484224975783',
          script:
            '事实上，要解答这个问题，我们需要回顾一下历史。胡塞武装起源于20世纪90年代的也门，当时也门南北统一后，政治矛盾逐渐加剧。在过去的几十年里，胡塞武装经历了多次战争和冲突。',
          duration: 13860,
          startTime: '00:12',
          endTime: '00:25',
          keywords: ['胡塞武装', '军事武器'],
          materials: [
            {
              mediaId: '6964833549132267520',
              videoId: ['6964833549132267520'],
              videoUrl: '/videos/video3.mp4',
              pictureUrl: '/thumbnail/demo.png',
            },
          ],
        },
        {
          sceneId: '112128484224975783',
          script:
            '事实上，要解答这个问题，我们需要回顾一下历史。胡塞武装起源于20世纪90年代的也门，当时也门南北统一后，政治矛盾逐渐加剧。在过去的几十年里，胡塞武装经历了多次战争和冲突。',
          duration: 13860,
          startTime: '00:12',
          endTime: '00:25',
          keywords: ['胡塞武装', '军事武器'],
          materials: [
            {
              mediaId: '6964833549132267520',
              videoId: ['6964833549132267520'],
              videoUrl: '/videos/video3.mp4',
              pictureUrl: '/thumbnail/demo.png',
            },
          ],
        },
        {
          sceneId: '112128484224975783',
          script:
            '事实上，要解答这个问题，我们需要回顾一下历史。胡塞武装起源于20世纪90年代的也门，当时也门南北统一后，政治矛盾逐渐加剧。在过去的几十年里，胡塞武装经历了多次战争和冲突。',
          duration: 13860,
          startTime: '00:12',
          endTime: '00:25',
          keywords: ['胡塞武装', '军事武器'],
          materials: [
            {
              mediaId: '6964833549132267520',
              videoId: ['6964833549132267520'],
              videoUrl: '/videos/video3.mp4',
              pictureUrl: '/thumbnail/demo.png',
            },
          ],
        },
        {
          sceneId: '112128484224975783',
          script:
            '事实上，要解答这个问题，我们需要回顾一下历史。胡塞武装起源于20世纪90年代的也门，当时也门南北统一后，政治矛盾逐渐加剧。在过去的几十年里，胡塞武装经历了多次战争和冲突。',
          duration: 13860,
          startTime: '00:12',
          endTime: '00:25',
          keywords: ['胡塞武装', '军事武器'],
          materials: [
            {
              mediaId: '6964833549132267520',
              videoId: ['6964833549132267520'],
              videoUrl: '/videos/video3.mp4',
              pictureUrl: '/thumbnail/demo.png',
            },
          ],
        },
      ],
    },
  }

  if (response.code === 1) {
    scenes.value = response.data.scenes
    if (scenes.value.length > 0) {
      selectedScene.value = scenes.value[0]
    }
  }
})

const selectScene = (scene) => {
  selectedScene.value = { ...scene }
  videoKey.value++
}
</script>

<template>
  <ToolsBar />
  <div class="main-container">
    <div class="resource-container">
      <div v-for="scene in scenes" :key="scene.sceneId" class="scene-card">
        <NCard class="card" @click="selectScene(scene)">
          <div class="card-content">
            <img :src="scene.materials[0].pictureUrl" alt="素材图片" class="material-img" />
            <div class="card-details">
              <div class="scene-script">{{ scene.script }}</div>
              <div class="card-footer">
                <span>{{ scene.startTime }} - {{ scene.endTime }}</span>
                <div class="card-buttons">
                  <NButton size="small" type="primary">替换</NButton>
                  <NButton size="small" type="primary">插入</NButton>
                  <NButton size="small" type="primary">更多</NButton>
                </div>
              </div>
            </div>
          </div>
        </NCard>
      </div>
    </div>
    <div v-if="selectedScene" class="preview-container">
      <NCard class="full-height-card">
        <div class="audio-controls">
          <NButton size="small" type="primary">背景音乐</NButton>
          <NButton size="small" type="primary">人声</NButton>
        </div>
        <div class="video-container">
          <video :key="videoKey" controls class="preview-video">
            <source :src="selectedScene.materials[0].videoUrl" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
        <div class="scene-info">
          <div>素材时长: {{ selectedScene.startTime }} - {{ selectedScene.endTime }}</div>
          <div class="scene-title">{{ selectedScene.script }}</div>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.main-container {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  width: 100%;
  height: 100vh;
  margin: 0;
}
.resource-container {
  width: 50%;
  max-height: 85vh; /* 确保容器高度适配视口 */
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}
.scene-card {
  cursor: pointer;
}
.card {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
}
.card-content {
  display: flex;
  flex-direction: row;
  width: 100%;
}
.material-img {
  width: 30%;
  height: auto;
}
.card-details {
  width: 70%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.scene-script {
  font-size: 14px;
  margin-bottom: 10px;
  margin-left: 10px;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-left: 10px;
}
.card-buttons {
  display: flex;
  gap: 5px;
}
.preview-container {
  width: 50%;
  max-height: 85vh; /* 确保容器高度适配视口 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0;
  overflow: hidden;
}
.full-height-card {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 0;
}
.audio-controls {
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
}
.video-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  flex-grow: 1;
}
.preview-video {
  width: 100%;
  height: auto;
  max-height: calc(100vh - 120px);
  aspect-ratio: 16 / 9;
  background: black;
}
.scene-info {
  text-align: center;
  padding: 10px;
}
</style>
