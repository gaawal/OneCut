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
          :class="{ selected: selectedTab === VoiceNavBarType.ONLINE }"
          @click="selectTab(VoiceNavBarType.ONLINE)"
          >热门人声</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === VoiceNavBarType.VIP }"
          @click="selectTab(VoiceNavBarType.VIP)"
          >高级人声</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === VoiceNavBarType.RECENT }"
          @click="selectTab(VoiceNavBarType.RECENT)"
          >最近使用</NButton
        >
        <NButton
          size="small"
          strong
          secondary
          type="error"
          class="nav-button"
          :class="{ selected: selectedTab === VoiceNavBarType.CLONE }"
          @click="selectTab(VoiceNavBarType.CLONE)"
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
      <keep-alive>
        <component :is="currentComponent" />
      </keep-alive>
    </NForm>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useVideoStore } from '@/store'

import { Icon } from '@vicons/utils'
import { MusicalNotesOutline, VolumeMediumOutline } from '@vicons/ionicons5'
import { VoiceNavBarType } from '@/config/videoOptions'
import OnlineVoices from './pages/OnlineVoices.vue'
import VipVoices from './pages/VipVoices.vue'
import RecentVoices from './pages/RecentVoices.vue'
import CloneVoices from './pages/CloneVoices.vue'

const videoStore = useVideoStore()

const selectedTab = ref(VoiceNavBarType.ONLINE)

const adjustVolume = (value) => {
  if (videoStore.currentAudio) {
    videoStore.currentAudio.volume = value
  }
}

const selectTab = (tab) => {
  console.log(tab)
  selectedTab.value = tab
}

const currentComponent = computed(() => {
  switch (selectedTab.value) {
    case VoiceNavBarType.ONLINE:
      return OnlineVoices
    case VoiceNavBarType.VIP:
      return VipVoices
    case VoiceNavBarType.RECENT:
      return RecentVoices
    case VoiceNavBarType.CLONE:
      return CloneVoices
    default:
      return OnlineVoices
  }
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
.control-icon {
  color: #ffb3b3;
}
</style>
