import { defineStore } from 'pinia'
import api from '@/api'
import axios from 'axios'
import { MusicType } from '@/config/videoOptions'

export const useVideoStore = defineStore('video', {
  state: () => ({
    videoTheme: '自媒体文案如何生成爆款',
    videoScript: '',
    weiboUrl: '',
    weiboMid: '',
    weiboTitle: '',
    continueScript: '',
    wordCount: 300,
    videoKeywords: [],
    videoTitle: '',
    videoCategory: 'opinion_sharing',
    inspirationKeyword: '', //视频灵感关键词语句
    selectedInspiration: {}, //当前选中视频灵感类型
    scriptLanguage: 'auto-detect',
    videoSource: 'pixabay',
    videoLayout: 'random',
    videoRatio: '16:9',
    videoMaxLength: 10,
    videoCount: 1,
    paragraphNumber: 4,
    enableSubtitles: true,
    enablePlayVoices: true,
    subtitleFont: 'MicrosoftYaHeiBold.ttc',
    subtitlePosition: 'bottom',
    subtitleColor: '#F9F9F8FF',
    subtitleStrokeColor: '#040a52',
    subtitleSize: 65,
    subtitleBorderColor: '#1e1e1b',
    subtitleBackgroundColor: '#39C186FF',
    subtitleOpacity: 1,
    subtitleStrokeWidth: 3,
    selectedVoiceLabel: 'zh-CN-YunxiNeural',
    voiceVolume: 1.0,
    bgmVolume: 0.1,
    bgmType: 'random',
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
    currentAudio: new Audio(),
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

      // 如果有微博参数，更新视频主题和请求体
      // 如果有微博参数，加入请求体
      if (this.weiboUrl && this.weiboUrl.trim() !== '') {
        this.videoTheme = this.weiboTitle
      }

      this.loadingScript = true
      try {
        // 构建请求体
        const requestBody = {
          video_subject: this.videoTheme,
          video_language: this.scriptLanguage,
          video_category: this.videoCategory,
          word_count: this.wordCount,
          paragraph_number: this.paragraphNumber,
          amount: 5,
        }

        // 如果有微博参数，加入请求体
        if (this.weiboUrl && this.weiboUrl.trim() !== '') {
          requestBody.weibo_mid = this.weiboMid
          requestBody.weibo_url = this.weiboUrl
          requestBody.weibo_title = this.weiboTitle
          console.log('如果有微博参数，加入请求体', requestBody)
        }

        // 发起请求
        const scriptResponse = await api.getScriptsTerms(requestBody)
        this.videoScript = scriptResponse.data.video_script
        this.videoKeywords = scriptResponse.data.video_terms
        this.videoTheme = scriptResponse.data.video_title
        this.videoTitle = scriptResponse.data.video_title
      } catch (error) {
        console.error('生成失败', error)
        $message?.error('生成失败，请重试')
        this.loadingScript = false
      } finally {
        this.loadingScript = false
      }
    },
    async handleGenerateScriptByInspire() {
      //
      if (!this.selectedInspiration.value || this.selectedInspiration.value.trim() === '') {
        $message?.error('请先选中灵感才能生成文案哦')
        return
      }
      try {
        // 构建请求体
        this.loadingScript = true
        const requestBody = {
          video_inspire: this.selectedInspiration.value,
          video_inspire_keyword: this.inspirationKeyword,
          word_count: this.wordCount,
          paragraph_number: this.paragraphNumber,
          amount: 5,
        }
        // 发起请求
        const scriptResponse = await api.getScriptsTermsByInspire(requestBody)
        this.videoScript = scriptResponse.data.video_script
        this.videoKeywords = scriptResponse.data.video_terms
        this.videoTheme = scriptResponse.data.video_title
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
      this.videoTitle = ''
    },
    async togglePlayAudio(index, playOptions, musicType) {
      try {
        if (!playOptions || !playOptions[index]) {
          console.error('播放音频时出错: 无效的音频选项')
          return
        }
        if (this.isPlayingArray[index]) {
          this.closeAudio()
          this.isPlayingArray[index] = false
        } else {
          this.closeAudio()
          let requestUrl
          let volume
          if (musicType === MusicType.BGM) {
            volume = this.bgmVolume
            const musicName = playOptions[index].name
            let genre = playOptions[index].genres
            requestUrl = `/api/v1/audio/stream-audio/${encodeURIComponent(
              musicName
            )}?genre=${encodeURIComponent(genre)}`
          } else {
            volume = this.voiceVolume
            const voiceName = playOptions[index].name
            requestUrl = `/api/v1/audio/stream-voice/${encodeURIComponent(voiceName)}`
          }
          const response = await axios.get(requestUrl, {
            responseType: 'blob',
          })
          if (response.status === 200) {
            const blob = response.data
            const audioUrl = URL.createObjectURL(blob)
            await this.playAudio(audioUrl, volume)
          } else {
            console.error('V2版本暂不支持播放')
          }
          this.isPlayingArray.fill(false)
          this.isPlayingArray[index] = true
        }

        this.currentAudio.onended = () => {
          this.isPlayingArray[index] = false
        }
      } catch (error) {
        console.error('播放音频时出错:', error)
      }
    },
    async playAudio(audioUrl, volume) {
      try {
        this.currentAudio.pause()
        this.currentAudio.currentTime = 0
        this.currentAudio.src = audioUrl
        await this.currentAudio.play()
        this.currentAudio.volume = volume
      } catch (error) {
        console.error('Error playing audio:', error)
      }
    },
    adjustVolume(value) {
      if (this.currentAudio) {
        this.currentAudio.volume = value
      }
    },
    closeAudio() {
      this.isPlayingArray = new Array(this.bgmOptions.length).fill(false)
      if (this.currentAudio) {
        this.currentAudio.pause()
        this.currentAudio.currentTime = 0
      }
    },
  },
})
