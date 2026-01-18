// api/create-issue.js - Vercel Serverless Function
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Sadece POST kabul et
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { question } = req.body;

    if (!question || question.trim().length < 3) {
      return res.status(400).json({
        error: 'Soru çok kısa (en az 3 karakter)',
        success: false
      });
    }

    // Vercel Environment Variable'dan token
    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

    if (!GITHUB_TOKEN) {
      console.error('GITHUB_TOKEN bulunamadı!');
      return res.status(500).json({
        error: 'Server configuration error',
        success: false
      });
    }

    console.log('GitHub Issue oluşturuluyor:', question.substring(0, 50));

    // GitHub API'ye istek gönder
    const githubResponse = await fetch(
      'https://api.github.com/repos/borsaanaliz-raporlar/borsaanaliz-raporlar-/issues',
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Content-Type': 'application/json',
          'User-Agent': 'BorsaAnaliz-AI-Chat'
        },
        body: JSON.stringify({
          title: `🤖 ${question.substring(0, 60)}${question.length > 60 ? '...' : ''}`,
          body: `## 📝 Kullanıcı Sorusu\n\n${question}\n\n---\n**Kaynak:** BorsaAnaliz Web Chat\n**Zaman:** ${new Date().toISOString()}`,
          labels: ['excel-ai', 'web-chat']
        })
      }
    );

    const issueData = await githubResponse.json();

    if (!githubResponse.ok) {
      console.error('GitHub API hatası:', issueData);
      return res.status(githubResponse.status).json({
        error: issueData.message || 'GitHub API hatası',
        details: issueData,
        success: false
      });
    }

    console.log(`✅ Issue #${issueData.number} oluşturuldu`);

    return res.status(200).json({
      success: true,
      issueNumber: issueData.number,
      issueUrl: issueData.html_url,
      message: 'Soru AI\'ya iletildi. Yanıt 1-2 dakika içinde gelecek.'
    });

  } catch (error) {
    console.error('Handler error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      details: error.message,
      success: false
    });
  }
}
