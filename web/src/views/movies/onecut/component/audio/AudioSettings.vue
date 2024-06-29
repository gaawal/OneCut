<template>
  <div class="audio-config-container">
    <div class="nav-bar">
      <div class="nav-left">
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === AudioNavBarType.ONLINE }"
          @click="selectTab(AudioNavBarType.ONLINE)"
          >在线音乐</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === AudioNavBarType.MYMUSIC }"
          @click="selectTab(AudioNavBarType.MYMUSIC)"
          >我的音乐</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === AudioNavBarType.RECENT }"
          @click="selectTab(AudioNavBarType.RECENT)"
          >最近使用</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === AudioNavBarType.FAVORITES }"
          @click="selectTab(AudioNavBarType.FAVORITES)"
          >收藏</NButton
        >
      </div>
      <div class="nav-middle">
        <div class="nav-current-music">
          <NButton size="small" strong secondary type="error">
            <Icon class="control-icon favorite" size="20">
              <MusicalNotesOutline />
            </Icon>
            <span>已选：</span>
            <span class="selected-music-title">
              {{ videoStore.selectedBgmLabel || '当前无选中音乐' }}</span
            >
          </NButton>
        </div>
      </div>
      <div class="nav-right">
        <NInput
          v-model:value="videoStore.searchQuery"
          placeholder="搜索音频"
          clearable
          size="small"
          class="search-input"
          @input="filterMusic"
        />
        <NIcon size="24" style="margin-left: 5px; cursor: pointer">
          <VolumeMediumOutline />
        </NIcon>
        <NSlider
          v-model:value="videoStore.bgmVolume"
          :min="0.0"
          :max="1.0"
          step="0.1"
          style="width: 100px; margin-left: 8px"
          @update:value="videoStore.adjustVolume"
        />
      </div>
    </div>

    <div class="fixed-container">
      <div class="genre-grid-container">
        <div class="genre-scroll">
          <div
            v-for="genre in genreOptions"
            :key="genre.value"
            class="genre-item"
            :class="{ selected: videoStore.selectedGenre === genre.value }"
            @click="selectGenre(genre.value)"
          >
            <span class="genre-label">{{ genre.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <NForm label-placement="left" label-align="left">
      <keep-alive>
        <component :is="currentComponent" />
      </keep-alive>
    </NForm>
  </div>
</template>

<script setup>
import { useVideoStore } from '@/store'
import { watch, ref, onMounted, onBeforeUnmount } from 'vue'
import api from '@/api'
import { Icon } from '@vicons/utils'
import OnlinesAudio from './pages/OnlinesAudio.vue'
import MyMusic from './pages/MyMusic.vue'
import RecentAudio from './pages/RecentAudio.vue'
import FavoriteAudio from './pages/FavoriteAudio.vue'
import { VolumeMediumOutline, MusicalNotesOutline } from '@vicons/ionicons5'

import { genreOptions } from '@/config/videoOptions'

const videoStore = useVideoStore()
const filteredMusic = ref([])
import { AudioNavBarType } from '@/config/videoOptions'
const selectedTab = ref(AudioNavBarType.ONLINE)

const selectGenre = (genre) => {
  videoStore.selectedGenre = genre
  filterMusic()
}

const filterMusic = () => {
  const query = videoStore.searchQuery
  const genres = videoStore.selectedGenre
  filteredMusic.value = videoStore.allBgms.filter(
    (bgm) =>
      (bgm.label.includes(query) || bgm.artist.includes(query)) && bgm.genres.includes(genres)
  )
}

const selectTab = (tab) => {
  selectedTab.value = tab
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
const currentComponent = computed(() => {
  switch (selectedTab.value) {
    case AudioNavBarType.ONLINE:
      return OnlinesAudio
    case AudioNavBarType.RECENT:
      return MyMusic
    case AudioNavBarType.MYMUSIC:
      return RecentAudio
    case AudioNavBarType.FAVORITES:
      return FavoriteAudio
    default:
      return OnlinesAudio
  }
})
onBeforeUnmount(() => {
  videoStore.closeAudio()
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
