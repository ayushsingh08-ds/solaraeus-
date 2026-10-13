# ==============================================================================
# SOLARAEUS CPU Benchmark Runner (PowerShell for Windows)
# Usage:
#   .\benchmarks\benchmark_cpu.ps1 [-Scene <scene_a|scene_b|scene_c|all>] [-Mode <full|inc|all>] [-Repeats <int>] [-Output <path>]
# Example:
#   .\benchmarks\benchmark_cpu.ps1 -Scene scene_b -Repeats 5
# ==============================================================================

param (
    [string]$Scene = "all",
    [string]$Mode = "all",
    [int]$Repeats = 5,
    [string]$Output = "$PSScriptRoot\..\results\raw\stage_5\benchmark_cpu_results.json"
)

$RootDir = Resolve-Path "$PSScriptRoot\.."

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "SOLARAEUS Stage 5: Running CPU Performance Benchmark" -ForegroundColor Cyan
Write-Host "Scene:   $Scene"
Write-Host "Mode:    $Mode"
Write-Host "Repeats: $Repeats"
Write-Host "Output:  $Output"
Write-Host "================================================================================" -ForegroundColor Cyan

python "$RootDir\benchmarks\benchmark_cpu.py" --scene $Scene --mode $Mode --repeats $Repeats --output $Output
