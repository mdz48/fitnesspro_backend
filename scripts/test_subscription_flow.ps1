param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$UserId = 3,
    [int]$ExistingPlanId = 23,
    [switch]$CreatePlan,
    [switch]$UseNoPlan,
    [string]$CardTokenId = "",
    [switch]$OpenCheckout,
    [switch]$PauseBeforePolling,
    [ValidateSet("any", "test", "production")]
    [string]$ExpectedMpMode = "any",
    [int]$PollIntervalSeconds = 5,
    [int]$MaxPollAttempts = 24,
    [switch]$RunLifecycleOps
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Output "`n=== $Message ==="
}

function Invoke-Api {
    param(
        [string]$Method,
        [string]$Url,
        [object]$Body = $null
    )

    try {
        if ($null -ne $Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 10
            return Invoke-RestMethod -Method $Method -Uri $Url -ContentType "application/json" -Body $jsonBody
        }
        return Invoke-RestMethod -Method $Method -Uri $Url -ContentType "application/json"
    } catch {
        $statusCode = $null
        $responseText = ""
        if ($_.Exception.Response) {
            try {
                $statusCode = [int]$_.Exception.Response.StatusCode
            } catch {
                $statusCode = $null
            }
        }

        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $responseText = $_.ErrorDetails.Message
        } elseif ($_.Exception.Message) {
            $responseText = $_.Exception.Message
        }

        throw "HTTP error calling $Method $Url | status=$statusCode | response=$responseText"
    }
}

$summary = [ordered]@{
    plan_created = $false
    plan_id = $null
    subscription_created = $false
    subscription_id = $null
    checkout_url = $null
    final_status = $null
    lifecycle_pause = "not_run"
    lifecycle_reactivate = "not_run"
    lifecycle_cancel = "not_run"
    blocker = $null
    recommendation = $null
}

function Set-RecommendationFromBlocker {
    param([string]$Blocker)

    if (-not $Blocker) {
        return $null
    }

    if ($Blocker -match "Both payer and collector must be real or test users") {
        return "Alinea ambientes: collector y payer deben ser ambos TEST o ambos reales. Cambia MERCADOPAGO_ACCESS_TOKEN al seller test correspondiente o usa payer real."
    }

    if ($Blocker -match "Cannot operate between different countries") {
        return "Collector y payer deben ser del mismo pais (MLM). Verifica que user.email sea buyer TEST MLM y que el seller/token tambien sea MLM."
    }

    if ($Blocker -match "card_token_id is required") {
        return "Para este flujo MP exige card_token_id. Genera token de tarjeta de prueba y pasalo con -CardTokenId."
    }

    if ($Blocker -match "Unsupported_credit_card_for_recurring_payment") {
        return "La tarjeta/token no soporta pagos recurrentes. Prueba otro BIN/tarjeta de prueba para suscripciones recurrentes."
    }

    return "Revisa mp_response en blocker para detalle exacto y ajusta credenciales/token de prueba."
}

Write-Output "Iniciando pruebas de suscripciones"
Write-Output "BaseUrl=$BaseUrl UserId=$UserId ExistingPlanId=$ExistingPlanId CreatePlan=$CreatePlan UseNoPlan=$UseNoPlan"

Write-Step "Validacion de modo Mercado Pago (runtime backend)"
try {
    $mpMode = Invoke-Api -Method "GET" -Url "$BaseUrl/api/subscriptions/debug/mp-mode"
    Write-Output "access_token_mode=$($mpMode.access_token_mode) public_key_mode=$($mpMode.public_key_mode) modes_match=$($mpMode.modes_match)"

    if ($ExpectedMpMode -ne "any" -and $mpMode.access_token_mode -ne $ExpectedMpMode) {
        throw "Modo MP inesperado. Esperado=$ExpectedMpMode actual=$($mpMode.access_token_mode). Reinicia backend tras cambiar .env."
    }

    if (-not $mpMode.modes_match) {
        throw "MERCADOPAGO_ACCESS_TOKEN y MERCADOPAGO_PUBLIC_KEY no estan en el mismo modo (test/production)."
    }
} catch {
    throw "No se pudo validar modo MP en runtime: $($_.Exception.Message)"
}

$planId = $ExistingPlanId

if (-not $UseNoPlan -and ($CreatePlan -or $planId -le 0)) {
    Write-Step "Crear plan de suscripcion"
    $planName = "Plan Test $(Get-Date -Format 'yyyyMMddHHmmss')"
    $planBody = @{
        name = $planName
        description = "Plan generado por script de pruebas"
        reason = "FitnessPro Premium - Mensual"
        frequency = 1
        frequency_type = "months"
        transaction_amount = 10.0
        currency_id = "MXN"
        billing_day = 1
        billing_day_proportional = $true
        free_trial = @{
            frequency = 7
            frequency_type = "days"
        }
    }

    $planResp = Invoke-Api -Method "POST" -Url "$BaseUrl/api/subscriptions/plans" -Body $planBody
    $planId = [int]$planResp.id
    $summary.plan_created = $true
    $summary.plan_id = $planId
    Write-Output "Plan creado id=$($planResp.id) mp_plan_id=$($planResp.mp_plan_id)"
} elseif (-not $UseNoPlan) {
    Write-Step "Usar plan existente"
    $summary.plan_id = $planId
    Write-Output "Usando ExistingPlanId=$planId"
}

Write-Step "Crear suscripcion"
$subResp = $null

if ($UseNoPlan) {
    $subBody = @{
        user_id = $UserId
        reason = "FitnessPro Premium - Mensual"
        frequency = 1
        frequency_type = "months"
        transaction_amount = 10.0
        currency_id = "MXN"
    }
    if ($CardTokenId) {
        $subBody.card_token_id = $CardTokenId
    }
    try {
        $subResp = Invoke-Api -Method "POST" -Url "$BaseUrl/api/subscriptions/no-plan" -Body $subBody
    } catch {
        $summary.blocker = $_.Exception.Message
    }
} else {
    $subBody = @{
        user_id = $UserId
        plan_id = $planId
    }
    if ($CardTokenId) {
        $subBody.card_token_id = $CardTokenId
    }

    try {
        $subResp = Invoke-Api -Method "POST" -Url "$BaseUrl/api/subscriptions" -Body $subBody
    } catch {
        $errorText = $_.Exception.Message
        if (($errorText -match "card_token_id is required") -and (-not $CardTokenId)) {
            Write-Output "Mercado Pago requiere card_token_id para /subscriptions; probando fallback /subscriptions/no-plan"
            $fallbackBody = @{
                user_id = $UserId
                reason = "FitnessPro Premium - Mensual"
                frequency = 1
                frequency_type = "months"
                transaction_amount = 10.0
                currency_id = "MXN"
            }
            try {
                $subResp = Invoke-Api -Method "POST" -Url "$BaseUrl/api/subscriptions/no-plan" -Body $fallbackBody
            } catch {
                $summary.blocker = $_.Exception.Message
            }
        } else {
            $summary.blocker = $errorText
        }
    }
}

if ($subResp) {
    $subscriptionId = [int]$subResp.subscription_id
    $checkoutUrl = if ($subResp.sandbox_init_point) { $subResp.sandbox_init_point } else { $subResp.init_point }

    $summary.subscription_created = $true
    $summary.subscription_id = $subscriptionId
    $summary.checkout_url = $checkoutUrl

    Write-Output "Suscripcion creada subscription_id=$subscriptionId mp_preapproval_id=$($subResp.mp_preapproval_id)"
    Write-Output "[1] checkout_url=$checkoutUrl"

    if ($OpenCheckout -and $checkoutUrl) {
        Write-Output "[2] Abriendo checkout en navegador..."
        Write-Output "    Inicia sesion con un BUYER TEST del mismo ambiente/pais que el SELLER (collector)."
        Start-Process $checkoutUrl | Out-Null
    } elseif ($checkoutUrl) {
        Write-Output "[2] No se abre navegador (usa -OpenCheckout para abrirlo)."
    }

    if ($PauseBeforePolling) {
        Write-Output "[3] Cuando termines login/autorizacion en checkout, presiona Enter para iniciar polling..."
        [void](Read-Host)
    }

    Write-Step "Polling de estado"
    $lastStatus = "unknown"
    for ($i = 1; $i -le $MaxPollAttempts; $i++) {
        $statusResp = Invoke-Api -Method "GET" -Url "$BaseUrl/api/subscriptions/$subscriptionId/status"
        $lastStatus = $statusResp.status
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Output "    intento=$i hora=$ts status=$lastStatus"

        if ($lastStatus -in @("authorized", "paused", "cancelled")) {
            break
        }

        Start-Sleep -Seconds $PollIntervalSeconds
    }
    $summary.final_status = $lastStatus
} else {
    Write-Output "No se pudo crear suscripcion. Revisa blocker en resumen."
    if ($OpenCheckout) {
        Write-Output "No se abrio navegador porque no se obtuvo checkout_url (la suscripcion no se creo)."
    }
    $summary.final_status = "not_created"
}

if ($RunLifecycleOps -and $summary.subscription_created) {
    Write-Step "Pruebas de ciclo de vida"

    try {
        $pauseResp = Invoke-Api -Method "PUT" -Url "$BaseUrl/api/subscriptions/$subscriptionId/pause" -Body @{ reason = "Prueba automatizada" }
        $summary.lifecycle_pause = "ok:$($pauseResp.status)"
        Write-Output "Pause OK status=$($pauseResp.status)"
    } catch {
        $summary.lifecycle_pause = "error"
        Write-Output "Pause ERROR: $($_.Exception.Message)"
    }

    try {
        $reactivateResp = Invoke-Api -Method "PUT" -Url "$BaseUrl/api/subscriptions/$subscriptionId/reactivate"
        $summary.lifecycle_reactivate = "ok:$($reactivateResp.status)"
        Write-Output "Reactivate OK status=$($reactivateResp.status)"
    } catch {
        $summary.lifecycle_reactivate = "error"
        Write-Output "Reactivate ERROR: $($_.Exception.Message)"
    }

    try {
        $cancelResp = Invoke-Api -Method "PUT" -Url "$BaseUrl/api/subscriptions/$subscriptionId/cancel" -Body @{ reason = "Cierre prueba automatizada" }
        $summary.lifecycle_cancel = "ok:$($cancelResp.status)"
        Write-Output "Cancel OK status=$($cancelResp.status)"
    } catch {
        $summary.lifecycle_cancel = "error"
        Write-Output "Cancel ERROR: $($_.Exception.Message)"
    }
}

Write-Step "Resumen"
$summary.recommendation = Set-RecommendationFromBlocker -Blocker $summary.blocker
$summary | ConvertTo-Json -Depth 10 | Write-Output

if (-not $summary.subscription_created) {
    exit 3
}

if ($summary.final_status -eq "authorized") {
    exit 0
}

if ($summary.final_status -eq "pending") {
    exit 1
}

exit 0