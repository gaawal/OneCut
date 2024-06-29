<template>
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
              @click.stop="
                videoStore.togglePlayAudio(index, videoStore.voiceOptions, MusicType.VOICE)
              "
            >
              <MicCircleOutline />
            </Icon>
            <Icon
              v-else
              size="24"
              @click.stop="
                videoStore.togglePlayAudio(index, videoStore.voiceOptions, MusicType.VOICE)
              "
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
</template>

<script setup>
import { onMounted } from 'vue'
import { useVideoStore } from '@/store'
import api from '@/api'
import { Icon } from '@vicons/utils'
import { MicCircleOutline, MicCircle, Female, Male } from '@vicons/ionicons5'
import { voiceNames, voiceLanguages, voiceCountry, MusicType } from '@/config/videoOptions'

const videoStore = useVideoStore()

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

const selectVoice = (voice) => {
  videoStore.selectedVoiceLabel = voice.label
}

onMounted(async () => {
  await fetchVoicesOptions()
})
</script>

<style scoped>
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
  border-radius: 8px;
  background: #292929;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  color: #ffffff;
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
</style>
