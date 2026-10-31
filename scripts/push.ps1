# 一键推送：把本地仓库推到 Gitee / GitHub
# 用法：右键“使用 PowerShell 运行”，或双击同目录的 推送代码.bat
param([string]$RepoUrl)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$git = Join-Path $root "tools\mingit\cmd\git.exe"
if (-not (Test-Path $git)) { $git = "git" }

if (-not $RepoUrl) {
    Write-Host ""
    Write-Host "请粘贴仓库地址，例如：" -ForegroundColor Cyan
    Write-Host "  https://gitee.com/你的用户名/campus-lost-found.git"
    Write-Host "  https://github.com/你的用户名/campus-lost-found.git"
    Write-Host ""
    $RepoUrl = Read-Host "仓库地址"
}
$RepoUrl = $RepoUrl.Trim()
if (-not $RepoUrl) { Write-Host "没有输入地址，已退出"; pause; exit 1 }

Write-Host ""
Write-Host "== 1/3 设置远程地址 ==" -ForegroundColor Cyan
& $git remote remove origin 2>$null
& $git remote add origin $RepoUrl

Write-Host "== 2/3 推送代码 ==" -ForegroundColor Cyan
Write-Host "如果提示输入账号密码：用户名填你的账号，密码填登录密码（GitHub 需要 Personal Access Token）"
& $git push -u origin main

Write-Host ""
Write-Host "== 3/3 完成 ==" -ForegroundColor Green
& $git log --oneline -3
Write-Host ""
Write-Host "打开仓库地址确认能看到文件：$RepoUrl"
pause
