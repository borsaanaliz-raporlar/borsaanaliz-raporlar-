const axios = require('axios');
const fs = require('fs');

// 1. GitHub'dan gelen soruyu oku
const eventPath = process.env.GITHUB_EVENT_PATH;
const eventData = require(eventPath);
const question = eventData.client_payload.question;

console.log('Soru:', question);

// 2. DeepSeek API'ye bağlan
async function getAnswer() {
  try {
    const response = await axios.post(
      'https://api.deepseek.com/chat/completions',
      {
        model: 'deepseek-chat',
        messages: [
          {
            role: 'system',
            content: `Sen BORSAANALIZ V11 asistanısın. 
            Kullanıcılara Excel analiz raporları hakkında yardım ediyorsun.
            Raporlarda 9 sayfa var.
            MACRO açma, RSI analizi, hisse seçimi konularında yardımcı ol.
            Türkçe ve anlaşılır yanıt ver.`
          },
          {
            role: 'user',
            content: question
          }
        ],
        max_tokens: 1000
      },
      {
        headers: {
          'Authorization': `Bearer ${process.env.DEEPSEEK_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const answer = response.data.choices[0].message.content;
    console.log('Yanıt:', answer);
    
    // 3. Yanıtı dosyaya yaz
    fs.writeFileSync('response.txt', answer);
    
  } catch (error) {
    console.error('Hata:', error.message);
    fs.writeFileSync('response.txt', 'Üzgünüm, şu anda yanıt veremiyorum.');
  }
}

getAnswer();
