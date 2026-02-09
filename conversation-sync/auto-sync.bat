@echo off
REM AI Task Tracker - Hourly Auto Sync
REM Called by Windows Task Scheduler every hour
cd /d "C:\Users\smile\Documents\ai-task-tracker"
C:\Python314\python.exe conversation-sync\auto-sync.py
