<template>
  <NSpin v-if="videoStore.loadingBgms"></NSpin>

  <div class="cards-container">
    <div
      v-for="(music, index) in filteredMusic"
      :key="music.name"
      class="audio-card"
      @click="selectMusic(music)"
    >
      <div class="music-card-content">
        <div class="music-info-container">
          <img
            v-if="music.image"
            :src="'data:image/jpeg;base64,' + music.image"
            alt="Album Cover"
            class="album-cover"
          />
          <div class="music-info">
            <span v-if="music.title" class="music-title">{{ music.title }}</span>
            <span v-else class="music-title">{{ music.name }}</span>
            <span class="music-duration">{{ music.duration }} {{ music.artist }}</span>
            <span class="music-genre">{{ music.genres }}</span>
          </div>
        </div>
        <div class="music-waveform">
          <WaveformCanvas :audio-data="music.waveform" :canvas-id="'waveform-' + index" />
        </div>
        <div class="music-controls">
          <Icon
            v-if="!videoStore.isPlayingArray[index]"
            class="control-icon"
            size="24"
            @click.stop="togglePlayAudio(index, filteredMusic, MusicType.BGM)"
          >
            <PlayCircleSharp />
          </Icon>
          <Icon
            v-else
            class="control-icon"
            size="24"
            @click.stop="togglePlayAudio(index, filteredMusic, MusicType.BGM)"
          >
            <PauseCircle />
          </Icon>
          <Icon class="control-icon favorite" size="24" @click.stop="toggleFavorite(index)">
            <HeartOutline />
          </Icon>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useVideoStore } from '@/store'
import { watch, ref, onMounted, onBeforeUnmount } from 'vue'
import api from '@/api'
import axios from 'axios'
import { Icon } from '@vicons/utils'
import { PlayCircleSharp, PauseCircle, HeartOutline } from '@vicons/ionicons5'
import { MusicType } from '@/config/videoOptions'
import WaveformCanvas from './WaveformCanvas.vue'

const videoStore = useVideoStore()
const filteredMusic = ref([])

const closeAudio = () => {
  videoStore.isPlayingArray = new Array(videoStore.bgmOptions.length).fill(false)
  if (videoStore.currentAudio) {
    videoStore.currentAudio.pause()
    videoStore.currentAudio.currentTime = 0
  }
}

const selectMusic = (music) => {
  videoStore.selectedBgmLabel = music.label
}

const togglePlayAudio = async (index, playOptions, musicType) => {
  try {
    if (!playOptions || !playOptions[index]) {
      console.error('播放音频时出错: 无效的音频选项')
      return
    }
    if (videoStore.isPlayingArray[index]) {
      closeAudio()
      videoStore.isPlayingArray[index] = false
    } else {
      closeAudio()
      const musicName = playOptions[index].name
      let requestUrl
      let genre = playOptions[index].genres
      if (musicType === MusicType.BGM) {
        requestUrl = `/api/v1/audio/stream-audio/${encodeURIComponent(
          musicName
        )}?genre=${encodeURIComponent(genre)}`
      }
      const response = await axios.get(requestUrl, {
        responseType: 'blob',
      })
      if (response.status === 200) {
        const blob = response.data
        const audioUrl = URL.createObjectURL(blob)
        playAudio(audioUrl)
      } else {
        console.error('V2版本暂不支持播放')
      }
      videoStore.isPlayingArray.fill(false)
      videoStore.isPlayingArray[index] = true
    }

    videoStore.currentAudio.onended = () => {
      videoStore.isPlayingArray[index] = false
    }
  } catch (error) {
    console.error('播放音频时出错:', error)
  }
}

const playAudio = async (audioUrl) => {
  try {
    videoStore.currentAudio.pause()
    videoStore.currentAudio.currentTime = 0
    videoStore.currentAudio.src = audioUrl
    await videoStore.currentAudio.play()
    videoStore.currentAudio.volume = videoStore.bgmVolume
  } catch (error) {
    console.error('Error playing audio:', error)
  }
}

const filterMusic = () => {
  const query = videoStore.searchQuery
  const genres = videoStore.selectedGenre
  filteredMusic.value = videoStore.allBgms.filter(
    (bgm) =>
      (bgm.label.includes(query) || bgm.artist.includes(query)) && bgm.genres.includes(genres)
  )
}

watch([() => videoStore.selectedGenre, () => videoStore.searchQuery], () => {
  filterMusic()
})

onMounted(async () => {
  if (!videoStore.allBgms) {
    await fetchMusicOptions()
  }
  filterMusic()
})

const fetchMusicOptions = async () => {
  try {
    videoStore.musicDialogVisible = true
    videoStore.loadingBgms = true
    const bgmRetrieveResponse = await api.getBgms()
    const files = bgmRetrieveResponse.data.files
    videoStore.allBgms = files.map((bgm) => ({
      label: bgm.name.replace('.mp3', ''),
      name: bgm.name,
      size: bgm.size,
      duration: bgm.duration,
      genres: bgm.genres,
      image: bgm.image,
      title: bgm.title,
      artist: bgm.artist,
      url: bgm.file,
      waveform: bgm.waveform, // 添加 waveform 数据
    }))
    videoStore.bgmOptions = videoStore.allBgms
    videoStore.isPlayingArray = new Array(videoStore.bgmOptions.length).fill(false)
    videoStore.loadingBgms = false
    filteredMusic.value = videoStore.allBgms
  } catch (error) {
    console.error('Error fetching BGM options:', error)
    videoStore.loadingBgms = false
  }
}

onBeforeUnmount(() => {
  closeAudio()
})
</script>

<style scoped>
.audio-config-container {
  display: flex;
  flex-direction: column;
  padding: 5px;
  background: #1d1d1d;
  color: #ffffff;
  height: 80vh;
  width: 100%;
}

.nav-bar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 10px;
  gap: 10px;
  background: rgba(50, 50, 50, 0.9);
  margin-bottom: 2px;
}

.nav-left {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 30%;
  gap: 1px;
}
.nav-middle {
  display: flex;
  justify-content: flex-start;

  width: 40%;
  align-items: center;
}
.nav-right {
  position: relative;
  display: flex;
  width: 30%;
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
}

.nav-button.selected {
  border: 2px solid #ff3e3e;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
.nav-button:hover {
  box-shadow: 0 4px 8px rgba(243, 173, 173, 0.3);
}
.nav-current-music {
  display: flex;
  justify-content: space-between;
  color: #ff3e3e;
  background: #333;
  cursor: default;

  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.2);
}
.nav-current-music:hover {
  box-shadow: 0 4px 8px rgba(243, 194, 194, 0.3);
}
.selected-music-title {
  width: 250px;
  white-space: nowrap;
  overflow: hidden;

  text-overflow: ellipsis;
}
.search-input {
  display: flex;
  width: 50%;
  background: #f5f0f0;
  color: #ff3e3e;
  border-color: #ff3e3e;
}

.fixed-container {
  display: flex;
  flex-direction: column;
  background: rgba(50, 50, 50, 0.9);
  border-radius: 8px;
  backdrop-filter: blur(10px);
  margin-bottom: 16px;
}

.genre-grid-container {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 5px;
}

.genre-scroll {
  display: flex;
  overflow-x: auto;
  scrollbar-width: none;
  flex-wrap: wrap;
  transition: transform 0.3s ease-in-out;
}

.genre-scroll::-webkit-scrollbar {
  display: none;
}

.genre-item {
  display: flex;
  border-radius: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.3s ease-in-out;
}

.genre-label {
  font-size: 14px;
  font-weight: bold;
  color: #ee8873;
  padding: 5px 10px;
  white-space: nowrap;
  transition: background 0.2s, transform 0.2s, color 0.2s;
}

.genre-label:hover,
.genre-item.selected .genre-label {
  background: #555;
  transform: scale(1.05);
  color: #ff3e3e;
}

.cards-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 60vh;
  overflow-y: auto;
  flex-grow: 1;
}

.audio-card {
  display: flex;
  flex-direction: column;

  padding: 10px;
  border-radius: 8px;
  background: #292929;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.audio-card:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.music-card-content {
  display: flex;
  align-items: center;
  width: 100%;
  margin-bottom: 2px;
}

.music-info-container {
  display: flex;
  align-items: center;
  flex: 1;
}

.music-info {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #ffffff;
}

.music-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 30%;
}

.album-cover {
  width: 60px;
  height: 60px;
  object-fit: cover;
  margin-right: 15px;
  border-radius: 8px;
}

.music-title {
  font-size: 15px;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 250px;
}

.music-duration {
  font-size: 12px;
  color: #aaaaaa;
}
.music-genre {
  font-size: 12px;
  color: #aaaaaa;
}

.music-waveform {
  display: flex;
  align-items: center;
  flex-grow: 1;
  display: flex;
  width: 100%;
  height: auto;
  background: #444;

  position: relative;
}

.control-icon,
.favorite {
  color: #ec5252;
  margin-left: 10px;
}

.genre-item.selected .genre-label {
  background: #d53333;
  color: #e3e0e0;
}
</style>
