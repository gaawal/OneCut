import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/access_token', data, { noNeedToken: true }),
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // llm
  getScripts: (data = {}) => request.post('/llm/scripts', data),
  getScriptsTerms: (data = {}) => request.post('/llm/scripts_terms', data),
  getScriptsTermsByInspire: (data = {}) => request.post('/llm/inspire_scripts_terms', data),
  refineScripts: (data = {}) => request.post('/llm/refine-scripts', data),
  continueScripts: (data = {}) => request.post('/llm/continue-scripts', data),
  getHotSpot: (params = {}) => request.get('/llm/hot-spot', { params }),
  getTerms: (data = {}) => request.post('/llm/terms', data),
  //audio
  getBgms: (params = {}) => request.get('/audio/bgms', { params }),
  getBgmMusicUrl: (filePath) => request.get(`/audio/bgmUrl/${encodeURIComponent(filePath)}`),
  uploadBgmMusics: (data = {}) => request.post('/audio/uploadBgm', data),
  playStreamMusic: (filePath) =>
    request.get(`/audio/stream-audio/${encodeURIComponent(filePath)}`, { responseType: 'blob' }),
  // voices
  getVoices: (params = {}) => request.get('/audio/voices', { params }),
  // videos
  createVideos: (params = {}) => request.post('/video/createVideos', params),
  getVideoTask: (taskId) => request.get(`/video/tasks/${encodeURIComponent(taskId)}`),
}
