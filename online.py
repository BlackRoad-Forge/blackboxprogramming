<!-- FILE: webstr/web/online.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Lucidia Paste → PR</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#0b0b10;color:#e8e8f0;margin:0}
    .wrap{max-width:960px;margin:40px auto;padding:24px;border-radius:16px;background:#14141d;box-shadow:0 10px 30px rgba(0,0,0,.35)}
    h1{margin:0 0 8px;font-size:22px}
    label{display:block;margin:14px 0 6px;font-weight:600}
    input,textarea,button{width:100%;padding:12px;border-radius:10px;border:1px solid #2a2a3b;background:#0f0f17;color:#f6f6ff}
    textarea{min-height:280px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
    .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .hint{opacity:.7;font-size:12px;margin-top:6px}
    .ok{color:#9be29b}.err{color:#ff6b6b}
  </style>
</head>
<body>
<div class="wrap">
  <h1>Lucidia Co‑Coding -- Paste → PR</h1>
  <div class="row">
    <div>
      <label>Repo (owner/name)</label>
      <input id="repo" value="blackboxprogramming/blackboxprogramming"/>
    </div>
    <div>
      <label>Issue title</label>
      <input id="title" value="Ingest: pasted snippets"/>
    </div>
  </div>
  <label>Paste code here (use <code>&lt;!-- FILE: path --&gt;</code> above fenced blocks)</label>
  <textarea id="body" placeholder="<!-- FILE: web/app/phi.html -->

```html
<!doctype html>
<html><body><h1>Phi online</h1></body></html>
```

<!-- FILE: tools/guardian.py -->

```py
print('guardian online')
```"></textarea>
  <div class="row">
    <button id="send">Create issue → PR</button>
    <button id="demo">Insert demo</button>
  </div>
  <p id="out" class="hint"></p>
</div>
<script>
const $ = s => document.querySelector(s);
function msg(t, bad){ const o=$('#out'); o.textContent=t; o.className = bad ? 'err' : 'ok'; }
$('#demo').onclick = () => {
  $('#body').value = `<!-- FILE: web/app/phi.html -->\n\n\`\`\`html\n<!doctype html>\n<html><body><h1>Phi online</h1></body></html>\n\`\`\`\n\n<!-- FILE: tools/guardian.py -->\n\n\`\`\`py\nprint('guardian online')\n\`\`\``;
};
$('#send').onclick = async () => {
  const repo = $('#repo').value.trim();
  const title = $('#title').value.trim();
  const body  = $('#body').value;
  if(!/^[^\/]+\/[^\/]+$/.test(repo)) return msg('Invalid repo', true);
  if(!title||!body) return msg('Need title + body', true);
  try{
    const r = await fetch('/api/ingest', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({repo, title, body, labels:['ingest','auto']})});
    const j = await r.json();
    if(!r.ok) throw new Error(j.detail || JSON.stringify(j));
    msg(`✅ Issue #${j.number} created. Open PR will follow via workflow.`, false);
  }catch(e){ msg('Error: '+ e.message, true); }
};
</script>
</body>
</html>