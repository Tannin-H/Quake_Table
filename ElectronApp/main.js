const { app, BrowserWindow } = require('electron');
const { exec } = require('child_process');
const path = require('path');

let mainWindow;

app.on('ready', () => {
    // Start the Python PythonBackend
    const server = exec('python ../python-PythonBackend/app.py');

    // Open a window after server starts
    setTimeout(() => {
        mainWindow = new BrowserWindow({
            width: 800,
            height: 600,
            webPreferences: {
                nodeIntegration: false
            }
        });

        mainWindow.loadURL('http://127.0.0.1:5000');
    }, 3000);

    // Stop the Python server when the app closes
    app.on('before-quit', () => {
        server.kill();
    });
});



