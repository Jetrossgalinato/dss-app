import { app, BrowserWindow, dialog, ipcMain, shell } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'

import { BackendManager } from './backend-manager'

if (process.env.DSS_DISABLE_GPU === '1') {
  app.disableHardwareAcceleration()
  app.commandLine.appendSwitch('disable-gpu')
  app.commandLine.appendSwitch('disable-software-rasterizer')
}

let backendManager: BackendManager | null = null
let quitting = false

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 720,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    const target = new URL(details.url)
    if (target.protocol === 'https:') {
      void shell.openExternal(target.toString())
    }
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

const hasSingleInstanceLock = app.requestSingleInstanceLock()

if (!hasSingleInstanceLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    const window = BrowserWindow.getAllWindows()[0]
    if (window) {
      if (window.isMinimized()) window.restore()
      window.focus()
    }
  })

  app.whenReady().then(async () => {
    electronApp.setAppUserModelId('com.dss.enrollment')

    app.on('browser-window-created', (_, window) => {
      optimizer.watchWindowShortcuts(window)
    })

    backendManager = new BackendManager({
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
      userDataPath: app.getPath('userData'),
      projectRoot: join(app.getAppPath(), '..'),
      onUnexpectedExit: (message) => {
        dialog.showErrorBox('Enrollment DSS backend stopped', message)
        app.quit()
      },
    })

    try {
      await backendManager.start()
      ipcMain.handle('dss:get-backend-config', () =>
        backendManager?.getRuntimeConfig(),
      )
      createWindow()
    } catch (error) {
      await backendManager.stop()
      dialog.showErrorBox(
        'Enrollment DSS could not start',
        error instanceof Error ? error.message : 'Unknown backend startup error.',
      )
      app.quit()
    }

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
  })

  app.on('before-quit', (event) => {
    if (quitting || !backendManager) return
    event.preventDefault()
    quitting = true
    void backendManager.stop().finally(() => app.quit())
  })

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit()
    }
  })
}
