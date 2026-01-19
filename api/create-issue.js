// api/create-issue.js - DÜZELTİLMİŞ VERSİYON
module.exports = async (req, res) => {
  console.log('API called:', req.method);
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');
  
  // Handle preflight
  if (req.method === 'OPTIONS') {
    console.log('CORS preflight');
    res.status(200).end();
    return;
  }
  
  // Only POST allowed
  if (req.method !== 'POST') {
    console.log('Method not allowed:', req.method);
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed. Use POST.' 
    });
  }
  
  try {
    console.log('Parsing request body...');
    let body = {};
    
    // Parse request body
    if (typeof req.body === 'string') {
      body = JSON.parse(req.body);
    } else if (req.body) {
      body = req.body;
    }
    
    const { question } = body;
    
    console.log('Question received:', question ? question.substring(0, 50) : 'No question');
    
    if (!question || question.trim().length < 3) {
      return res.status(400).json({ 
        success: false, 
        error: 'Soru çok kısa (en az 3 karakter)' 
      });
    }
    
    // Get token from Vercel env
    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    
    if (!GITHUB_TOKEN) {
      console.error('❌ GITHUB_TOKEN missing in environment variables');
      return res.status(500).json({ 
        success: false, 
        error: 'Server configuration error: GITHUB_TOKEN not found' 
      });
    }
    
    console.log('Creating GitHub issue...');
    
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
      console.error('❌ GitHub API error:', issueData);
      return res.status(githubResponse.status).json({
        success: false,
        error: issueData.message || 'GitHub API error',
        details: issueData.errors || 'No details'
      });
    }
    
    console.log(`✅ Issue created: #${issueData.number} - ${issueData.html_url}`);
    
    return res.status(200).json({
      success: true,
      issueNumber: issueData.number,
      issueUrl: issueData.html_url,
      message: 'Soru AI\'ya iletildi'
    });
    
  } catch (error) {
    console.error('❌ API Error:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      details: error.message,
      stack: error.stack
    });
  }
};
