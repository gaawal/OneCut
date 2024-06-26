<script setup>
import { ref, onMounted } from 'vue'

const works = ref([])

const fetchData = async () => {
  // Mock data based on the provided structure
  const mockData = {
    code: 1,
    msg: 'SUCCESS',
    data: {
      page: 1,
      limit: 20,
      count: 2,
      cursor: 0,
      total: 2,
      list: [
        {
          auditStatus: 2,
          downloadPic: '/thumbnail/demo.png',
          downloadUrl:
            'https://bin-trans.miaopai.com/stream/fUZnKfw3XjdYbiCDLtOrqWbNMpyAdJLVtx7dCg__.mp4?ssig=ba31f88f4fe57fd3e281aa8fc0ee089c&time_stamp=1718978646623&filename=【丝绸之路】.mp4',
          duration: 142360,
          fileSize: '54.99MB',
          height: 1080,
          levelTag: 0,
          mediaId: '7208478320911810560',
          nickname: '豁达大度的霸王龙GRZV',
          onlineStatus: 0,
          picture: '/thumbnail/demo.png',
          productId: '162126464120470840',
          shareUrl: 'https://h5.yizhentv.com/video-page.html?sid=HOf2K-WHRe4bDIEx-0KoiMtOSK2IuL7F',
          showCreateUrl: 0,
          status: 9,
          title: '【丝绸之路】',
          uid: '1243221032477718548',
          uniqueIndexId: 1,
          updateTime: '2024-06-17 22:43:17',
          url: 'https://alicdnliz.miaopai.com/stream/fUZnKfw3XjdYbiCDLtOrqWbNMpyAdJLVtx7dCg__.mp4?ssig=ba31f88f4fe57fd3e281aa8fc0ee089c&time_stamp=1718978646623',
          version: 1,
          videoDownloadSize: 0,
          videoType: 0,
          width: 1920,
          workId: '102126506135960881',
        },
        {
          auditStatus: 3,
          downloadPic: '/thumbnail/demo.png',
          downloadUrl:
            'https://bin-trans.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623&filename=广州一宝马冲撞人群_致多人受伤5死13伤这绝对是故意杀人_不过用的工具是车罢.mp4',
          duration: 37000,
          fileSize: '9.03MB',
          height: 1080,
          levelTag: 0,
          mediaId: '7018923473452728320',
          nickname: '豁达大度的霸王龙GRZV',
          onlineStatus: 0,
          picture: '/thumbnail/demo.png',
          productId: '16645914991689856',
          shareUrl: '',
          showCreateUrl: 0,
          status: 9,
          title: '广州一宝马冲撞人群 致多人受伤#5死13伤！这绝对是故意杀人，不过用的工具是车罢',
          uid: '1243221032477718548',
          uniqueIndexId: 2,
          updateTime: '2023-01-11 20:57:06',
          url: 'https://alicdnliz.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623',
          version: 1,
          videoDownloadSize: 0,
          videoType: 0,
          width: 1920,
          workId: '10645911348478048',
        },
        {
          auditStatus: 3,
          downloadPic: '/thumbnail/demo.png',
          downloadUrl:
            'https://bin-trans.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623&filename=广州一宝马冲撞人群_致多人受伤5死13伤这绝对是故意杀人_不过用的工具是车罢.mp4',
          duration: 37000,
          fileSize: '9.03MB',
          height: 1080,
          levelTag: 0,
          mediaId: '7018923473452728320',
          nickname: '豁达大度的霸王龙GRZV',
          onlineStatus: 0,
          picture: '/thumbnail/demo.png',
          productId: '16645914991689856',
          shareUrl: '',
          showCreateUrl: 0,
          status: 9,
          title: '广州一宝马冲撞人群 致多人受伤#5死13伤！这绝对是故意杀人，不过用的工具是车罢',
          uid: '1243221032477718548',
          uniqueIndexId: 2,
          updateTime: '2023-01-11 20:57:06',
          url: 'https://alicdnliz.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623',
          version: 1,
          videoDownloadSize: 0,
          videoType: 0,
          width: 1920,
          workId: '10645911348478048',
        },
        {
          auditStatus: 3,
          downloadPic: '/thumbnail/demo.png',
          downloadUrl:
            'https://bin-trans.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623&filename=广州一宝马冲撞人群_致多人受伤5死13伤这绝对是故意杀人_不过用的工具是车罢.mp4',
          duration: 37000,
          fileSize: '9.03MB',
          height: 1080,
          levelTag: 0,
          mediaId: '7018923473452728320',
          nickname: '豁达大度的霸王龙GRZV',
          onlineStatus: 0,
          picture: '/thumbnail/demo.png',
          productId: '16645914991689856',
          shareUrl: '',
          showCreateUrl: 0,
          status: 9,
          title: '广州一宝马冲撞人群 致多人受伤#5死13伤！这绝对是故意杀人，不过用的工具是车罢',
          uid: '1243221032477718548',
          uniqueIndexId: 2,
          updateTime: '2023-01-11 20:57:06',
          url: 'https://alicdnliz.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623',
          version: 1,
          videoDownloadSize: 0,
          videoType: 0,
          width: 1920,
          workId: '10645911348478048',
        },
        {
          auditStatus: 3,
          downloadPic: '/thumbnail/demo.png',
          downloadUrl:
            'https://bin-trans.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623&filename=广州一宝马冲撞人群_致多人受伤5死13伤这绝对是故意杀人_不过用的工具是车罢.mp4',
          duration: 37000,
          fileSize: '9.03MB',
          height: 1080,
          levelTag: 0,
          mediaId: '7018923473452728320',
          nickname: '豁达大度的霸王龙GRZV',
          onlineStatus: 0,
          picture: '/thumbnail/demo.png',
          productId: '16645914991689856',
          shareUrl: '',
          showCreateUrl: 0,
          status: 9,
          title: '广州一宝马冲撞人群 致多人受伤#5死13伤！这绝对是故意杀人，不过用的工具是车罢',
          uid: '1243221032477718548',
          uniqueIndexId: 2,
          updateTime: '2023-01-11 20:57:06',
          url: 'https://alicdnliz.miaopai.com/stream/vPkZUp2X78gVYhSEDN1pHRaDD2gNPYHMs1oSNw__.mp4?ssig=6275c7a8fa046cd4b7750b137f721150&time_stamp=1718978646623',
          version: 1,
          videoDownloadSize: 0,
          videoType: 0,
          width: 1920,
          workId: '10645911348478048',
        },
      ],
      hasMore: 0,
    },
  }

  works.value = mockData.data.list
}

const createNewProject = () => {
  console.log('Create new project clicked')
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${
    date.getMonth() + 1
  }-${date.getDate()} ${date.getHours()}:${date.getMinutes()}:${date.getSeconds()}`
}

const formatDuration = (ms) => {
  const minutes = Math.floor(ms / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`
}

onMounted(fetchData)
</script>
<template>
  <NCard style="height: 100%">
    <div class="works-container">
      <div class="works-create-button">
        <NButton type="primary" @click="createNewProject">创建项目</NButton>
      </div>
      <div class="work-list">
        <NCard v-for="item in works" :key="item.workId" :hoverable="false" class="work-item">
          <div class="work-image-container">
            <img :src="item.downloadPic" class="work-image" />
            <div class="work-info-overlay">
              <span>{{ item.fileSize }}</span>
              <span>{{ formatDuration(item.duration) }}</span>
            </div>
          </div>
          <div class="work-details">
            <div class="work-title">{{ item.title }}</div>
            <div class="work-info">
              <span>生成时间：</span>
              <span>{{ item.updateTime }}</span>
            </div>
          </div>
        </NCard>
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.works-container {
  padding: 10px;
}

.works-create-button {
  margin-bottom: 10px;
  padding: 10px;
}

.work-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.work-item {
  max-width: 24%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.work-image-container {
  position: relative;
  width: 100%;
  height: auto;
}

.work-image {
  width: 100%;
  height: auto;
}

.work-info-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  color: rgba(255, 255, 255, 0.88);
  padding: 5px;
  font-size: 12px;
  display: flex;
  justify-content: space-between;
}

.work-details {
  display: flex;
  flex-direction: column;
}

.work-title {
  font-size: 14px;
  font-weight: bold;
  height: 70px; /* 固定高度 */
  max-height: 65px;
  width: 100%;
  overflow: auto; /* 超出部分隐藏 */
}

.work-info {
  font-size: 12px;
  color: #666;
}
</style>
