<template>
  <div class="hot-search-container">
    <div class="header">
      <div class="header-left">
        <h3>实时热点新闻</h3>
      </div>
      <div class="header-right">
        <NButton strong secondary size="small" type="success" @click="fetchHotSearches">
          <img :src="RefreshIcon" alt="热" class="hot-icon" />
          <span>点击刷新</span>
        </NButton>
      </div>
    </div>
    <div v-if="loading">
      <NSpace vertical>
        <div v-for="index in 10" :key="index" class="skeleton-item">
          <NSkeleton text style="width: 5%; height: 3vh"></NSkeleton>
          <NSkeleton text style="width: 40%; height: 3vh; margin-left: 5px"></NSkeleton>
          <NSkeleton text style="width: 20%; height: 3vh; margin-left: 5px"></NSkeleton>
          <NSkeleton text style="width: 10%; height: 3vh; margin-left: 5px"></NSkeleton>
          <NSkeleton text style="width: 20%; height: 3vh; margin-left: 5px"></NSkeleton>
        </div>
      </NSpace>
    </div>
    <div v-else class="hot-search-list">
      <div
        v-for="(item, index) in videoStore.hotSearches"
        :key="index"
        class="hot-search-item"
        @click="selectHotSearch(item)"
      >
        <div class="hot-search-rank">{{ index + 1 }}</div>
        <div class="hot-search-content">
          <div class="hot-search-title">
            <span>{{ item.title }}</span>
            <span class="hot-search-hot">{{ item.category }}</span>
            <span class="hot-search-hot">{{ formatHot(item.hot) }}</span>
            <img :src="HotMidIcon" alt="热" class="hot-icon" />
          </div>
          <div class="hot-search-info"></div>
          <div class="hot-search-category"></div>
        </div>
        <div class="buttons">
          <NButton strong secondary size="small" type="primary" @click.stop="generateText(item)">
            <img :src="GenerateTextIcon" alt="热" class="hot-icon" />
            <span style="margin-left: 5px">生成文案</span>
          </NButton>
          <NButton strong secondary size="small" type="primary" @click.stop="searchWeibo(item.url)">
            <img :src="OpenBrowserIcon" alt="查看" class="hot-icon" />
            <span style="margin-left: 5px">查看原文</span>
          </NButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { HotMidIcon, GenerateTextIcon, OpenBrowserIcon, RefreshIcon } from '@/config/videoIcons'
import { useVideoStore } from '@/store'

const videoStore = useVideoStore()
const loading = ref(true)
const selectedHotSearch = ref(null)

const fetchHotSearches = async () => {
  loading.value = true
  try {
    const response = await api.getHotSpot()
    const statusCode = response.code
    if (statusCode === 200) {
      videoStore.hotSearches = response.data
      $message.success('刷新热点新闻成功')
    } else if (statusCode === 400) {
      $message.info(response.data.msg || '请求错误，请检查输入参数')
    } else {
      $message.error(`刷新实时热点新闻失败: ${response.data.msg || '未知错误'}`)
    }
  } catch (error) {
    $message.error(`获取热点新闻失败，请重试。错误信息: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

const selectHotSearch = (item) => {
  selectedHotSearch.value = item
}

const generateText = async (item) => {
  try {
    videoStore.weiboMid = item.mid
    videoStore.weiboTitle = item.title
    videoStore.weiboUrl = item.url
    console.log('generateText,', videoStore.weiboUrl, videoStore.weiboId)
    videoStore.handleGenerateScript()
  } catch (error) {
    console.error('Error generating text:', error)
  }
}

const searchWeibo = (url) => {
  window.open(url, '_blank')
}

const formatHot = (hot) => {
  return (hot / 10000).toFixed(1) + '万'
}

onMounted(() => {
  if (videoStore.hotSearches.length === 0) {
    fetchHotSearches()
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.hot-search-container {
  padding: 16px;
  height: 70vh;
  width: 100%;
  overflow-y: auto;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 16px;
}

.header-left {
  flex: 1;
  text-align: left;
}

.header-right {
  display: flex;
  justify-content: flex-end;
}

.hot-search-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-search-item {
  display: flex;
  align-items: center;
  padding: 0px 10px;
  margin-bottom: 10px;
  cursor: pointer;
}

.hot-search-rank {
  width: 30px;
  margin-right: 3px;
  font-size: 14px;
  font-weight: bold;
  color: #ff4500;
}

.hot-search-content {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  flex-grow: 1;
}

.hot-search-title {
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  width: 500px;
}

.hot-search-title span {
  font-size: 15px;
}

.hot-search-info {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-top: 4px;
}

.hot-search-hot {
  color: #aba7a7;
  font-size: 14px;
  margin-right: 4px;
  margin-left: 5px;
}

.hot-icon {
  margin-left: 2px;
  margin-right: 2px;
  width: 16px;
  height: 16px;
}

.hot-search-category {
  margin-right: 16px;
}

.buttons {
  display: flex;
  gap: 8px;
  width: 10%;
  justify-content: flex-end;
}

.skeleton-item {
  display: flex;
  width: 100%;
  align-items: center;
  height: 5vh;
  border-radius: 4px;
  padding: 5px;
}
</style>
