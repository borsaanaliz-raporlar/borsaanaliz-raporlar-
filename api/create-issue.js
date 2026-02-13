module.exports = async (req, res) => {
    // CORS headers
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');
    
    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }
    
    if (req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }
    
    try {
        const { question } = req.body;
        console.log('📝 Orijinal soru:', question);
        
        // 🆕 MOD KONTROLÜ EKLENDİ
        let detailed = false;
        let processedQuestion = question;
        
        if (question && question.startsWith('📋 detaylı ')) {
            detailed = true;
            processedQuestion = question.replace('📋 detaylı ', '');
            console.log('📋 DETAYLI mod aktif');
        } else if (question && question.startsWith('⚡ ')) {
            processedQuestion = question.replace('⚡ ', '');
            console.log('⚡ HIZLI mod aktif');
        }
        
        // 🆕 Issue başlığına mod bilgisi ekle
        const titlePrefix = detailed ? '📋 ' : '⚡ ';
        const issueTitle = `${titlePrefix}${processedQuestion.substring(0, 50)}${processedQuestion.length > 50 ? '...' : ''}`;
        
        // 🆕 Issue body'sine mod bilgisi ekle
        const issueBody = `## 📝 Kullanıcı Sorusu\n\n${processedQuestion}\n\n` +
                         `---\n` +
                         `**Mod:** ${detailed ? '📋 Detaylı Analiz' : '⚡ Hızlı Analiz'}\n` +
                         `**Zaman:** ${new Date().toISOString()}\n` +
                         `**Kaynak:** BorsaAnaliz Web Chat`;
        
        // GitHub issue oluştur
        const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
        
        const githubResponse = await fetch(
            'https://api.github.com/repos/borsaanaliz-raporlar/borsaanaliz-raporlar-/issues',
            {
                method: 'POST',
                headers: {
                    'Authorization': `token ${GITHUB_TOKEN}`,
                    'Content-Type': 'application/json',
                    'User-Agent': 'BorsaAnaliz-AI'
                },
                body: JSON.stringify({
                    title: issueTitle,
                    body: issueBody,
                    labels: detailed ? ['excel-ai', 'detayli-analiz'] : ['excel-ai', 'hizli-analiz']
                })
            }
        );
        
        const issueData = await githubResponse.json();
        
        if (!githubResponse.ok) {
            return res.status(githubResponse.status).json({
                success: false,
                error: issueData.message || 'GitHub API error'
            });
        }
        
        return res.status(200).json({
            success: true,
            issueNumber: issueData.number,
            issueUrl: issueData.html_url,
            message: detailed ? '📋 Detaylı analiz isteğiniz iletildi!' : '⚡ Hızlı analiz isteğiniz iletildi!'
        });
        
    } catch (error) {
        console.error('❌ API Error:', error);
        return res.status(500).json({
            success: false,
            error: 'Internal server error'
        });
    }
};
