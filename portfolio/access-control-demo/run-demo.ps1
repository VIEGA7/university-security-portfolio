$ErrorActionPreference = 'Stop'
$env:ASPNETCORE_ENVIRONMENT = 'Development'
$env:DEMO_ADMIN_USER = 'admin'
$env:DEMO_READER_USER = 'reader'
$adminSecret = Read-Host 'Temporary admin password (12+ characters)' -AsSecureString
$readerSecret = Read-Host 'Temporary reader password (12+ characters)' -AsSecureString
function Get-PlainText([Security.SecureString]$secret) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}
try {
    $env:DEMO_ADMIN_PASSWORD = Get-PlainText $adminSecret
    $env:DEMO_READER_PASSWORD = Get-PlainText $readerSecret
    dotnet run --project "$PSScriptRoot/AccessControlDemo.csproj" --urls http://127.0.0.1:5087
} finally {
    Remove-Item Env:DEMO_ADMIN_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:DEMO_READER_PASSWORD -ErrorAction SilentlyContinue
}
