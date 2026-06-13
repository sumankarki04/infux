# INFUX Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete INFUX — Nepal's first influencer-brand marketplace — by finishing all missing templates, fixing discovered bugs, and verifying the full app runs.

**Architecture:** Flask 3 app with 6 blueprints (public/auth/influencer/brand/admin/chat), SQLAlchemy ORM, Bootstrap 5.3 + custom violet/gold design system. SQLite for dev, Supabase PostgreSQL for production (configured via DATABASE_URL env var).

**Tech Stack:** Flask 3, SQLAlchemy, Flask-Login, Flask-WTF, Bootstrap 5.3.3, AOS animations, Font Awesome 6.5, Fraunces + Plus Jakarta Sans fonts, bleach sanitization, python-dotenv.

---

## File Map

| File | Status | Task |
|------|--------|------|
| `app/templates/chat/inbox.html` | CREATE | Task 1 |
| `app/templates/chat/chat.html` | CREATE | Task 2 |
| `app/static/uploads/default.png` | CREATE | Task 3 |
| `app/routes/public.py` | FIX — route param name mismatch | Task 4 |
| `app/templates/brand/campaign_detail.html` | FIX — wrong url_for param | Task 4 |
| `app/templates/admin/influencers.html` | FIX — wrong url_for param | Task 4 |
| `app/static/css/style.css` | FIX — add missing `--violet-light` alias | Task 4 |
| `app/static/css/style.css` | ENHANCE — chat bubble CSS | Task 2 |
| `run.py` | VERIFY — app starts clean | Task 5 |

---

### Task 1: Chat Inbox Template

Shows all conversations with last message preview + unread badge.

**Files:**
- Create: `app/templates/chat/inbox.html`

Context passed from `chat.inbox()`:
- `conversations` — list of dicts: `{'partner': User, 'last_msg': Message|None, 'unread': int}`

- [ ] **Step 1: Create `app/templates/chat/inbox.html`**

```html
{% extends "base.html" %}
{% block title %}Messages - INFUX{% endblock %}
{% block content %}

<div class="inner-banner">
    <div class="container">
        <div class="section-label mb-2">Chat</div>
        <h1 class="mb-0" style="font-size:clamp(1.4rem,3vw,1.9rem);">
            Your <span style="background:linear-gradient(135deg,var(--violet),var(--gold));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Messages</span>
        </h1>
    </div>
</div>

<div class="container py-4" style="max-width:720px;">
    {% if conversations %}
    <div class="card border-0 shadow-sm rounded-4" data-aos="fade-up">
        {% for conv in conversations %}
        <a href="{{ url_for('chat.chat', partner_id=conv.partner.user_id) }}"
           class="d-flex align-items-center gap-3 p-3 text-decoration-none conv-row
                  {% if not loop.last %}border-bottom{% endif %}"
           style="border-color:#f1f5f9!important;transition:background .15s;">
            <div class="position-relative flex-shrink-0">
                <img src="{{ conv.partner.avatar_url() }}" class="rounded-circle"
                     style="width:52px;height:52px;object-fit:cover;border:2px solid var(--violet-lt);"
                     alt="{{ conv.partner.full_name() }}">
                {% if conv.unread > 0 %}
                <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill"
                      style="background:var(--violet);font-size:.65rem;">{{ conv.unread }}</span>
                {% endif %}
            </div>
            <div class="flex-grow-1 min-width-0">
                <div class="d-flex justify-content-between align-items-baseline">
                    <span class="fw-semibold {% if conv.unread %}text-dark{% else %}text-muted{% endif %}"
                          style="{% if conv.unread %}color:var(--navy)!important;{% endif %}">
                        {{ conv.partner.full_name() }}
                    </span>
                    {% if conv.last_msg %}
                    <span class="text-muted" style="font-size:.72rem;white-space:nowrap;margin-left:.5rem;">
                        {{ conv.last_msg.created_at.strftime('%b %d') }}
                    </span>
                    {% endif %}
                </div>
                <div class="text-muted small text-truncate" style="font-size:.82rem;max-width:400px;">
                    {% if conv.last_msg %}
                        {% if conv.last_msg.sender_id == current_user.user_id %}
                        <span style="color:var(--violet);font-weight:500;">You: </span>
                        {% endif %}
                        {{ conv.last_msg.content[:80] }}{% if conv.last_msg.content|length > 80 %}...{% endif %}
                    {% else %}
                        <em>No messages yet</em>
                    {% endif %}
                </div>
            </div>
            <i class="fas fa-chevron-right text-muted" style="font-size:.75rem;flex-shrink:0;"></i>
        </a>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty-state" data-aos="fade-up">
        <div class="empty-state-icon"><i class="fas fa-comment-dots"></i></div>
        <h5 class="fw-bold mb-2">No conversations yet</h5>
        <p class="text-muted mb-4">Accept an application or get accepted to start messaging.</p>
        {% if current_user.user_type == 'brand' %}
        <a href="{{ url_for('brand.my_campaigns') }}" class="btn btn-violet rounded-pill px-5">
            <i class="fas fa-bullhorn me-2"></i>View Campaigns
        </a>
        {% else %}
        <a href="{{ url_for('influencer.browse_campaigns') }}" class="btn btn-violet rounded-pill px-5">
            <i class="fas fa-search me-2"></i>Browse Campaigns
        </a>
        {% endif %}
    </div>
    {% endif %}
</div>

<style>
.conv-row:hover { background: #f8fafc; }
.min-width-0 { min-width: 0; }
</style>
{% endblock %}
```

- [ ] **Step 2: Verify template renders** — start app, log in, go to `/chat/inbox`

---

### Task 2: Chat Conversation Template + JS Polling

Real-time chat UI with message bubbles and 2-second polling.

**Files:**
- Create: `app/templates/chat/chat.html`
- Modify: `app/static/css/style.css` — ensure chat CSS classes present

Context from `chat.chat()`:
- `partner` — User object
- `messages` — list of Message objects (ordered asc)
- `PARTNER_ID` — int, the other user's ID

- [ ] **Step 1: Verify chat CSS exists in `app/static/css/style.css`**

Search for `.chat-wrapper`. If missing, add after the last rule:

```css
/* ── Chat ── */
.chat-wrapper { display:flex; flex-direction:column; height:65vh; overflow-y:auto; padding:1.25rem; gap:.75rem; background:#f8fafc; border-radius:var(--radius); }
.bubble { max-width:72%; padding:.6rem 1rem; border-radius:18px; line-height:1.5; font-size:.9rem; word-break:break-word; }
.bubble-me   { background:var(--violet); color:#fff; border-bottom-right-radius:4px; align-self:flex-end; }
.bubble-them { background:#fff; color:var(--text); border:1px solid var(--border); border-bottom-left-radius:4px; align-self:flex-start; }
.bubble-time { font-size:.68rem; opacity:.65; margin-top:.2rem; }
.chat-input-wrap { display:flex; gap:.5rem; padding:1rem; border-top:1px solid var(--border); background:#fff; border-radius:0 0 var(--radius) var(--radius); }
```

- [ ] **Step 2: Create `app/templates/chat/chat.html`**

```html
{% extends "base.html" %}
{% block title %}Chat with {{ partner.full_name() }} - INFUX{% endblock %}
{% block content %}

<div class="container py-4" style="max-width:720px;">
    <!-- Header -->
    <div class="d-flex align-items-center gap-3 mb-3" data-aos="fade-up">
        <a href="{{ url_for('chat.inbox') }}" class="btn btn-sm btn-outline-secondary rounded-pill px-3">
            <i class="fas fa-arrow-left me-1"></i>Back
        </a>
        <img src="{{ partner.avatar_url() }}" class="rounded-circle"
             style="width:42px;height:42px;object-fit:cover;border:2px solid var(--violet-lt);"
             alt="{{ partner.full_name() }}">
        <div>
            <div class="fw-bold" style="color:var(--navy);">{{ partner.full_name() }}</div>
            <div class="text-muted" style="font-size:.75rem;">{{ partner.user_type|title }}</div>
        </div>
    </div>

    <div class="card border-0 shadow-sm rounded-4 overflow-hidden" data-aos="fade-up">
        <!-- Messages -->
        <div class="chat-wrapper" id="chatWrapper">
            {% for msg in messages %}
            <div class="d-flex flex-column {% if msg.sender_id == current_user.user_id %}align-items-end{% else %}align-items-start{% endif %}"
                 data-msg-id="{{ msg.message_id }}">
                <div class="bubble {% if msg.sender_id == current_user.user_id %}bubble-me{% else %}bubble-them{% endif %}">
                    {{ msg.content }}
                </div>
                <div class="bubble-time {% if msg.sender_id == current_user.user_id %}text-end{% endif %}">
                    {{ msg.created_at.strftime('%H:%M') }}
                </div>
            </div>
            {% endfor %}
            {% if not messages %}
            <div class="text-center text-muted small py-4">
                <i class="fas fa-comment-dots fa-2x mb-2 d-block" style="color:var(--border);"></i>
                Say hello to {{ partner.first_name }}!
            </div>
            {% endif %}
        </div>

        <!-- Input -->
        <div class="chat-input-wrap">
            <input type="text" id="msgInput" class="form-control rounded-pill"
                   placeholder="Type a message..." autocomplete="off" maxlength="2000">
            <button id="sendBtn" class="btn btn-violet rounded-pill px-4" type="button">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    </div>
</div>

<script>
(function() {
    const PARTNER_ID = {{ PARTNER_ID }};
    const MY_ID = {{ current_user.user_id }};
    const wrapper = document.getElementById('chatWrapper');
    const input   = document.getElementById('msgInput');
    const sendBtn = document.getElementById('sendBtn');

    let lastId = {{ messages[-1].message_id if messages else 0 }};

    function scrollBottom() {
        wrapper.scrollTop = wrapper.scrollHeight;
    }
    scrollBottom();

    function appendMsg(id, content, senderId, time) {
        const isMe = senderId === MY_ID;
        const wrap = document.createElement('div');
        wrap.className = 'd-flex flex-column ' + (isMe ? 'align-items-end' : 'align-items-start');
        wrap.dataset.msgId = id;
        wrap.innerHTML = `
            <div class="bubble ${isMe ? 'bubble-me' : 'bubble-them'}">${escHtml(content)}</div>
            <div class="bubble-time ${isMe ? 'text-end' : ''}">${time}</div>`;
        wrapper.appendChild(wrap);
        scrollBottom();
    }

    function escHtml(s) {
        return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    async function send() {
        const content = input.value.trim();
        if (!content) return;
        input.value = '';
        sendBtn.disabled = true;
        try {
            const r = await fetch(`/chat/${PARTNER_ID}/send`, {
                method: 'POST',
                headers: {'Content-Type':'application/json', 'X-CSRFToken': csrfToken()},
                body: JSON.stringify({content})
            });
            if (r.ok) {
                const msg = await r.json();
                appendMsg(msg.id, msg.content, msg.sender_id, msg.created_at);
                lastId = msg.id;
            }
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }

    async function poll() {
        try {
            const r = await fetch(`/chat/${PARTNER_ID}/messages?since=${lastId}`);
            if (r.ok) {
                const msgs = await r.json();
                msgs.forEach(m => {
                    if (m.sender_id !== MY_ID) {
                        appendMsg(m.id, m.content, m.sender_id, m.created_at);
                        lastId = m.id;
                    }
                });
            }
        } catch(e) {}
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
    setInterval(poll, 2000);
})();
</script>
{% endblock %}
```

- [ ] **Step 3: Test chat** — log in as two different users, send messages, verify polling works

---

### Task 3: Default Avatar Image

Without `default.png` in uploads, every avatar_url() call returns a broken image.

**Files:**
- Create: `app/static/uploads/default.png` (1x1 transparent PNG, or copy placeholder)

- [ ] **Step 1: Create placeholder avatar**

Run in Python (from `E:\INFUX`):

```python
# Creates a simple 80x80 violet circle PNG as default avatar
from PIL import Image, ImageDraw
img = Image.new('RGB', (80, 80), color='#7c3aed')
draw = ImageDraw.Draw(img)
draw.ellipse([5,5,75,75], fill='#5b21b6')
img.save('app/static/uploads/default.png')
```

Or run via shell:
```bash
cd E:\INFUX
python -c "from PIL import Image,ImageDraw; img=Image.new('RGB',(80,80),'#7c3aed'); ImageDraw.Draw(img).ellipse([5,5,75,75],fill='#5b21b6'); img.save('app/static/uploads/default.png')"
```

- [ ] **Step 2: Verify** — `/static/uploads/default.png` loads in browser

---

### Task 4: Bug Fixes

Three bugs found during code review.

**Files:**
- Modify: `app/routes/public.py:98` — route uses `influencer_id` param, but templates pass `user_id`
- Modify: `app/templates/brand/campaign_detail.html` — fix url_for param
- Modify: `app/templates/admin/influencers.html` — fix url_for param
- Modify: `app/static/css/style.css` — add `--violet-light` alias for `--violet-lt`

**Bug A — Route/template param mismatch:**

`public.py` route:
```python
@public_bp.route('/influencer/<int:influencer_id>')
def influencer_profile(influencer_id):
    inf = Influencer.query.get_or_404(influencer_id)
```

But `brand/campaign_detail.html` calls:
```
url_for('public.influencer_profile', user_id=app.influencer.user_id)  # WRONG
```

Fix: change route to accept `user_id` and look up Influencer by user_id:

- [ ] **Step 1: Fix `app/routes/public.py` line 98**

Replace:
```python
@public_bp.route('/influencer/<int:influencer_id>')
def influencer_profile(influencer_id):
    inf = Influencer.query.get_or_404(influencer_id)
    return render_template('public/influencer_profile.html', inf=inf)
```

With:
```python
@public_bp.route('/influencer/<int:user_id>')
def influencer_profile(user_id):
    inf = Influencer.query.filter_by(user_id=user_id).first_or_404()
    return render_template('public/influencer_profile.html', inf=inf)
```

- [ ] **Step 2: Fix `app/templates/brand/campaign_detail.html`**

No change needed — already passes `user_id=app.influencer.user_id` which now matches.

- [ ] **Step 3: Fix `app/templates/admin/influencers.html` line with `url_for('public.influencer_profile')`**

Find line:
```
<a href="{{ url_for('public.influencer_profile', user_id=inf.user_id) }}"
```
Confirm it passes `user_id` — already correct after Step 1.

**Bug B — CSS variable alias:**

Templates use `var(--violet-light)` but CSS only defines `--violet-lt`.

- [ ] **Step 4: Add alias to `app/static/css/style.css` `:root` block**

Find `:root {` block and add one line:
```css
  --violet-light: #ede9fe;   /* alias for --violet-lt */
```

**Bug C — `app/models/brand.py` missing `created_at`:**

`admin/brands.html` references `br.created_at`. Verify the Brand model has it.

- [ ] **Step 5: Read `app/models/brand.py` and confirm/add `created_at`**

If missing, add to Brand model:
```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

### Task 5: Verify App Starts

- [ ] **Step 1: Install deps**
```powershell
cd E:\INFUX
pip install -r requirements.txt
```
Expected: `Successfully installed ...` or `Requirement already satisfied`

- [ ] **Step 2: Start app**
```powershell
cd E:\INFUX
python run.py
```
Expected output includes:
```
* Running on http://127.0.0.1:5001
```
No `ImportError`, no `TemplateNotFound`.

- [ ] **Step 3: Smoke test routes**

Open browser and verify these load without 500 errors:
- `http://127.0.0.1:5001/` — home page with stats + influencer cards
- `http://127.0.0.1:5001/auth/register` — register form
- `http://127.0.0.1:5001/auth/login` — login form
- `http://127.0.0.1:5001/discover` — influencer grid
- `http://127.0.0.1:5001/campaigns` — campaigns list

- [ ] **Step 4: Login as admin and verify dashboard**

Credentials: `admin@infux.com` / `admin123`
Go to `/admin/dashboard` — should show 6 influencers, 4 brands, 4 campaigns.

- [ ] **Step 5: Login as influencer and verify flow**

Credentials: `suman@infux.com` / `pass123`
- Go to `/influencer/dashboard` — stat cards visible
- Go to `/influencer/campaigns` — campaign cards + Apply modal
- Apply to one campaign
- Check `/influencer/applications` — pending application visible

- [ ] **Step 6: Login as brand and verify flow**

Credentials: `retail@maya.com` / `pass123`
- Go to `/brand/dashboard` — campaign table visible
- Go to `/brand/campaigns` — campaign with status Open
- Click campaign → `/brand/campaigns/<id>` — applications list visible
- Accept application → status changes to Accepted

---

### Task 6: Graphify Knowledge Map

Run graphify on completed INFUX codebase to produce architecture docs.

- [ ] **Step 1: Run `/graphify E:\INFUX`** via the graphify skill

Expected output: `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`

---

## Self-Review Notes

- **Route param fix (Task 4)** — critical bug. Without it every influencer profile link 404s.
- **Default avatar (Task 3)** — without it every `<img>` is broken, breaking card layouts.
- **CSS var alias (Task 4B)** — visual-only but affects border styling on avatar images.
- **Chat polling (Task 2)** — `lastId` correctly initialized from last server-rendered message to avoid re-fetching history.
- **Brand model created_at** — verify before deploying; admin brands table references it.
