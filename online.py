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