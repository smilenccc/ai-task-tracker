#!/usr/bin/env node
/**
 * AI 任務統計系統 - REST API Server
 * 
 * 功能：
 *   - GET /api/tasks - 取得所有任務
 *   - POST /api/tasks - 新增任務
 *   - PUT /api/tasks/:id - 更新任務
 *   - DELETE /api/tasks/:id - 刪除任務
 *   - 自動同步到 GitHub
 */

import express from 'express';
import cors from 'cors';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, '..');

const PORT = process.env.PORT || 5568;
const TASKS_PATH = resolve(ROOT, 'tasks.json');

// ── 資料操作 ────────────────────────────────────────
function loadTasks() {
    if (!existsSync(TASKS_PATH)) {
        return { tasks: [], lastUpdated: new Date().toISOString() };
    }
    try {
        return JSON.parse(readFileSync(TASKS_PATH, 'utf-8'));
    } catch {
        return { tasks: [], lastUpdated: new Date().toISOString() };
    }
}

function saveTasks(data) {
    data.lastUpdated = new Date().toISOString();
    writeFileSync(TASKS_PATH, JSON.stringify(data, null, 2), 'utf-8');
    
    // 自動推送到 GitHub
    try {
        execSync('git add tasks.json', { cwd: ROOT });
        const taskCount = data.tasks.length;
        const completedCount = data.tasks.filter(t => t.status === 'completed').length;
        execSync(`git commit -m "任務更新：${taskCount} 筆任務（${completedCount} 已完成）"`, { cwd: ROOT });
        execSync('git push origin main', { cwd: ROOT });
        console.log('✅ 已推送到 GitHub');
    } catch (e) {
        console.warn('⚠️ Git 推送失敗:', e.message);
    }
}

// ── Server ──────────────────────────────────────────
const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' }));

// 靜態檔案
app.use(express.static(ROOT));

// API：取得所有任務
app.get('/api/tasks', (req, res) => {
    try {
        const data = loadTasks();
        res.json(data);
    } catch (error) {
        console.error('載入任務失敗:', error);
        res.status(500).json({ error: 'Failed to load tasks' });
    }
});

// API：新增任務
app.post('/api/tasks', (req, res) => {
    try {
        const { title, description, category, status, source } = req.body;
        
        if (!title) {
            return res.status(400).json({ error: 'Title is required' });
        }
        
        const data = loadTasks();
        const newTask = {
            id: data.tasks.length > 0 ? Math.max(...data.tasks.map(t => t.id)) + 1 : 1,
            title,
            description: description || '',
            category: category || '其他',
            status: status || 'pending',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            source: source || 'api'
        };
        
        data.tasks.push(newTask);
        saveTasks(data);
        
        console.log(`✅ 新增任務 #${newTask.id}: ${title}`);
        res.json({ success: true, task: newTask });
    } catch (error) {
        console.error('新增任務失敗:', error);
        res.status(500).json({ error: 'Failed to create task' });
    }
});

// API：更新任務
app.put('/api/tasks/:id', (req, res) => {
    try {
        const taskId = parseInt(req.params.id);
        const updates = req.body;
        
        const data = loadTasks();
        const taskIndex = data.tasks.findIndex(t => t.id === taskId);
        
        if (taskIndex === -1) {
            return res.status(404).json({ error: 'Task not found' });
        }
        
        data.tasks[taskIndex] = {
            ...data.tasks[taskIndex],
            ...updates,
            updatedAt: new Date().toISOString()
        };
        
        saveTasks(data);
        
        console.log(`✅ 更新任務 #${taskId}: ${data.tasks[taskIndex].title}`);
        res.json({ success: true, task: data.tasks[taskIndex] });
    } catch (error) {
        console.error('更新任務失敗:', error);
        res.status(500).json({ error: 'Failed to update task' });
    }
});

// API：刪除任務
app.delete('/api/tasks/:id', (req, res) => {
    try {
        const taskId = parseInt(req.params.id);
        
        const data = loadTasks();
        const taskIndex = data.tasks.findIndex(t => t.id === taskId);
        
        if (taskIndex === -1) {
            return res.status(404).json({ error: 'Task not found' });
        }
        
        const deletedTask = data.tasks.splice(taskIndex, 1)[0];
        saveTasks(data);
        
        console.log(`✅ 刪除任務 #${taskId}: ${deletedTask.title}`);
        res.json({ success: true, task: deletedTask });
    } catch (error) {
        console.error('刪除任務失敗:', error);
        res.status(500).json({ error: 'Failed to delete task' });
    }
});

// API：統計資訊
app.get('/api/stats', (req, res) => {
    try {
        const data = loadTasks();
        const stats = {
            total: data.tasks.length,
            completed: data.tasks.filter(t => t.status === 'completed').length,
            pending: data.tasks.filter(t => t.status === 'pending').length,
            inProgress: data.tasks.filter(t => t.status === 'in-progress').length,
            byCategory: {},
            lastUpdated: data.lastUpdated
        };
        
        data.tasks.forEach(task => {
            stats.byCategory[task.category] = (stats.byCategory[task.category] || 0) + 1;
        });
        
        res.json(stats);
    } catch (error) {
        console.error('載入統計失敗:', error);
        res.status(500).json({ error: 'Failed to load stats' });
    }
});

// 健康檢查
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'tasks-api' });
});

// 首頁
app.get('/', (req, res) => {
    res.sendFile(resolve(ROOT, 'tasks.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log('');
    console.log('📋 AI 任務統計系統 API 啟動');
    console.log(`🌐 http://localhost:${PORT}`);
    console.log(`📡 API: http://localhost:${PORT}/api/tasks`);
    console.log('');
});
