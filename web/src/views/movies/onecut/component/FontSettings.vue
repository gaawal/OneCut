<template>
  <div class="font-config-container">
    <div flex items-center style="color: #e91e63">
      <Icon size="24" style="margin-right: 5px">
        <Text />
      </Icon>
      <h3>字幕</h3>
    </div>
    <NForm label-placement="left" label-align="left" :label-width="videoStore.labelWidth">
      <NFormItem label="启用字幕">
        <NSwitch v-model:value="videoStore.enableSubtitles" />
      </NFormItem>
      <template v-if="videoStore.enableSubtitles">
        <NFormItem label="字幕字体">
          <NInput v-model:value="videoStore.subtitleFont" placeholder="选择字体文件" />
        </NFormItem>
        <NFormItem label="字幕位置">
          <NSelect v-model:value="videoStore.subtitlePosition" :options="subtitlePositionOptions" />
        </NFormItem>
        <NFormItem label="字幕颜色">
          <NColorPicker v-model:value="videoStore.subtitleColor" />
        </NFormItem>
        <NFormItem label="字幕大小">
          <NSlider v-model:value="videoStore.subtitleSize" :min="30" :max="100" />
        </NFormItem>
        <NFormItem label="描边颜色">
          <NColorPicker v-model:value="videoStore.subtitleBorderColor" />
        </NFormItem>
        <NFormItem label="描边粗细">
          <NSlider
            v-model:value="videoStore.subtitleBorderThickness"
            :min="0"
            :max="10"
            step="0.1"
          />
        </NFormItem>
      </template>
    </NForm>
  </div>
</template>

<script setup>
import { useVideoStore } from '@/store'
import { Icon } from '@vicons/utils'
import { Text } from '@vicons/ionicons5'
import { subtitlePositionOptions } from '@/config/videoOptions' //导入视频参数表单选项参数
const videoStore = useVideoStore()
</script>

<style scoped>
.font-config-container {
  margin: 10px;
}
</style>
