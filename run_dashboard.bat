@echo off
title Face Recognition Web Dashboard
echo ========================================================
echo  Face Recognition Web Dashboard (React + Vite)
echo ========================================================
echo  Dashboard URL: http://localhost:3000
echo ========================================================
echo.

start http://localhost:3000
cd dashboard
npm run dev
pause
