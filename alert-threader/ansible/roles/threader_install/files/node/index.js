import express from 'express';
import fetch from 'node-fetch';
import { createClient } from 'redis';

// =============================
// Environment Variables
// =============================
const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN;
const SLACK_CHANNEL = process.env.SLACK_CHANNEL;  // 권장: 채널 ID(Cxxxx)
const ENVIRONMENT = process.env.ENVIRONMENT || 'staging';
const THREAD_STORE = process.env.THREAD_STORE || 'file';   // file|redis
const THREAD_STORE_FILE = process.env.THREAD_STORE_FILE || '/var/lib/alert-threader/threads.json';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';
const REDIS_KEY_PREFIX = process.env.REDIS_KEY_PREFIX || 'threader:ts';

// =============================
// Application
// =============================
const app = express();
app.use(express.json());

let _thread_cache = {};   // key -> thread_ts
let _redis = null;

// =============================
// Utilities
// =============================
function sev_color(sev) {
    sev = (sev || "info").toLowerCase();
    return {"critical": "#E01E5A", "warning": "#ECB22E"}[sev] || "#2EB67D";
}

function sev_emoji(sev) {
    return {"critical": "🚨", "warning": "⚠️"}[(sev || "info").toLowerCase()] || "ℹ️";
}

function thread_key(alert) {
    const name = alert.labels?.alertname || "unknown";
    const sev = alert.labels?.severity || "info";
    return `${name}|${sev}|${ENVIRONMENT}`;
}

// =============================
// Storage (File / Redis)
// =============================
function load_cache_file() {
    try {
        const fs = require('fs');
        if (fs.existsSync(THREAD_STORE_FILE)) {
            _thread_cache = JSON.parse(fs.readFileSync(THREAD_STORE_FILE, 'utf8'));
        }
    } catch (err) {
        console.error('Failed to load cache file:', err);
        _thread_cache = {};
    }
}

function save_cache_file() {
    if (THREAD_STORE !== 'file') return;
    try {
        const fs = require('fs');
        const path = require('path');
        const dir = path.dirname(THREAD_STORE_FILE);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        const tmp = THREAD_STORE_FILE + '.tmp';
        fs.writeFileSync(tmp, JSON.stringify(_thread_cache, null, 2));
        fs.renameSync(tmp, THREAD_STORE_FILE);
    } catch (err) {
        console.error('Failed to save cache file:', err);
    }
}

async function load_cache_redis() {
    try {
        _redis = createClient({ url: REDIS_URL });
        await _redis.connect();
        _thread_cache = {};
    } catch (err) {
        console.error('Failed to connect to Redis:', err);
        throw new Error('Redis connection failed');
    }
}

async function store_get_ts(key) {
    if (THREAD_STORE === 'redis') {
        let ts = _thread_cache[key];
        if (ts) return ts;
        try {
            const v = await _redis.get(`${REDIS_KEY_PREFIX}:${key}`);
            if (v) {
                _thread_cache[key] = v;
            }
            return v;
        } catch (err) {
            console.error('Redis get error:', err);
            return null;
        }
    }
    return _thread_cache[key];
}

async function store_set_ts(key, ts) {
    if (THREAD_STORE === 'redis') {
        try {
            await _redis.set(`${REDIS_KEY_PREFIX}:${key}`, ts);
            _thread_cache[key] = ts;
        } catch (err) {
            console.error('Redis set error:', err);
        }
        return;
    }
    _thread_cache[key] = ts;
    save_cache_file();
}

// =============================
// Slack payload (Block Kit + attachments color)
// =============================
function build_blocks(summary, sev, description, labels) {
    const emoji = sev_emoji(sev);
    const fields = [
        {"type": "mrkdwn", "text": `*Severity:*\n\`${sev}\``},
        {"type": "mrkdwn", "text": `*Environment:*\n\`${ENVIRONMENT}\``},
    ];
    for (const k of ["alertname", "instance", "job"]) {
        if (labels[k]) {
            fields.push({"type": "mrkdwn", "text": `*${k}:*\n\`${labels[k]}\``});
        }
    }
    const blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": `${emoji} ${summary}`, "emoji": true}},
        {"type": "section", "fields": fields},
    ];
    if (description) {
        blocks.push({"type": "section", "text": {"type": "mrkdwn", "text": description}});
    }
    blocks.push({"type": "context", "elements": [{"type": "mrkdwn", "text": `\`env=${ENVIRONMENT}\``}]});
    return blocks;
}

async function slack_post_message(text, blocks = null, thread_ts = null, color = null) {
    const payload = {
        channel: SLACK_CHANNEL,
        text: text,
        unfurl_links: false,
        unfurl_media: false,
    };
    if (blocks) payload.blocks = blocks;
    if (thread_ts) payload.thread_ts = thread_ts;
    if (color) payload.attachments = [{"color": color}];
    
    const headers = {"Authorization": `Bearer ${SLACK_BOT_TOKEN}`};
    const response = await fetch("https://slack.com/api/chat.postMessage", {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    if (!data.ok) {
        throw new Error(`Slack error: ${JSON.stringify(data)}`);
    }
    return data;
}

// =============================
// Startup
// =============================
async function startup() {
    if (THREAD_STORE === 'redis') {
        await load_cache_redis();
    } else {
        load_cache_file();
    }
}

// =============================
// Webhook
// =============================
app.post('/alert', async (req, res) => {
    try {
        const body = req.body;
        const status = body.status;         // firing|resolved
        const alerts = body.alerts || [];
        const results = [];
        
        for (const a of alerts) {
            const labels = a.labels || {};
            const ann = a.annotations || {};
            const key = thread_key(a);
            const ts = await store_get_ts(key);
            const summary = ann.summary || labels.alertname || "(no summary)";
            const description = ann.description || "";
            const sev = labels.severity || "info";
            const color = sev_color(sev);

            let text, blocks;
            if (status === "resolved") {
                text = `[${ENVIRONMENT}] ✅ RESOLVED: ${summary}`;
                blocks = build_blocks(`RESOLVED — ${summary}`, sev, description, labels);
            } else {
                text = `[${ENVIRONMENT}] ${sev.toUpperCase()} — ${summary}`;
                blocks = build_blocks(summary, sev, description, labels);
            }

            if (!ts) {
                const data = await slack_post_message(text, blocks, null, color);
                const new_ts = data.ts;
                await store_set_ts(key, new_ts);
                results.push({"key": key, "thread_ts": new_ts, "status": status});
            } else {
                await slack_post_message(text, blocks, ts, color);
                results.push({"key": key, "thread_ts": ts, "status": status});
            }
        }
        
        res.json({"ok": true, "count": results.length, "results": results});
    } catch (error) {
        console.error('Alert processing error:', error);
        res.status(500).json({"ok": false, "error": error.message});
    }
});

app.get('/health', (req, res) => {
    res.json({"status": "ok", "store": THREAD_STORE, "env": ENVIRONMENT});
});

app.get('/stats', (req, res) => {
    res.json({
        "thread_cache_size": Object.keys(_thread_cache).length,
        "store_type": THREAD_STORE,
        "environment": ENVIRONMENT
    });
});

// =============================
// Start Server
// =============================
const PORT = process.env.PORT || 9010;
const HOST = process.env.HOST || '0.0.0.0';

startup().then(() => {
    app.listen(PORT, HOST, () => {
        console.log(`Alert Threader (Node.js) listening on ${HOST}:${PORT}`);
        console.log(`Environment: ${ENVIRONMENT}`);
        console.log(`Store: ${THREAD_STORE}`);
    });
}).catch(err => {
    console.error('Startup failed:', err);
    process.exit(1);
});
