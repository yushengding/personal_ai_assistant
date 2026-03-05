@echo off
setlocal
cd /d %~dp0\..\apps\desktop-shell

if not exist node_modules (
  npm install
)

npm run dev
