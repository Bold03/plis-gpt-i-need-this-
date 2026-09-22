param(
  [Parameter(Mandatory=$true)][string]$XPlaneSdk,
  [string]$BuildDir = "build/cpp"
)
$ErrorActionPreference = "Stop"
cmake -S cpp_bridge -B $BuildDir -DXPLANE_SDK="$XPlaneSdk" -A x64
cmake --build $BuildDir --config Release
Write-Host "Built plugin. Run scripts/package_plugin.py to copy win.xpl into X-Plane Resources/plugins."
