<template>
  <div class="inspiration-page">
    <div class="navbar">
      <div class="selected-inspiration">
        <NGradientText :size="20" type="danger">
          当前选中的灵感: {{ videoStore.selectedInspiration.name || '无' }}
        </NGradientText>
      </div>
      <div class="inspiration-input">
        <NInput
          v-model:value="videoStore.inspirationKeyword"
          placeholder="请输入灵感来源关键词或者句子"
        />
      </div>
      <div>
        <NButton strong secondary type="success" @click="generateRandomInspiration">
          生成文案
        </NButton>
      </div>
    </div>
    <div class="card-container">
      <div v-for="card in cards" :key="card.value" class="card" @click="selectInspiration(card)">
        <img :src="card.icon" alt="icon" class="card-icon" />
        <div class="card-content">
          <h3 class="card-title">{{ card.name }}</h3>
          <p class="card-subhead">{{ card.subhead }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'
import {
  XiaohongshuIcon,
  ShafaIcon,
  BoyIcon,
  PetIcon,
  BaoxianIcon,
  House,
  Kouhong,
  Tandian,
  Taobao,
  Health,
  History,
  Heal,
  Maikease,
  MaterialSettingsIcon,
  Book,
  ET,
} from '@/config/videoIcons' //导入视频图标
import { useVideoStore } from '@/store'
const videoStore = useVideoStore()

const cards = ref([
  {
    name: '通用文案',
    subhead: '请输入您想要表达的内容',
    category: '自定义',
    weights: 50,
    icon: MaterialSettingsIcon,
    role: 1,
    value: 'generic',
  },
  {
    name: '历史知识',
    subhead: '历史知识类小科普，满足你的好奇心',
    category: '短视频',
    weights: 11,
    icon: History,
    role: 1,
    value: 'historical_knowledge',
  },
  {
    name: '未解之谜',
    subhead: '讲述一个历史上的未解之谜事件，满足你的好奇心',
    category: '短视频',
    weights: 11,
    icon: ET,
    role: 1,
    value: 'unsolved_mystery',
  },
  {
    name: '情感语录',
    subhead: '情感语录类视频脚本，一键get',
    category: '短视频',
    weights: 11,
    icon: Heal,
    role: 1,
    value: 'emotional_quotes',
  },
  {
    name: '麦克阿瑟体',
    subhead: '不是文案想不起，而是麦克阿瑟体更有性价比',
    category: '短视频',
    weights: 11,
    icon: Maikease,
    role: 1,
    value: 'macarthur_style',
  },
  {
    name: '家居短视频脚本',
    subhead: '快速生成家居宣传短视频！',
    category: '短视频',
    weights: 13,
    icon: ShafaIcon,
    role: 1,
    value: 'home_video',
  },
  {
    name: '图书短视频脚本',
    subhead: '与书相伴，是对人生最好的奖励',
    category: '短视频',
    weights: 13,
    icon: Book,
    role: 1,
    value: 'book_video',
  },
  {
    name: '母婴短视频脚本',
    subhead: '为打造母婴爆款提供更多可能',
    category: '短视频',
    weights: 13,
    icon: BoyIcon,
    role: 1,
    value: 'mother_baby',
  },
  {
    name: '宠物类短视频脚本',
    subhead: '针对不同的宠物商品生成卖点信息',
    category: '短视频',
    weights: 13,
    icon: PetIcon,
    role: 1,
    value: 'pet_video',
  },
  {
    name: '保险知识视频脚本',
    subhead: '一键生成保险科普知识脚本文案',
    category: '短视频',
    weights: 12,
    icon: BaoxianIcon,
    role: 1,
    value: 'insurance_knowledge',
  },
  {
    name: '房产短视频脚本',
    subhead: '一键生成房地产类宣传视频脚本',
    category: '短视频',
    weights: 12,
    icon: House,
    role: 1,
    value: 'real_estate_video',
  },
  {
    name: '美妆类视频脚本',
    subhead: '美妆产品类视频脚本，一键get',
    category: '短视频',
    weights: 11,
    icon: Kouhong,
    role: 1,
    value: 'beauty_video',
  },
  {
    name: '探店类视频脚本',
    subhead: '吃喝玩乐探店脚本，一键get！',
    category: '短视频',
    weights: 11,
    icon: Tandian,
    role: 1,
    value: 'store_tour_video',
  },
  {
    name: '小红书种草文案',
    subhead: '结合产品特点，生成种草文案',
    category: '营销',
    weights: 10,
    icon: XiaohongshuIcon,
    role: 1,
    value: 'xiaohongshu_copywriting',
  },
  {
    name: '淘宝逛逛文案',
    subhead: '可根据商品描述生成淘宝逛逛文案',
    category: '营销',
    weights: 10,
    icon: Taobao,
    role: 1,
    value: 'taobao_copywriting',
  },
  {
    name: '健康科普',
    subhead: '敲黑板！靠谱健康知识来了',
    category: '短视频',
    weights: 9,
    icon: Health,
    role: 1,
    value: 'health_knowledge',
  },
])

const selectInspiration = (card) => {
  videoStore.selectedInspiration = card
}

const generateRandomInspiration = async () => {
  let inpireValue
  if (videoStore.selectedInspiration) {
    inpireValue = videoStore.selectedInspiration.value
  } else {
    const randomCard = cards.value[Math.floor(Math.random() * cards.value.length)]
    videoStore.selectedInspiration = randomCard
    inpireValue = randomCard.value
  }
  await generateContent(inpireValue)
  window.close() // 假设这会关闭当前窗口
}

const generateContent = async () => {
  try {
    await videoStore.handleGenerateScriptByInspire()
  } catch (error) {
    console.error('Error generating content:', error)
  }
}
</script>
<style scoped>
.inspiration-page {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  width: 100%;
}
.selected-inspiration {
  display: flex;
  width: 45%;
}
.inspiration-input {
  display: flex;
  width: 40%;
}
.card-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  height: 65vh;
  overflow-y: auto;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #2b2b2b;
  border-radius: 10px;
  padding: 10px;
  margin: 1px;
  width: calc(33% - 10px);
  cursor: pointer;
  transition: transform 0.2s ease-in-out;
}

.card:hover {
  transform: scale(1.05);
}

.card.selected {
  box-shadow: 0 0 15px rgba(76, 175, 80, 0.6); /* 半透明悬浮阴影 */
  background-color: #3b3b3b; /* 选中时稍微加深背景色 */
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin-bottom: 12px;
}
.card-content {
}
.card-title {
  display: flex;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  color: #ffffff;
}

.card-subhead {
  font-size: 12px;
  color: #a9a9a9;
  text-align: center;
}
</style>
