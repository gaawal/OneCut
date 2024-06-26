<template>
  <div class="material-config-container">
    <div flex items-center style="color: #e91e63">
      <Icon size="24" style="margin-right: 5px">
        <Film />
      </Icon>
      <h3>素材设置</h3>
    </div>
    <NForm label-placement="left" label-align="left" :label-width="videoStore.labelWidth">
      <NFormItem label="素材来源">
        <NSelect v-model:value="videoStore.videoSource" :options="videoSourceOptions" />
      </NFormItem>
      <NFormItem label="拼接方式">
        <NSelect v-model:value="videoStore.videoLayout" :options="videoLayoutOptions" />
      </NFormItem>
      <NFormItem label="画面比例">
        <NSelect v-model:value="videoStore.videoRatio" :options="videoRatioOptions" />
      </NFormItem>
      <NFormItem label="素材最大时长(秒)">
        <NInputNumber v-model:value="videoStore.videoMaxLength" :min="1" />
      </NFormItem>
      <NFormItem label="生成视频数量">
        <NInputNumber v-model:value="videoStore.videoCount" :min="1" />
      </NFormItem>
    </NForm>
  </div>
</template>

<script setup>
import { Icon } from '@vicons/utils'
import { useVideoStore } from '@/store'
import { Film } from '@vicons/ionicons5'

const videoStore = useVideoStore()

import { videoSourceOptions, videoLayoutOptions, videoRatioOptions } from '@/config/videoOptions' //导入视频参数表单选项参数
</script>

<style scoped>
.material-config-container {
  margin: 10px;
}
</style>
