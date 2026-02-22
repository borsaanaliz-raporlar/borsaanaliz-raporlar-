<?php
session_start();
header('Content-Type: application/json');

$correctPassword = "ba"; // Şifren burada (güvenlik için veritabanına taşı)

$input = json_decode(file_get_contents('php://input'), true);
$password = isset($input['password']) ? $input['password'] : '';

$response = ['success' => false, 'message' => ''];

if ($password === $correctPassword) {
    $_SESSION['authenticated'] = true;
    $_SESSION['login_time'] = time();
    $_SESSION['login_date'] = date('Y-m-d');
    $_SESSION['file_version'] = getCurrentFileVersion();
    
    $response['success'] = true;
    $response['message'] = 'Giriş başarılı';
} else {
    $response['message'] = 'Hatalı şifre';
}

echo json_encode($response);

function getCurrentFileVersion() {
    $filePath = __DIR__ . '/raporlar/BORSAANALIZ_V11_TAM_' . date('dmY') . '.xlsm';
    if (file_exists($filePath)) {
        return filemtime($filePath);
    }
    return date('Y-m-d');
}
?>
