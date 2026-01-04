import { app, BrowserWindow, screen } from 'electron';
import * as path from 'path';

function createWindow() {
    const { width, height } = screen.getPrimaryDisplay().workAreaSize;

    const mainWindow = new BrowserWindow({
        width: Math.floor(width * 0.8),
        height: Math.floor(height * 0.9),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
        titleBarStyle: 'hiddenInset', // Apple Native feel
        vibrancy: 'under-window',     // Apple Native blur
        visualEffectState: 'active',
        backgroundColor: '#00000000', // Transparent for vibrancy
    });

    // Load the Vite dev server URL in development, or the local index.html in production
    const isDev = !app.isPackaged;
    if (isDev) {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    } else {
        mainWindow.loadFile(path.join(__dirname, '../../renderer/dist/index.html'));
    }
}

app.whenReady().then(() => {
    import('electron').then(({ ipcMain, dialog }) => {
        ipcMain.handle('dialog:openFile', async () => {
            const result = await dialog.showOpenDialog({
                properties: ['openFile'],
                filters: [{ name: 'CSV/JSONL', extensions: ['csv', 'jsonl', 'json'] }]
            });
            if (result.canceled) return null;
            return result.filePaths[0];
        });

        ipcMain.handle('dialog:openDirectory', async () => {
            const result = await dialog.showOpenDialog({
                properties: ['openDirectory']
            });
            if (result.canceled) return null;
            return result.filePaths[0];
        });
    });

    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit();
});
