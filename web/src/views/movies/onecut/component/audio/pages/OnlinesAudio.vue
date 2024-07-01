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
            @click.stop="videoStore.togglePlayAudio(index, filteredMusic, MusicType.BGM)"
          >
            <PlayCircleSharp />
          </Icon>
          <Icon
            v-else
            class="control-icon"
            size="24"
            @click.stop="videoStore.togglePlayAudio(index, filteredMusic, MusicType.BGM)"
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
import { Icon } from '@vicons/utils'
import { PlayCircleSharp, PauseCircle, HeartOutline } from '@vicons/ionicons5'
import { MusicType } from '@/config/videoOptions'
import WaveformCanvas from './WaveformCanvas.vue'

const videoStore = useVideoStore()
const filteredMusic = ref([])

const selectMusic = (music) => {
  videoStore.selectedBgmLabel = music.label
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
  videoStore.closeAudio()
})
</script>

<style scoped>
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
