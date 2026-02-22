<?php
session_start();

// CORS izni (güvenlik için sadece kendi sitene izin ver)
header("Access-Control-Allow-Origin: " . $_SERVER['HTTP_ORIGIN']);
header("Access-Control-Allow-Credentials: true");
header("Content-Type: application/json");

// Session kontrolü
$response = [
    'valid' => false,
    'message' => '',
    'forceLogout' => false,
    'version' => getCurrentFileVersion()
];

if (isset($_SESSION['authenticated']) && $_SESSION['authenticated'] === true) {
    $currentTime = time();
    
    // 2 saat kontrolü
    if (isset($_SESSION['login_time'])) {
        if ($currentTime - $_SESSION['login_time'] > 7200) { // 2 saat = 7200 saniye
            session_destroy();
            $response['valid'] = false;
            $response['forceLogout'] = true;
            $response['message'] = '2 saatlik oturum süreniz doldu';
            echo json_encode($response);
            exit;
        }
    }
    
    // Tarih değişimi kontrolü
    if (isset($_SESSION['login_date'])) {
        if ($_SESSION['login_date'] != date('Y-m-d')) {
            session_destroy();
            $response['valid'] = false;
            $response['forceLogout'] = true;
            $response['message'] = 'Yeni güne giriş yapmalısınız';
            echo json_encode($response);
            exit;
        }
    }
    
    // Dosya sürüm kontrolü
    if (isset($_SESSION['file_version'])) {
        $currentVersion = getCurrentFileVersion();
        if ($_SESSION['file_version'] != $currentVersion) {
            session_destroy();
            $response['valid'] = false;
            $response['forceLogout'] = true;
            $response['message'] = 'Yeni dosya sürümü yayınlandı';
            echo json_encode($response);
            exit;
        }
    }
    
    // Her şey yolunda
    $response['valid'] = true;
    $response['login_time'] = $_SESSION['login_time'];
} else {
    $response['valid'] = false;
    $response['forceLogout'] = true;
}

echo json_encode($response);

// Dosya sürümünü belirleme fonksiyonu
function getCurrentFileVersion() {
    // 1. YÖNTEM: Dosya değişim zamanı
    $filePath = __DIR__ . '/raporlar/BORSAANALIZ_V11_TAM_' . date('dmY') . '.xlsm';
    if (file_exists($filePath)) {
        return filemtime($filePath); // Zaman damgası
    }
    
    // 2. YÖNTEM: Versiyon dosyası
    $versionFile = __DIR__ . '/current_version.txt';
    if (file_exists($versionFile)) {
        return trim(file_get_contents($versionFile));
    }
    
    // 3. YÖNTEM: Varsayılan - günlük versiyon
    return date('Y-m-d');
}
?>
