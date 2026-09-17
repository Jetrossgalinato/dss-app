import { createServer } from 'node:net'
import { createServer as createHttpServer } from 'node:http'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

import {
  BackendManager,
  findAvailablePort,
  resolveBackendExecutable,
} from './backend-manager'

function options(overrides: Record<string, unknown> = {}) {
  return {
    isPackaged: false,
    resourcesPath: '/resources',
    userDataPath: '/tmp/dss-test',
    projectRoot: '/project',
    readinessTimeoutMs: 2_000,
    ...overrides,
  }
}

const healthyServerScript = `
  const http = require('node:http')
  const port = Number(process.argv[process.argv.indexOf('--port') + 1])
  http.createServer((request, response) => {
    response.writeHead(200, {'Content-Type': 'application/json'})
    response.end(JSON.stringify({status: 'ok', database: 'ready'}))
  }).listen(port, '127.0.0.1')
`

describe('BackendManager', () => {
  it('resolves platform-specific packaged executables', () => {
    expect(resolveBackendExecutable('/resources', 'win32')).toBe(
      join('/resources', 'backend', 'dss-backend', 'dss-backend.exe'),
    )
    expect(resolveBackendExecutable('/resources', 'linux')).toBe(
      join('/resources', 'backend', 'dss-backend', 'dss-backend'),
    )
  })

  it('allocates an available loopback port', async () => {
    const port = await findAvailablePort()
    const server = createServer()
    await new Promise<void>((resolve) => server.listen(port, '127.0.0.1', resolve))
    await new Promise<void>((resolve) => server.close(() => resolve()))
  })

  it('uses and verifies an explicitly configured development backend', async () => {
    const server = createHttpServer((_request, response) => {
      response.writeHead(200, { 'Content-Type': 'application/json' })
      response.end(JSON.stringify({ status: 'ok', database: 'ready' }))
    })
    const port = await findAvailablePort()
    await new Promise<void>((resolve) => server.listen(port, '127.0.0.1', resolve))
    const manager = new BackendManager(
      options({
        env: {
          DSS_BACKEND_URL: `http://127.0.0.1:${port}`,
          DSS_API_TOKEN: 'development-token',
        },
      }),
    )

    await expect(manager.start()).resolves.toEqual({
      url: `http://127.0.0.1:${port}`,
      token: 'development-token',
    })
    await manager.stop()
    server.closeAllConnections()
    await new Promise<void>((resolve) => server.close(() => resolve()))
  })

  it('starts and stops an owned backend process cleanly', async () => {
    let unexpectedExit = ''
    const manager = new BackendManager(
      options({
        commandFactory: (desktopArgs: string[]) => ({
          command: process.execPath,
          args: ['-e', healthyServerScript, '--', ...desktopArgs],
          cwd: process.cwd(),
        }),
        onUnexpectedExit: (message: string) => {
          unexpectedExit = message
        },
      }),
    )

    await manager.start()
    await manager.stop()

    expect(unexpectedExit).toBe('')
  })

  it('reports an unexpected backend crash after readiness', async () => {
    let resolveCrash!: (message: string) => void
    const crashMessage = new Promise<string>((resolve) => {
      resolveCrash = resolve
    })
    const manager = new BackendManager(
      options({
        commandFactory: (desktopArgs: string[]) => ({
          command: process.execPath,
          args: [
            '-e',
            `${healthyServerScript}; setTimeout(() => process.exit(7), 500)`,
            '--',
            ...desktopArgs,
          ],
          cwd: process.cwd(),
        }),
        onUnexpectedExit: resolveCrash,
      }),
    )

    await manager.start()
    await expect(crashMessage).resolves.toContain('exit code 7')
  })

  it('times out when an external backend never becomes ready', async () => {
    const port = await findAvailablePort()
    const manager = new BackendManager(
      options({
        env: { DSS_BACKEND_URL: `http://127.0.0.1:${port}` },
        readinessTimeoutMs: 50,
      }),
    )

    await expect(manager.start()).rejects.toThrow('did not become ready')
  })
})
