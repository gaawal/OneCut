import { defineStore } from 'pinia'
import api from '@/api'

export const useVideoStore = defineStore('video', {
  state: () => ({
    videoTheme: '自媒体文案如何生成爆款',
    videoScript: '',
    continueScript: '',
    wordCount: 300,
    videoKeywords: [],
    videoTitle: '',
    videoCategory: 'generic',
    scriptLanguage: 'auto-detect',
    videoSource: 'pixabay',
    videoLayout: 'random',
    videoRatio: '16:9',
    videoMaxLength: 5,
    videoCount: 1,
    enableSubtitles: true,
    enablePlayVoices: true,
    subtitleFont: 'MicrosoftYaHeiBold.ttc',
    subtitlePosition: 'bottom',
    subtitleColor: '#FFD700',
    subtitleSize: 60,
    subtitleBorderColor: '#000000',
    subtitleBorderThickness: 1.5,
    selectedVoiceLabel: 'zh-CN-YunxiNeural',
    voiceVolume: 1.0,
    bgmVolume: 0.2,
    bgmType: 'customize',
    voiceOptions: [],
    bgmOptions: [],
    selectedBgmLabel: '',
    loadingScript: false,
    loadingBgms: false,
    loadingVoices: false,
    loadingKeywords: false,
    labelWidth: 200,
    voiceDialogVisible: false,
    musicDialogVisible: false,
    isPlayingArray: [],
    searchQuery: '',
    selectedGenre: '',
    videoTaskId: '',
    hotSearches: [],
    currentStep: 0,
    taskDetailState: '',
    progressPercentage: '',
    progressState: 'wait',
    showTaskProgressModal: false,
  }),
  getters: {
    wordCountExceeded: (state) => state.videoScript.length > state.wordCount,
  },
  actions: {
    async handleGenerateScript() {
      console.log('handleGenerateScript', this.videoTheme)
      if (!this.videoTheme || this.videoTheme.trim() === '') {
        $message?.error('请填写视频主题')
        return
      }
      this.loadingScript = true
      try {
        const scriptResponse = await api.getScriptsTerms({
          video_subject: this.videoTheme,
          video_language: this.scriptLanguage,
          video_category: this.videoCategory,
          word_count: this.wordCount,
          paragraph_number: 3,
          amount: 5,
        })
        this.videoScript = scriptResponse.data.video_script
        this.videoKeywords = scriptResponse.data.video_terms
        this.videoTitle = scriptResponse.data.video_title
      } catch (error) {
        console.error('生成失败', error)
        $message?.error('生成失败，请重试')
        this.loadingScript = false
      } finally {
        this.loadingScript = false
      }
    },

    async handleAIRefinementSciprt() {
      if (!this.videoScript || this.videoScript.trim() === '') {
        $message?.error('请先生成文案再进行润色哦')
        return
      }
      this.loadingScript = true
      try {
        const scriptResponse = await api.refineScripts({
          origin_script: this.videoScript,
          video_category: this.videoCategory,
          word_count: this.wordCount,
        })
        this.videoScript = scriptResponse.data.video_script
      } catch (error) {
        console.error('生成失败', error)
        $message?.error('生成失败，请重试')
        this.loadingScript = false
      } finally {
        this.loadingScript = false
      }
    },
    async handleAIContinueSciprt() {
      if (!this.videoScript || this.videoScript.trim() === '') {
        $message?.error('请先生成文案再进行续写')
        return
      }
      this.loadingScript = true
      try {
        const scriptResponse = await api.continueScripts({
          origin_script: this.videoScript,
          video_category: this.videoCategory,
          word_count: this.wordCount,
        })
        this.continueScript = scriptResponse.data.video_script
        this.videoScript += this.continueScript
      } catch (error) {
        console.error('生成失败', error)
        $message?.error('生成失败，请重试')
        this.loadingScript = false
      } finally {
        this.loadingScript = false
      }
    },
    handleResetScript() {
      this.videoTheme = ''
      this.videoScript = ''
      this.videoKeywords = []
    },
  },
})
