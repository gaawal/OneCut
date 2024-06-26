<template>
  <div class="voice-config-container">
    <div class="nav-bar">
      <div class="nav-left">
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === 'online' }"
          @click="selectTab('online')"
          >热门人声</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === 'myMusic' }"
          @click="selectTab('myMusic')"
          >高级人声</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === 'recent' }"
          @click="selectTab('recent')"
          >最近使用</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === 'favorites' }"
          @click="selectTab('favorites')"
          >克隆音色</NButton
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
              {{ videoStore.selectedVoiceLabel || '当前无选中音色' }}</span
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
          v-model:value="videoStore.voiceVolume"
          :min="0.0"
          :max="3.0"
          step="0.1"
          style="width: 100px; margin-left: 8px"
          @update:value="adjustVolume"
        />
      </div>
    </div>

    <NForm label-placement="left" label-align="left">
      <NSpin v-if="videoStore.loadingVoices"></NSpin>
      <div v-else class="cards-container">
        <NCard
          v-for="(voice, index) in videoStore.voiceOptions"
          :key="voice.label"
          class="voice-card"
          @click="selectVoice(voice)"
        >
          <div class="voice-card-content">
            <div class="voice-info-container">
              <div class="voice-info">
                <Icon
                  v-if="!videoStore.isPlayingArray[index]"
                  size="24"
                  @click.stop="togglePlayAudio(index, videoStore.voiceOptions, MusicType.VOICE)"
                >
                  <MicCircleOutline />
                </Icon>
                <Icon
                  v-else
                  size="24"
                  @click.stop="togglePlayAudio(index, videoStore.voiceOptions, MusicType.VOICE)"
                >
                  <MicCircle />
                </Icon>
                <span v-if="voice.voice" class="voice-title">
                  {{ voiceNames[voice.voice] ? voiceNames[voice.voice] : voice.voice }}
                </span>
                <Icon :style="{ color: voice.gender === 'Male' ? '#3884be' : '#e91e63' }" size="16">
                  <component :is="voice.gender === 'Male' ? Male : Female" />
                </Icon>
                <span class="voice-language">
                  {{ voiceLanguages[voice.language] }} {{ voiceCountry[voice.country] }}
                </span>
              </div>
            </div>
          </div>
        </NCard>
      </div>
    </NForm>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useVideoStore } from '@/store'
import api from '@/api'
import axios from 'axios'
import { Icon } from '@vicons/utils'
import {
  MicCircleOutline,
  MusicalNotesOutline,
  MicCircle,
  Female,
  Male,
  VolumeMediumOutline,
} from '@vicons/ionicons5'
import { voiceNames, voiceLanguages, voiceCountry, MusicType } from '@/config/videoOptions'

const videoStore = useVideoStore()
let currentAudio = new Audio()
const selectedTab = ref('online')

const fetchVoicesOptions = async () => {
  try {
    videoStore.loadingVoices = true
    const { data } = await api.getVoices()
    videoStore.voiceOptions = data.voices.map((voice) => ({
      label: voice.name,
      name: voice.name,
      language: voice.language,
      voice: voice.voice.replace('Neural', ''),
      country: voice.country,
      gender: voice.gender,
      url: voice.url,
    }))
    videoStore.isPlayingArray = new Array(videoStore.voiceOptions.length).fill(false)
    videoStore.loadingVoices = false
  } catch (error) {
    console.error('Error fetching voice options:', error)
    videoStore.loadingVoices = false
  }
}

const closeAudio = () => {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0
  }
}

const selectVoice = (voice) => {
  videoStore.selectedVoiceLabel = voice.label
}

const togglePlayAudio = async (index, playOptions, musicType) => {
  try {
    if (!playOptions || !playOptions[index]) {
      console.error('播放音频时出错: 无效的音频选项')
      return
    }
    if (videoStore.isPlayingArray[index]) {
      videoStore.isPlayingArray[index] = false
    } else {
      const voiceName = playOptions[index].name
      const requestUrl = `/api/v1/audio/stream-voice/${encodeURIComponent(voiceName)}`
      const response = await axios.get(requestUrl, { responseType: 'blob' })
      if (response.status === 200) {
        const blob = response.data
        const audioUrl = URL.createObjectURL(blob)
        await playAudio(audioUrl)
      } else {
        console.error('V2版本暂不支持播放')
      }
      videoStore.isPlayingArray.fill(false)
      videoStore.isPlayingArray[index] = true
    }
    currentAudio.onended = () => {
      videoStore.isPlayingArray[index] = false
    }
  } catch (error) {
    console.error('播放音频时出错:', error)
  }
}

const playAudio = async (audioUrl) => {
  try {
    currentAudio.pause()
    currentAudio.currentTime = 0
    currentAudio.src = audioUrl
    await currentAudio.play()
  } catch (error) {
    console.error('Error playing audio:', error)
  }
}

const adjustVolume = (value) => {
  if (currentAudio) {
    currentAudio.volume = value
  }
}

const selectTab = (tab) => {
  selectedTab.value = tab
}

onMounted(async () => {
  await fetchVoicesOptions()
})
</script>

<style scoped>
.voice-config-container {
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
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: rgba(50, 50, 50, 0.9);
  margin-bottom: 2px;
}

.nav-left {
  display: flex;
  gap: 1px;
}
.nav-middle {
  display: flex;
  align-items: center;
}

.nav-right {
  display: flex;
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
  align-items: center;
  color: #ff3e3e;
  background: #333;
  padding: 5px 10px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.2);
}

.nav-current-music:hover {
  box-shadow: 0 4px 8px rgba(243, 194, 194, 0.3);
}

.selected-music-title {
  width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-input {
  display: flex;
  width: 200px;
  background: #f5f0f0;
  color: #ff3e3e;
  border-color: #ff3e3e;
}

.cards-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  overflow-y: auto;
  padding: 10px;
  flex-grow: 1;
}

.voice-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: calc(33.333% - 10px);
  padding: 10px;
  background: #720d23;
  color: #ffffff;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.voice-card:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.voice-card-content {
  display: flex;
  align-items: center;
}

.voice-info-container {
  display: flex;
  align-items: center;
}

.voice-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.voice-title {
  font-size: 14px;
}

.voice-language {
  font-size: 12px;
  color: #ccc;
}

.control-icon {
  color: #ffb3b3;
}
</style>
