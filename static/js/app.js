const chatEl = document.getElementById('chat');
const formEl = document.getElementById('form');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');

function el(html) { const d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; }

function addMessage(role, htmlContent) {
    const node = el(`
        <div class="msg role-${role}">
            <div class="avatar">${role === 'user' ? 'U' : 'AI'}</div>
            <div class="content">${htmlContent}</div>
        </div>
    `);
    chatEl.appendChild(node);
    chatEl.scrollTop = chatEl.scrollHeight;
    return node.querySelector('.content');
}

function addTyping() {
    const n = el(`<div class="typing">Assistant is typing…</div>`);
    chatEl.appendChild(n);
    chatEl.scrollTop = chatEl.scrollHeight;
    return n;
}

async function streamChat(message) {
    const typing = addTyping();
    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        if (!resp.ok) {
            let detail = '';
            try { detail = await resp.text(); } catch (_) {}
            throw new Error(`HTTP ${resp.status} ${resp.statusText}${detail ? ': ' + detail : ''}`);
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buf = '';
        let text = '';
        const contentEl = addMessage('assistant', '');
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });
            // Attempt to parse as one big JSON (since server wraps chunks array)
            try {
                const obj = JSON.parse(buf);
                if (obj && obj.chunks) {
                    const deltas = [];
                    let errorMsg = '';
                    for (const c of obj.chunks) {
                        if (c && typeof c.error === 'string' && c.error) errorMsg = c.error;
                        if (c && typeof c.delta === 'string') deltas.push(c.delta);
                    }
                    if (errorMsg) {
                        contentEl.innerHTML = `<span style="color:#f87171">${errorMsg}</span>`;
                    } else {
                        text = deltas.join('');
                        contentEl.innerHTML = marked.parse(text);
                    }
                    chatEl.scrollTop = chatEl.scrollHeight;
                }
            } catch (_) {
                // wait for valid JSON
            }
        }
        if (text.trim()) {
            await fetch('/api/commit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: text })
            });
        }
    } catch (e) {
        addMessage('assistant', `<span style="color:#f87171">${e.message || 'Error'}</span>`);
    } finally {
        typing.remove();
    }
}

formEl.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = inputEl.value.trim();
    if (!msg) return;
    addMessage('user', marked.parse(msg));
    inputEl.value = '';
    inputEl.focus();
    await streamChat(msg);
});

resetBtn.addEventListener('click', async () => {
    await fetch('/api/reset', { method: 'POST' });
    chatEl.innerHTML = '';
});

// Submit on Enter (Shift+Enter inserts newline)
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (typeof formEl.requestSubmit === 'function') {
            formEl.requestSubmit();
        } else {
            formEl.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        }
    }
});

