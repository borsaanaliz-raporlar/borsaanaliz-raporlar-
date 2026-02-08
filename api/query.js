// api/query.js - JavaScript Handler (Hemen çalışır)
export default async function handler(req, res) {
  console.log("⚡ Query Engine - JavaScript handler called");
  
  if (req.method === 'GET') {
    return res.status(200).json({
      status: "online",
      service: "BorsaAnaliz Query Engine",
      version: "2.0",
      timestamp: new Date().toISOString(),
      endpoints: {
        "GET /api/query": "Sistem durumu",
        "POST /api/query": "Sorgu çalıştır (JSON body: {query: '...'})",
        "GET /api/ask": "AI asistan",
        "POST /api/ask": "AI analiz"
      },
      example_queries: [
        "Pearson55 > 0.85",
        "VMA pozitif ve Regression55 POZİTİF",
        "BB alt bandına en yakın 10 hisse"
      ]
    });
  }
  
  if (req.method === 'POST') {
    try {
      const { query, debug } = req.body;
      
      // Python motoruna bağlanma simülasyonu
      const mockResults = [
        { hisse: "FROTO", pearson55: 0.938, vma: "POZİTİF (54)", status: "NÖTR", close: 115.7 },
        { hisse: "THYAO", pearson55: 0.935, vma: "POZİTİF (68)", status: "GÜÇLÜ POZİTİF", close: 335.2 },
        { hisse: "GARAN", pearson55: 0.928, vma: "POZİTİF (55)", status: "GÜÇLÜ POZİTİF", close: 28.2 },
        { hisse: "ASELS", pearson55: 0.932, vma: "POZİTİF (61)", status: "POZİTİF", close: 86.4 },
        { hisse: "EREGL", pearson55: 0.925, vma: "POZİTİF (49)", status: "POZİTİF", close: 52.8 }
      ];
      
      // Filtreleme simülasyonu
      let results = [...mockResults];
      
      if (query && query.includes("Pearson55")) {
        results = results.filter(h => h.pearson55 > 0.85);
      }
      
      if (query && query.includes("VMA pozitif")) {
        results = results.filter(h => h.vma.includes("POZİTİF"));
      }
      
      return res.status(200).json({
        success: true,
        query: query || "No query provided",
        results: results,
        count: results.length,
        execution_time: "0.1s",
        note: "JavaScript handler - Python engine bağlantısı kuruluyor...",
        debug: debug || false
      });
      
    } catch (error) {
      return res.status(500).json({
        success: false,
        error: error.message,
        query: req.body?.query || "Unknown"
      });
    }
  }
  
  // Method not allowed
  return res.status(405).json({
    success: false,
    error: "Method not allowed. Use GET or POST."
  });
}
