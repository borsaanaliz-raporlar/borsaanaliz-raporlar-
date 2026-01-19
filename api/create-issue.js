// api/create-issue.js - ÇALIŞAN VERSİYON
module.exports = async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');
  
  // Handle preflight
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  // Only POST allowed
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const { question } = JSON.parse(req.body || '{}');
    
    if (!question || question.trim().length < 3) {
      return res.status(400).json({ 
        success: false, 
        error: 'Soru çok kısa (en az 3 karakter)' 
      });
    }
    
    // Get token from Vercel env
    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    
    if (!GITHUB_TOKEN) {
      console.error('GITHUB_TOKEN missing in env');
      return res.status(500).json({ 
        success: false, 
        error: 'Server configuration error' 
      });
    }
    
    // Create GitHub issue
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
          title: `🤖 ${question.substring(0, 60)}${question.length > 60 ? '...' : ''}`,
          body: `## 📝 Kullanıcı Sorusu\n\n${question}\n\n---\n**Kaynak:** BorsaAnaliz Web Chat\n**Zaman:** ${new Date().toISOString()}`,
          labels: ['excel-ai', 'web-chat']
        })
      }
    );
    
    const issueData = await githubResponse.json();
    
    if (!githubResponse.ok) {
      console.error('GitHub API error:', issueData);
      return res.status(githubResponse.status).json({
        success: false,
        error: issueData.message || 'GitHub API error'
      });
    }
    
    console.log(`✅ Issue created: #${issueData.number}`);
    
    return res.status(200).json({
      success: true,
      issueNumber: issueData.number,
      issueUrl: issueData.html_url,
      message: 'Soru AI\'ya iletildi'
    });
    
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal server error: ' + error.message
    });
  }
};
