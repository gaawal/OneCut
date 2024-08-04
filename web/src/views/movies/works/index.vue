<template>
  <NCard>
    <NSpace vertical size="large">
      <NSpace justify="space-between" style="margin-bottom: 16px">
        <div>
          <NButton type="success" @click="handleBatchPublish">批量发布</NButton>
          <NButton type="error" style="margin-left: 8px" @click="handleBatchDelete"
            >批量删除</NButton
          >
        </div>
        <div>
          <NInput v-model="searchQuery" placeholder="搜索任务" @input="handleSearch" />
        </div>
      </NSpace>
      <div style="max-height: 75vh; overflow: auto">
        <NDataTable
          :columns="columns"
          :data="filteredTasks"
          :pagination="false"
          :row-key="rowKey"
          :checked-row-keys="checkedRowKeys"
          size="medium"
          bordered
          :max-height="550"
          :min-height="550"
          @filter-change="handleFilterChange"
          @update:checked-row-keys="handleCheck"
        />
      </div>
      <NSpace justify="center">
        <NPagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="[10, 20, 30, 50]"
          show-size-picker
          show-quick-jumper
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </NSpace>
    </NSpace>
  </NCard>

  <NModal v-model:show="publishModalVisible" title="发布视频任务">
    <div>
      <NSelect
        v-model="selectedPlatform"
        :options="platformOptions"
        placeholder="选择发布平台"
        style="width: 100%"
      />
      <NSelect
        v-model="selectedAccount"
        :options="accountOptions"
        placeholder="选择发布账号"
        style="width: 100%; margin-top: 10px"
      />
    </div>
    <template #footer>
      <NButton @click="publishModalVisible = false">取消</NButton>
      <NButton type="primary" @click="confirmPublish">发布</NButton>
    </template>
  </NModal>

  <NModal
    v-model:show="videoModalVisible"
    title="播放视频"
    :mask-closable="false"
    :style="{ width: '700px', height: '500px' }"
  >
    <template #header>
      <h3>播放视频</h3>
      <NButton text @click="videoModalVisible = false">关闭</NButton>
    </template>
    <video
      ref="videoPlayer"
      :src="videoUrl"
      controls
      autoplay
      style="width: 100%; height: 100%"
    ></video>
  </NModal>
</template>

<script setup>
import { ref, onMounted, h, watch, computed } from 'vue'
import {
  NProgress,
  NTag,
  NButton,
  NImage,
  NModal,
  NCard,
  NSpace,
  NPagination,
  NInput,
  NSelect,
  NDataTable,
  useMessage,
  NPopover,
} from 'naive-ui'
import axios from 'axios'
import api from '@/api'
import { getToken } from '@/utils'
import { PlayIcon, Weixin, Douyin, BiliBili, XiaohongshuIcon } from '@/config/videoIcons'
import { useTaskStore } from '@/store'

const taskStore = useTaskStore()
const pagination = ref({
  pageSize: taskStore.page_size,
  page: taskStore.page,
  itemCount: taskStore.total,
  showSizePicker: true,
  pageSizes: [10, 20, 30, 50],
})

const publishModalVisible = ref(false)
const videoModalVisible = ref(false)
const videoUrl = ref('')
const checkedRowKeys = ref([])

const searchQuery = ref('')
const sortOrder = ref('asc')
const taskStatusFilter = ref('')
const publishStatusFilter = ref('')

const rowKey = (row) => row.task_id

const handleCheck = (rowKeys) => {
  checkedRowKeys.value = rowKeys
}

const message = useMessage()

const selectedPlatform = ref(null)
const selectedAccount = ref(null)
const platformOptions = ref([
  { label: '抖音', value: 'douyin' },
  { label: '视频号', value: 'wechat' },
])
const accountOptions = ref([
  { label: '账号1', value: 'account1' },
  { label: '账号2', value: 'account2' },
])

const confirmPublish = async () => {
  if (checkedRowKeys.value.length === 0) {
    message.error('请先选择要发布的任务')
    return
  }
  try {
    const response = await axios.post('/api/v1/tasks/publish', {
      task_ids: checkedRowKeys.value,
      platform: selectedPlatform.value,
      account: selectedAccount.value,
    })
    if (response.data.code === 200) {
      message.success('发布成功')
      fetchTasks(pagination.value.page, pagination.value.pageSize)
    } else {
      message.error('发布失败')
    }
  } catch (error) {
    message.error('发布失败')
  }
  publishModalVisible.value = false
}

const fetchCoverImage = async (taskId) => {
  try {
    const response = await axios.get(`/api/v1/image/stream-coverimg`, {
      headers: { token: getToken() },
      params: { task_id: taskId },
      responseType: 'blob',
    })
    return URL.createObjectURL(response.data)
  } catch (error) {
    console.error('Error fetching cover image:', error)
    return ''
  }
}

const fetchVideo = async (taskId) => {
  try {
    const response = await axios.get(`/api/v1/video/stream-video`, {
      headers: { token: getToken() },
      params: { task_id: taskId },
      responseType: 'blob',
    })
    videoUrl.value = URL.createObjectURL(response.data)
    videoModalVisible.value = true
  } catch (error) {
    console.error('Error fetching video:', error)
    message.error('视频资源已过期清理')
  }
}

const playVideo = async (taskId) => {
  await fetchVideo(taskId)
}

const stateColorMap = {
  error: 'error',
  finish: 'success',
  wait: 'warning',
  processing: 'info',
  wait_publish: 'warning',
  publishing: 'info',
  publish_ok: 'success',
  publish_failed: 'error',
}

const stateTextMap = {
  error: '错误',
  finish: '完成',
  wait: '等待',
  processing: '处理中',
  wait_publish: '待发布',
  publishing: '发布中',
  publish_ok: '发布成功',
  publish_failed: '发布失败',
}

const detailStateColorMap = {
  failed: 'error',
  success: 'success',
  generating_script: 'info',
  script_generation_complete: 'success',
  generating_audio: 'info',
  audio_generation_complete: 'success',
  generating_subtitle: 'info',
  subtitle_generation_complete: 'success',
  downloading_videos: 'info',
  video_download_complete: 'success',
  combining_videos: 'info',
  combined_videos_complete: 'success',
  generating_final_video: 'info',
  final_video_generation_complete: 'success',
  loading_draft: 'info',
  publish_ok: 'success',
  publish_failed: 'error',
  publishing: 'info',
}

const detailStateTextMap = {
  failed: '失败',
  success: '成功',
  generating_script: '生成脚本中',
  script_generation_complete: '脚本生成完成',
  generating_audio: '生成音频中',
  audio_generation_complete: '音频生成完成',
  generating_subtitle: '生成字幕中',
  subtitle_generation_complete: '字幕生成完成',
  downloading_videos: '下载视频中',
  video_download_complete: '视频下载完成',
  combining_videos: '合并视频中',
  combined_videos_complete: '视频合并完成',
  generating_final_video: '生成最终视频中',
  final_video_generation_complete: '最终视频生成完成',
  loading_draft: '加载草稿中',
  publish_ok: '发布成功',
  publish_failed: '发布失败',
  publishing: '发布中',
}

const platformTextMap = {
  douyin: '抖音',
  wechat: '视频号',
}

const createColumns = () => [
  {
    type: 'selection',
    disabled(row) {
      return row.task_id === ''
    },
  },
  {
    title: '封面',
    key: 'cover',
    render(row) {
      return h(
        'div',
        {
          style: {
            position: 'relative',
            width: '100%',
            paddingTop: '56.25%', // 16:9 aspect ratio
            overflow: 'hidden',
            cursor: 'pointer',
          },
          onMouseenter: () => {
            row.showPlayButton = true
          },
          onMouseleave: () => {
            row.showPlayButton = false
          },
          onClick: () => playVideo(row.task_id),
        },
        [
          h(NImage, {
            src: row.coverUrl,
            style: {
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            },
          }),
          row.showPlayButton
            ? h('img', {
                src: PlayIcon,
                style: {
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '40px',
                  height: '40px',
                },
              })
            : null,
        ]
      )
    },
  },
  {
    title: '视频标题',
    key: 'title',
    render(row) {
      return row.draft_content.script_info.video_title
    },
  },
  {
    title: '时长',
    key: 'duration',
    width: 80,
    render(row) {
      return `${row.draft_content.materials.audios[0]?.duration || 0} 秒`
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    sorter: 'default',
    sortOrder: sortOrder.value,
    width: 180,
    filter: {
      options: [
        { label: '升序', value: 'asc' },
        { label: '降序', value: 'desc' },
      ],
      filter(value, row) {
        sortOrder.value = value
        return row
      },
    },
  },
  {
    title: '任务状态',
    key: 'state',
    filter: {
      options: Object.keys(stateTextMap).map((key) => ({
        label: stateTextMap[key],
        value: key,
      })),
      filter(value, row) {
        return row.state === value
      },
    },
    render(row) {
      const type = stateColorMap[row.state] || 'default'
      const text = stateTextMap[row.state] || row.state
      return h(NTag, { type }, { default: () => text })
    },
  },
  {
    title: '任务详细状态',
    key: 'detail_state',
    render(row) {
      const type = detailStateColorMap[row.detail_state] || 'default'
      const text = detailStateTextMap[row.detail_state] || row.detail_state
      return h(NTag, { type }, { default: () => text })
    },
  },
  {
    title: '进度',
    key: 'progress',
    render(row) {
      const status = row.progress === 100 ? 'success' : row.state === 'error' ? 'error' : 'info'
      return h(
        NProgress,
        {
          type: 'line',
          status,
          percentage: row.progress,
          indicatorPlacement: 'inside',
          height: 24,
          borderRadius: '12px 12px 0 0',
          fillBorderRadius: '12px 0 12px 12px',
          style: { width: '120px' },
        },
        {
          default: () => `${row.progress}%`,
        }
      )
    },
  },
  {
    title: '发布平台',
    key: 'platform_status',
    filter: {
      options: [
        { label: '抖音', value: 'douyin' },
        { label: '视频号', value: 'wechat' },
      ],
      filter(value, row) {
        return Object.keys(row.platform_status).includes(value)
      },
    },
    render(row) {
      if (!row.platform_status) {
        return h(
          NButton,
          { onClick: () => openPublishModal([row.task_id]) },
          { default: () => '发布' }
        )
      }
      return Object.keys(row.platform_status).map((platform) =>
        h(
          'img',
          {
            src: platform === 'douyin' ? Douyin : Weixin,
            alt: platformTextMap[platform] || platform,
            style: { width: '20px', height: '20px', marginRight: '8px' },
          },
          { default: () => platformTextMap[platform] || platform }
        )
      )
    },
  },
  {
    title: '操作',
    key: 'operation',
    render(row) {
      return h('div', {}, [
        row.progress === 100 && !row.platform_status
          ? h(NButton, { type: 'primary', onClick: () => openPublishModal([row.task_id]) }, '发布')
          : null,
        row.state === 'error'
          ? h(NButton, { type: 'error', onClick: () => handleDelete(row) }, '删除')
          : null,
      ])
    },
  },
]

const columns = createColumns()

const fetchTasks = async (page = 1, pageSize = 10, search = {}, order = []) => {
  const payload = {
    page,
    page_size: pageSize,
    search,
    order,
  }

  const response = await api.fetchTasks(payload)
  const { data, total } = response
  taskStore.tasks = await Promise.all(
    data.map(async (task) => {
      task.coverUrl = await fetchCoverImage(task.task_id)
      return task
    })
  )
  taskStore.total = total
}

const handlePageChange = (page) => {
  fetchTasks(page, pagination.value.pageSize)
}

const handlePageSizeChange = (pageSize) => {
  fetchTasks(pagination.value.page, pageSize)
}

const handleBatchPublish = async () => {
  if (checkedRowKeys.value.length === 0) {
    message.error('请先选择要发布的任务')
    return
  }
  openPublishModal(checkedRowKeys.value)
}

const handleBatchDelete = async () => {
  if (checkedRowKeys.value.length === 0) {
    message.error('请先选择要删除的任务')
    return
  }
  try {
    const response = await axios.post('/api/v1/tasks/batch-delete', {
      task_ids: checkedRowKeys.value,
    })
    if (response.data.code === 200) {
      message.success('批量删除成功')
      fetchTasks(pagination.value.page, pagination.value.pageSize)
    } else {
      message.error('批量删除失败')
    }
  } catch (error) {
    message.error('批量删除失败')
  }
}

const openPublishModal = (taskIds) => {
  checkedRowKeys.value = taskIds
  publishModalVisible.value = true
}

const handleDelete = async (row) => {
  const response = await axios.post('/api/v1/tasks/delete', {
    task_ids: [row.task_id],
  })
  if (response.data.code === 200) {
    message.success('删除成功')
    fetchTasks(pagination.value.page, pagination.value.pageSize)
  } else {
    message.error('删除失败')
  }
}

const handleSort = (order) => {
  sortOrder.value = order
  fetchTasks(pagination.value.page, pagination.value.pageSize, {}, [
    `${order === 'asc' ? '' : '-'}created_at`,
  ])
}

const handleFilterChange = (filters) => {
  const search = {}
  if (searchQuery.value) search.query = searchQuery.value
  if (filters.state && filters.state.length) search.taskStatus = filters.state[0]
  if (filters.platform_status && filters.platform_status.length)
    search.publishStatus = filters.platform_status[0]

  fetchTasks(pagination.value.page, pagination.value.pageSize, search)
}

const handleSearch = () => {
  const search = {}
  if (searchQuery.value) search.query = searchQuery.value
  if (taskStatusFilter.value) search.taskStatus = taskStatusFilter.value
  if (publishStatusFilter.value) search.publishStatus = publishStatusFilter.value

  fetchTasks(pagination.value.page, pagination.value.pageSize, search)
}

const filteredTasks = computed(() => {
  if (!searchQuery.value) {
    return taskStore.tasks
  }
  return taskStore.tasks.filter((task) =>
    task.draft_content.script_info.video_title.includes(searchQuery.value)
  )
})

watch(
  () => taskStore.total,
  (newTotal) => {
    pagination.value.itemCount = newTotal
  }
)

watch(
  () => taskStore.page_size,
  (newPageSize) => {
    pagination.value.pageSize = newPageSize
  }
)

watch(
  () => taskStore.page,
  (newPage) => {
    pagination.value.page = newPage
  }
)

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
/* Add your styles here if needed */
</style>
