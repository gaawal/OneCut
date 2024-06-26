<template>
  <div class="video-editor">
    <div class="timeline">
      <div class="time-markers">
        <span v-for="marker in timeMarkers" :key="marker">{{ formatTime(marker) }}</span>
      </div>
      <div class="tracks">
        <div class="track video-track">
          <h4>视频轨道</h4>
          <div class="track-content">
            <div
              v-for="(video, index) in videos"
              :key="index"
              class="track-item"
              :style="getTrackItemStyle(video)"
              @click="selectVideo(video.url)"
            >
              <video
                ref="videoThumbnails"
                :src="video.url"
                preload="metadata"
                style="display: none"
                @loadeddata="captureThumbnail($event, index)"
              ></video>
              <img v-if="video.thumbnail" :src="video.thumbnail" alt="Video Thumbnail" />
              <span>{{ video.name }}</span>
            </div>
          </div>
        </div>
        <div v-if="audio" class="track audio-track">
          <h4>音频轨道</h4>
          <div class="track-content">
            <div class="track-item" :style="getTrackItemStyle(audio)">
              <audio controls :src="audio.url"></audio>
            </div>
          </div>
        </div>
        <div v-if="textTracks.length" class="track text-track">
          <h4>文本轨道</h4>
          <div class="track-content">
            <div
              v-for="(textTrack, index) in textTracks"
              :key="index"
              class="track-item"
              :style="getTrackItemStyle(textTrack)"
            >
              <p>{{ textTrack.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="preview">
      <video ref="videoPreview" controls width="100%"></video>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const timeMarkers = ref([0, 10, 20, 30, 40, 50, 60])
const videos = ref([
  { name: '视频1', url: '/videos/video1.mp4', startTime: 0, endTime: 10, thumbnail: '' },
  { name: '视频2', url: '/videos/video2.mp4', startTime: 10, endTime: 20, thumbnail: '' },
])
const audio = ref({ url: '/audio/audio.mp3', startTime: 0, endTime: 60 })
const textTracks = ref([
  { text: '这是第一个文本', startTime: 0, endTime: 15 },
  { text: '这是第二个文本', startTime: 20, endTime: 30 },
])
const currentPreview = ref('')

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs < 10 ? '0' : ''}${secs}`
}

const getTrackItemStyle = (track) => {
  return {
    left: `${track.startTime * 10}px`,
    width: `${(track.endTime - track.startTime) * 10}px`,
  }
}

const selectVideo = (url) => {
  currentPreview.value = url
  const videoPreview = videoPreviewRef.value
  videoPreview.src = url
  videoPreview.load()
  videoPreview.play()
}

const captureThumbnail = (event, index) => {
  const video = event.target
  const canvas = document.createElement('canvas')
  canvas.width = 160
  canvas.height = 90
  const context = canvas.getContext('2d')
  context.drawImage(video, 0, 0, canvas.width, canvas.height)
  videos.value[index].thumbnail = canvas.toDataURL('image/png')
}

onMounted(() => {
  const videoElements = videoThumbnailsRef.value
  videoElements.forEach((video, index) => {
    video.addEventListener('loadeddata', (event) => captureThumbnail(event, index))
  })
})

const videoPreviewRef = ref(null)
const videoThumbnailsRef = ref([])
</script>

<style scoped>
.video-editor {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
}

.timeline {
  flex: 1;
  overflow-x: scroll;
  padding: 10px;
  background-color: #f0f0f0;
}

.time-markers {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.tracks {
  display: flex;
  flex-direction: column;
}

.track {
  margin-bottom: 20px;
}

.track h4 {
  margin: 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #ddd;
}

.track-content {
  position: relative;
  height: 80px;
  background-color: #fff;
  border: 1px solid #ddd;
}

.track-item {
  position: absolute;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #d0d0d0;
  border-right: 1px solid #bbb;
  cursor: pointer;
}

.track-item img {
  width: 100px;
  height: 56px;
  object-fit: cover;
  margin-right: 5px;
}

.track-item span {
  font-size: 12px;
  color: #333;
}

.track-item p {
  margin: 0;
  padding: 0 5px;
  font-size: 14px;
  color: #333;
}

.preview {
  flex: none;
  height: 300px;
  background-color: #000;
}
</style>
