// api/ask.js - AI Asistan JavaScript handler
export default async function handler(req, res) {
  console.log("🤖 AI Asistan - JavaScript handler called");
  
  if (req.method === 'GET') {
    return res.status(200).json({
      status: "online",
      service: "BorsaAnaliz AI Asistan",
      version: "2.0",
      capabilities: [
        "630+ hisse teknik analizi",
        "Gerçek Excel verileri",
        "VMA, EMA, Pivot analizi",
        "Pearson korelasyon değerlendirmesi"
      ]
    });
  }
  
  if (req.method === 'POST') {
    const { question } = req.body;
    
    return res.status(200).json({
      success: true,
      question: question || "No question provided",
      answer: "🤖 AI asistan JavaScript handler'da çalışıyor. Python entegrasyonu yakında...",
      sample_answer: `Örnek analiz: FROTO hissesi 115.7 TL, VMA: POZİTİF (54), Pearson55: 0.938, Durum: NÖTR`,
      note: "Python motoru bağlantısı kurulduğunda tam analiz gelecek"
    });
  }
  
  return res.status(405).json({ error: "Method not allowed" });
}
