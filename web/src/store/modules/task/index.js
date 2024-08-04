import { defineStore } from 'pinia'
import api from '@/api'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    loadingTasks: false,
    taskDetail: null,
    loadingTaskDetail: false,
    taskCreationState: '',
    taskUpdateState: '',
    page: 1,
    total: 100,
    page_size: 50,
  }),
  getters: {
    taskCount: (state) => state.tasks.length,
    completedTasks: (state) => state.tasks.filter((task) => task.state === 'completed'),
  },
  actions: {
    async fetchTasks(page = 1, pageSize = 10) {
      this.loadingTasks = true
      try {
        const response = await api.fetchTasks({
          page,
          page_size: pageSize,
        })
        if (response.code === 200) {
          this.tasks = response.data
          this.page = response.page
          this.total = response.total
          this.page_size = response.page_size
        } else {
          console.error('Failed to fetch tasks:', response.data.msg)
        }
      } catch (error) {
        console.error('Error fetching tasks:', error)
      } finally {
        this.loadingTasks = false
      }
    },
    async fetchTaskDetail(taskId) {
      this.loadingTaskDetail = true
      try {
        const response = await api.fetchTaskDetail({
          task_id: taskId,
        })
        if (response.data.code === 1) {
          this.taskDetail = response.data.data
        } else {
          console.error('Failed to fetch task detail:', response.data.msg)
        }
      } catch (error) {
        console.error('Error fetching task detail:', error)
      } finally {
        this.loadingTaskDetail = false
      }
    },
    async createTask(taskData) {
      try {
        const response = await api.createTask(taskData)
        if (response.data.code === 1) {
          this.taskCreationState = 'success'
          // Optionally, refresh the task list
          this.fetchTasks()
        } else {
          this.taskCreationState = 'failed'
          console.error('Failed to create task:', response.data.msg)
        }
      } catch (error) {
        this.taskCreationState = 'error'
        console.error('Error creating task:', error)
      }
    },
    async updateTask(taskData) {
      try {
        const response = await api.updateTask(taskData)
        if (response.data.code === 1) {
          this.taskUpdateState = 'success'
          // Optionally, refresh the task detail or task list
          this.fetchTaskDetail(taskData.id)
        } else {
          this.taskUpdateState = 'failed'
          console.error('Failed to update task:', response.data.msg)
        }
      } catch (error) {
        this.taskUpdateState = 'error'
        console.error('Error updating task:', error)
      }
    },
    async deleteTask(taskId) {
      try {
        const response = await api.deleteTask({
          task_id: taskId,
        })
        if (response.data.code === 1) {
          this.taskDeletionState = 'success'
          // Optionally, refresh the task list
          this.fetchTasks()
        } else {
          this.taskDeletionState = 'failed'
          console.error('Failed to delete task:', response.data.msg)
        }
      } catch (error) {
        this.taskDeletionState = 'error'
        console.error('Error deleting task:', error)
      }
    },
  },
})
