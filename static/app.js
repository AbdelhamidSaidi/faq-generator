(() => {
  const form = document.getElementById('form');
  const statusEl = document.getElementById('status');
  const result = document.getElementById('result');
  const downloadBtn = document.getElementById('downloadBtn');
  const scrapedLink = document.getElementById('scraped-link');
  let lastJson = null;

  function setStatus(msg, isError = false) {
    statusEl.textContent = msg;
    statusEl.style.color = isError ? '#b00020' : '#333';
  }

  async function generate(payload) {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.json();
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    result.innerHTML = '';
    downloadBtn.style.display = 'none';
    scrapedLink.style.display = 'none';

    const url = document.getElementById('url').value.trim();
    const text = document.getElementById('text').value.trim();
    if (!url && !text) { setStatus('Enter a URL or paste page text to continue', true); return; }

    setStatus('Generating FAQs…');
    try {
      const payload = text ? { text } : { url };
      const data = await generate(payload);
      if (!data || !data.success) {
        setStatus('Error: ' + (data?.error || 'Unknown error'), true);
        if (data?.raw) {
          const pre = document.createElement('pre'); pre.textContent = data.raw; result.appendChild(pre);
        }
        return;
      }

      setStatus('Done');
      const faqs = data.faqs || [];
      lastJson = data.faqs;
      if (Array.isArray(faqs)) {
        faqs.forEach(item => {
          const el = document.createElement('section'); el.className = 'faq';
          const q = document.createElement('h3'); q.textContent = item.question || '';
          const a = document.createElement('p'); a.textContent = item.answer || '';
          el.appendChild(q); el.appendChild(a); result.appendChild(el);
        });
      } else {
        const pre = document.createElement('pre'); pre.textContent = JSON.stringify(faqs, null, 2); result.appendChild(pre);
      }

      // show scraped text link and download
      scrapedLink.style.display = 'inline-block';
      downloadBtn.style.display = 'inline-block';
    } catch (err) {
      setStatus('Request failed: ' + err, true);
    }
  });

  downloadBtn.addEventListener('click', () => {
    if (!lastJson) return;
    const blob = new Blob([JSON.stringify(lastJson, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'faqs.json'; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  });
})();