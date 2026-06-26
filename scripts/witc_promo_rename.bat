@echo off
REM WITC Promo Rename — copies the current week's promo to WITC_PROMO.mp3
REM Finds the upcoming Saturday, matches WITC_PROMO_MM-DD-YY.mp3,
REM and copies it as WITC_PROMO.mp3 in the Spots folder.

cd /d "%~dp0.."

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    $ErrorActionPreference = 'Stop'; ^
    $config = Get-Content download_config.json -Raw | ConvertFrom-Json; ^
    $outDir = $config.output_dir; ^
    if (-not [IO.Path]::IsPathRooted($outDir)) { $outDir = Join-Path (Get-Location) $outDir }; ^
    $spotsDir = Join-Path $outDir Spots; ^
    $today = Get-Date; ^
    $dow = [int]$today.DayOfWeek; ^
    $daysUntilSat = (6 - $dow + 7) %% 7; if ($daysUntilSat -eq 0) { $daysUntilSat = 7 }; ^
    $saturday = $today.AddDays($daysUntilSat); ^
    $dateStr = '{0:D2}-{1:D2}-{2:D2}' -f $saturday.Month, $saturday.Day, ($saturday.Year %% 100); ^
    $src = Join-Path $spotsDir ('WITC_PROMO_' + $dateStr + '.mp3'); ^
    $dst = Join-Path $spotsDir 'WITC_PROMO.mp3'; ^
    if (Test-Path $src) { ^
        Copy-Item $src $dst -Force; ^
        Get-ChildItem $spotsDir -Filter 'WITC_PROMO_*.mp3' -Exclude ('WITC_PROMO_' + $dateStr + '.mp3'), 'WITC_PROMO.mp3' | Remove-Item; ^
        Write-Host ('Copied WITC_PROMO_' + $dateStr + '.mp3 -> WITC_PROMO.mp3, cleaned up old promos') ^
    } ^
    else { Write-Host ('No promo found for date ' + $dateStr) }
