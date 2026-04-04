param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$UserId = 1,
    [int]$PollIntervalSeconds = 3,
    [int]$MaxPollAttempts = 30,
    [switch]$UseSandbox = $true,
    [switch]$OpenCheckout
)

$ErrorActionPreference = "Stop"

Write-Output "=== TEST FLUJO PAGOS (Checkout + Polling) ==="
Write-Output "BaseUrl: $BaseUrl"
Write-Output "UserId: $UserId"

# 1) Crear checkout
$checkoutBody = @{ user_id = $UserId } | ConvertTo-Json
$checkout = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/payments/checkout" -ContentType "application/json" -Body $checkoutBody

$preferenceId = $checkout.preference_id
$initPoint = $checkout.init_point
$sandboxInitPoint = $checkout.sandbox_init_point
$checkoutUrl = $initPoint
if ($UseSandbox -and $sandboxInitPoint) {
    $checkoutUrl = $sandboxInitPoint
}

Write-Output "[1] Checkout creado"
Write-Output "    preference_id: $preferenceId"
Write-Output "    init_point: $initPoint"
Write-Output "    sandbox_init_point: $sandboxInitPoint"
Write-Output "    checkout_url_usada: $checkoutUrl"

if ($OpenCheckout -and $checkoutUrl) {
    Write-Output "[2] Abriendo checkout en navegador..."
    Start-Process $checkoutUrl | Out-Null
} else {
    Write-Output "[2] No se abre navegador (usa -OpenCheckout para abrirlo)."
}

# 3) Polling de estado
Write-Output "[3] Iniciando polling de estado..."
$lastStatus = "unknown"

for ($i = 1; $i -le $MaxPollAttempts; $i++) {
    $statusResp = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/payments/status/$preferenceId"
    $lastStatus = $statusResp.status
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    Write-Output "    intento=$i hora=$timestamp status=$lastStatus"

    if ($lastStatus -eq "approved" -or $lastStatus -eq "rejected") {
        break
    }

    Start-Sleep -Seconds $PollIntervalSeconds
}

Write-Output "[4] Resultado final"
Write-Output "    preference_id: $preferenceId"
Write-Output "    final_status: $lastStatus"

if ($lastStatus -eq "approved") {
    Write-Output "    resultado: EXITO"
    exit 0
}

if ($lastStatus -eq "rejected") {
    Write-Output "    resultado: RECHAZADO"
    exit 2
}

Write-Output "    resultado: TIMEOUT (sin estado final)"
exit 1
