import { spawn, type ChildProcess } from 'child_process'
import { randomBytes } from 'crypto'
import { createServer } from 'net'
import { join } from 'path'

export interface BackendRuntimeConfig {
  url: string
  token: string
}

export interface BackendCommand {
  command: string
  args: string[]
  cwd?: string
}

export interface BackendManagerOptions {
  isPackaged: boolean
  resourcesPath: string
  userDataPath: string
  projectRoot: string
  env?: NodeJS.ProcessEnv
  onUnexpectedExit?: (message: string) => void
  readinessTimeoutMs?: number
  commandFactory?: (desktopArgs: string[]) => BackendCommand
}

export function resolveBackendExecutable(
  resourcesPath: string,
  platform: NodeJS.Platform,
): string {
  return join(
    resourcesPath,
    'backend',
    'dss-backend',
    platform === 'win32' ? 'dss-backend.exe' : 'dss-backend',
  )
}

export async function findAvailablePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer()
    server.unref()
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      if (!address || typeof address === 'string') {
        server.close()
        reject(new Error('Could not allocate a local backend port.'))
        return
      }
      server.close(() => resolve(address.port))
    })
  })
}

export class BackendManager {
  private child: ChildProcess | null = null
  private runtimeConfig: BackendRuntimeConfig | null = null
  private stopping = false

  constructor(private readonly options: BackendManagerOptions) {}

  async start(): Promise<BackendRuntimeConfig> {
    const env = this.options.env ?? process.env
    if (!this.options.isPackaged && env.DSS_BACKEND_URL) {
      this.runtimeConfig = {
        url: env.DSS_BACKEND_URL,
        token: env.DSS_API_TOKEN ?? '',
      }
      await this.waitUntilReady(this.runtimeConfig.url, null)
      return this.runtimeConfig
    }

    const port = await findAvailablePort()
    const token = randomBytes(32).toString('hex')
    const dataDirectory = join(this.options.userDataPath, 'data')
    const logFile = join(this.options.userDataPath, 'logs', 'backend.log')
    const database = join(dataDirectory, 'enrollment.sqlite3')
    const commonArgs = [
      '--database',
      database,
      '--port',
      String(port),
      '--token',
      token,
      '--log-file',
      logFile,
    ]

    const command = this.options.isPackaged
      ? resolveBackendExecutable(this.options.resourcesPath, process.platform)
      : 'uv'
    const args = this.options.isPackaged
      ? commonArgs
      : [
          'run',
          '--project',
          join(this.options.projectRoot, 'backend'),
          'python',
          '-m',
          'app.desktop',
          ...commonArgs,
        ]

    const override = this.options.commandFactory?.(commonArgs)
    this.child = spawn(override?.command ?? command, override?.args ?? args, {
      cwd: override?.cwd ?? (this.options.isPackaged
        ? this.options.resourcesPath
        : join(this.options.projectRoot, 'backend')),
      env,
      stdio: 'ignore',
      windowsHide: true,
    })
    this.child.once('error', (error) => {
      if (!this.stopping && this.runtimeConfig) {
        this.options.onUnexpectedExit?.(`Backend failed to start: ${error.message}`)
      }
    })
    this.child.once('exit', (code, signal) => {
      if (!this.stopping && this.runtimeConfig) {
        this.options.onUnexpectedExit?.(
          `Backend stopped unexpectedly (${signal ?? `exit code ${code ?? 'unknown'}`}).`,
        )
      }
    })

    const url = `http://127.0.0.1:${port}`
    await this.waitUntilReady(url, this.child)
    this.runtimeConfig = { url, token }
    return this.runtimeConfig
  }

  getRuntimeConfig(): BackendRuntimeConfig {
    if (!this.runtimeConfig) {
      throw new Error('Backend runtime configuration is not ready.')
    }
    return this.runtimeConfig
  }

  async stop(): Promise<void> {
    const child = this.child
    if (!child || child.exitCode !== null) return

    this.stopping = true
    await new Promise<void>((resolve) => {
      const forceTimer = setTimeout(() => {
        child.kill('SIGKILL')
      }, 5_000)
      child.once('exit', () => {
        clearTimeout(forceTimer)
        resolve()
      })
      child.kill('SIGTERM')
    })
    this.child = null
    this.runtimeConfig = null
  }

  private async waitUntilReady(
    url: string,
    child: ChildProcess | null,
  ): Promise<void> {
    const timeout = this.options.readinessTimeoutMs ?? 30_000
    const deadline = Date.now() + timeout
    while (Date.now() < deadline) {
      if (child?.exitCode !== null && child?.exitCode !== undefined) {
        throw new Error(`Backend exited before becoming ready (${child.exitCode}).`)
      }
      try {
        const response = await fetch(`${url}/health`, {
          signal: AbortSignal.timeout(1_000),
        })
        if (response.ok) return
      } catch {
        // The backend may still be starting or applying migrations.
      }
      await new Promise((resolve) => setTimeout(resolve, 200))
    }
    throw new Error(`Backend did not become ready within ${timeout} milliseconds.`)
  }
}
