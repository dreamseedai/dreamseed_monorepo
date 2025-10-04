#!/usr/bin/env node
/**
 * DreamSeed Alertmanager Slack Threader - Advanced Node.js Version
 * - 파일/Redis 기반 thread_ts 영속 저장소
 * - Slack Block Kit + Attachments 컬러 강조
 * - 고급 메시지 포맷팅 및 필드 구성
 */

import fs from 'fs';
import path from 'path';
import express from 'express';
import fetch from 'node-fetch';
import { createClient } from 'redis';

// 환경 변수
const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN;
const SLACK_CHANNEL = process.env.SLACK_CHANNEL;
const ENVIRONMENT = process.env.ENVIRONMENT || 'staging';
const BIND_HOST = process.env.BIND_HOST || '0.0.0.0';
const BIND_PORT = parseInt(process.env.BIND_PORT || '9009');

// 저장소 설정
const THREAD_STORE = process.env.THREAD_STORE || 'file';
const THREAD_STORE_FILE = process.env.THREAD_STORE_FILE || '/var/lib/alert-threader/threads.json';
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379/0';
const REDIS_KEY_PREFIX = process.env.REDIS_KEY_PREFIX || 'threader:ts';

// 필수 환경 변수 검증
if (!SLACK_BOT_TOKEN) {
    console.error('❌ SLACK_BOT_TOKEN 환경 변수가 필요합니다');
    process.exit(1);
}
if (!SLACK_CHANNEL) {
    console.error('❌ SLACK_CHANNEL 환경 변수가 필요합니다');
    process.exit(1);
}

const app = express();
app.use(express.json());

// 전역 변수
let threadCache = new Map(); // key -> thread_ts
let redisClient = null;

// === 유틸리티 함수 ===

function getSeverityColor(severity) {
    const colorMap = {
        'critical': '#E01E5A',  // 빨강
        'warning': '#ECB22E',   // 노랑
        'info': '#2EB67D',      // 초록
        'error': '#E01E5A',     // 빨강
        'success': '#2EB67D',   // 초록
        'debug': '#36C5F0',     // 파랑
    };
    return colorMap[severity?.toLowerCase()] || '#2EB67D';
}

function getSeverityEmoji(severity) {
    const emojiMap = {
        'critical': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️',
        'error': '❌',
        'success': '✅',
        'debug': '🐛',
    };
    return emojiMap[severity?.toLowerCase()] || '📢';
}

function threadKey(alert) {
    const labels = alert.labels || {};
    const name = labels.alertname || 'unknown';
    const severity = labels.severity || 'info';
    const service = labels.service || 'unknown';
    const cluster = labels.cluster || 'default';
    return `${name}|${severity}|${service}|${cluster}|${ENVIRONMENT}`;
}

function formatTimestamp(timestamp) {
    try {
        const dt = new Date(timestamp);
        return dt.toISOString().replace('T', ' ').replace('Z', ' UTC');
    } catch {
        return timestamp;
    }
}

// === 저장소 관리 (파일/Redis) ===

function ensureParentDirectory(filePath) {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
}

function loadCacheFile() {
    try {
        if (fs.existsSync(THREAD_STORE_FILE)) {
            const data = fs.readFileSync(THREAD_STORE_FILE, 'utf8');
            const parsed = JSON.parse(data);
            threadCache = new Map(Object.entries(parsed));
            console.log(`📁 파일에서 ${threadCache.size}개 스레드 로드됨`);
        }
    } catch (error) {
        console.error('파일 캐시 로드 실패:', error);
        threadCache = new Map();
    }
}

function saveCacheFile() {
    if (THREAD_STORE !== 'file') return;
    
    try {
        ensureParentDirectory(THREAD_STORE_FILE);
        const tmpFile = THREAD_STORE_FILE + '.tmp';
        const data = JSON.stringify(Object.fromEntries(threadCache), null, 2);
        fs.writeFileSync(tmpFile, data);
        fs.renameSync(tmpFile, THREAD_STORE_FILE);
        console.log(`💾 파일에 ${threadCache.size}개 스레드 저장됨`);
    } catch (error) {
        console.error('파일 캐시 저장 실패:', error);
    }
}

async function loadCacheRedis() {
    try {
        redisClient = createClient({ url: REDIS_URL });
        redisClient.on('error', (err) => console.error('Redis 오류:', err));
        await redisClient.connect();
        threadCache = new Map(); // Redis는 지연 로딩 사용
        console.log('🔴 Redis 연결 초기화됨');
    } catch (error) {
        console.error('Redis 연결 실패:', error);
        throw error;
    }
}

async function storeGetTs(key) {
    if (THREAD_STORE === 'redis') {
        // 로컬 캐시 먼저 확인
        if (threadCache.has(key)) {
            return threadCache.get(key);
        }
        
        // Redis에서 조회
        try {
            const ts = await redisClient.get(`${REDIS_KEY_PREFIX}:${key}`);
            if (ts) {
                threadCache.set(key, ts);
            }
            return ts;
        } catch (error) {
            console.error('Redis 조회 실패:', error);
            return null;
        }
    } else {
        // 파일 저장소
        return threadCache.get(key) || null;
    }
}

async function storeSetTs(key, ts) {
    if (THREAD_STORE === 'redis') {
        try {
            await redisClient.set(`${REDIS_KEY_PREFIX}:${key}`, ts);
            threadCache.set(key, ts);
            console.log(`🔴 Redis에 스레드 저장: ${key} -> ${ts}`);
        } catch (error) {
            console.error('Redis 저장 실패:', error);
        }
    } else {
        // 파일 저장소
        threadCache.set(key, ts);
        saveCacheFile();
    }
}

// === Slack Block Kit 포맷팅 ===

function buildAlertBlocks(alert, status) {
    const labels = alert.labels || {};
    const annotations = alert.annotations || {};
    
    const alertname = labels.alertname || 'Unknown';
    const severity = labels.severity || 'info';
    const service = labels.service || 'unknown';
    const instance = labels.instance || '';
    const cluster = labels.cluster || 'default';
    
    const summary = annotations.summary || alertname;
    const description = annotations.description || '';
    const runbookUrl = annotations.runbook_url || '';
    
    const emoji = getSeverityEmoji(severity);
    
    // 상태에 따른 헤더 텍스트
    let headerText;
    if (status === 'resolved') {
        headerText = `✅ RESOLVED — ${summary}`;
    } else {
        headerText = `${emoji} ${summary}`;
    }
    
    // 헤더 블록
    const blocks = [
        {
            type: 'header',
            text: {
                type: 'plain_text',
                text: headerText,
                emoji: true
            }
        }
    ];
    
    // 필드 섹션
    const fields = [
        {
            type: 'mrkdwn',
            text: `*Severity:*\n\`${severity.toUpperCase()}\``
        },
        {
            type: 'mrkdwn',
            text: `*Environment:*\n\`${ENVIRONMENT}\``
        },
        {
            type: 'mrkdwn',
            text: `*Service:*\n\`${service}\``
        },
        {
            type: 'mrkdwn',
            text: `*Cluster:*\n\`${cluster}\``
        }
    ];
    
    // 인스턴스가 있으면 추가
    if (instance) {
        fields.push({
            type: 'mrkdwn',
            text: `*Instance:*\n\`${instance}\``
        });
    }
    
    blocks.push({
        type: 'section',
        fields: fields
    });
    
    // 설명이 있으면 추가
    if (description) {
        blocks.push({
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: `*Description:*\n${description}`
            }
        });
    }
    
    // Runbook URL이 있으면 추가
    if (runbookUrl) {
        blocks.push({
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: `*Runbook:* <${runbookUrl}|View Runbook>`
            }
        });
    }
    
    // 시간 정보
    const startsAt = alert.startsAt || '';
    const endsAt = alert.endsAt || '';
    
    const timeInfo = [];
    if (startsAt) {
        timeInfo.push(`Started: ${formatTimestamp(startsAt)}`);
    }
    if (endsAt && status === 'resolved') {
        timeInfo.push(`Resolved: ${formatTimestamp(endsAt)}`);
    }
    
    if (timeInfo.length > 0) {
        blocks.push({
            type: 'context',
            elements: [
                {
                    type: 'mrkdwn',
                    text: timeInfo.join(' | ')
                }
            ]
        });
    }
    
    // 환경 정보
    blocks.push({
        type: 'context',
        elements: [
            {
                type: 'mrkdwn',
                text: `\`env=${ENVIRONMENT}\` | \`alertname=${alertname}\``
            }
        ]
    });
    
    return blocks;
}

function buildAlertAttachments(alert, status) {
    const labels = alert.labels || {};
    const severity = labels.severity || 'info';
    const color = getSeverityColor(severity);
    
    // 기본 attachment
    const attachment = {
        color: color,
        fallback: `[${ENVIRONMENT}] ${labels.alertname || 'Unknown'}`
    };
    
    // 필드 구성
    const fields = [];
    
    // 심각도
    fields.push({
        title: 'Severity',
        value: severity.toUpperCase(),
        short: true
    });
    
    // 환경
    fields.push({
        title: 'Environment',
        value: ENVIRONMENT,
        short: true
    });
    
    // 서비스
    if (labels.service) {
        fields.push({
            title: 'Service',
            value: labels.service,
            short: true
        });
    }
    
    // 클러스터
    if (labels.cluster) {
        fields.push({
            title: 'Cluster',
            value: labels.cluster,
            short: true
        });
    }
    
    // 인스턴스
    if (labels.instance) {
        fields.push({
            title: 'Instance',
            value: labels.instance,
            short: true
        });
    }
    
    // Job
    if (labels.job) {
        fields.push({
            title: 'Job',
            value: labels.job,
            short: true
        });
    }
    
    attachment.fields = fields;
    
    // 설명
    if (labels.description || (alert.annotations && alert.annotations.description)) {
        attachment.text = alert.annotations?.description || labels.description;
    }
    
    // 시간 정보
    const startsAt = alert.startsAt || '';
    if (startsAt) {
        attachment.ts = Math.floor(new Date(startsAt).getTime() / 1000);
    }
    
    return [attachment];
}

async function slackPostMessage(text, options = {}) {
    const { blocks, attachments, threadTs } = options;
    
    const payload = {
        channel: SLACK_CHANNEL,
        text: text,
        unfurl_links: false,
        unfurl_media: false
    };
    
    if (blocks) {
        payload.blocks = blocks;
    }
    
    if (attachments) {
        payload.attachments = attachments;
    }
    
    if (threadTs) {
        payload.thread_ts = threadTs;
    }
    
    try {
        const response = await fetch('https://slack.com/api/chat.postMessage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${SLACK_BOT_TOKEN}`
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (!data.ok) {
            throw new Error(`Slack API 오류: ${data.error}`);
        }
        
        return data;
    } catch (error) {
        console.error('Slack API 요청 실패:', error);
        throw error;
    }
}

// === Express 엔드포인트 ===

app.get('/health', (req, res) => {
    const healthData = {
        status: 'healthy',
        environment: ENVIRONMENT,
        channel: SLACK_CHANNEL,
        thread_store: THREAD_STORE,
        cached_threads: threadCache.size,
        timestamp: new Date().toISOString()
    };
    
    res.json(healthData);
});

app.post('/alert', async (req, res) => {
    try {
        const { status, alerts = [], groupKey = '' } = req.body;
        
        console.log(`📨 Received ${alerts.length} alerts with status: ${status}`);
        
        const results = [];
        
        for (const alert of alerts) {
            try {
                const key = threadKey(alert);
                let threadTs = await storeGetTs(key);
                
                const labels = alert.labels || {};
                const annotations = alert.annotations || {};
                
                const alertname = labels.alertname || 'Unknown';
                const severity = labels.severity || 'info';
                const summary = annotations.summary || alertname;
                
                // 메시지 텍스트 (fallback)
                let text;
                if (status === 'resolved') {
                    text = `[${ENVIRONMENT}] ✅ RESOLVED: ${summary}`;
                } else {
                    text = `[${ENVIRONMENT}] ${severity.toUpperCase()}: ${summary}`;
                }
                
                // Block Kit 구성
                const blocks = buildAlertBlocks(alert, status);
                
                // Attachments 구성
                const attachments = buildAlertAttachments(alert, status);
                
                // 스레드가 없으면 새 메시지 생성
                if (!threadTs) {
                    const data = await slackPostMessage(text, {
                        blocks: blocks,
                        attachments: attachments
                    });
                    threadTs = data.ts;
                    await storeSetTs(key, threadTs);
                    console.log(`🧵 새 스레드 생성: ${key} -> ${threadTs}`);
                } else {
                    // 기존 스레드에 답글
                    await slackPostMessage(text, {
                        blocks: blocks,
                        attachments: attachments,
                        threadTs: threadTs
                    });
                    console.log(`💬 스레드 답글: ${key} -> ${threadTs}`);
                }
                
                results.push({
                    key: key,
                    thread_ts: threadTs,
                    status: status,
                    alertname: alertname,
                    severity: severity
                });
                
            } catch (error) {
                console.error('알림 처리 실패:', error);
                results.push({
                    key: key || 'unknown',
                    error: error.message
                });
            }
        }
        
        res.json({
            ok: true,
            count: results.length,
            status: status,
            group_key: groupKey,
            thread_store: THREAD_STORE,
            results: results
        });
        
    } catch (error) {
        console.error('Webhook 처리 실패:', error);
        res.status(500).json({
            ok: false,
            error: error.message
        });
    }
});

app.get('/cache', (req, res) => {
    const threads = {};
    for (const [key, ts] of threadCache.entries()) {
        threads[key] = ts;
    }
    
    res.json({
        cached_threads: threadCache.size,
        threads: threads,
        thread_store: THREAD_STORE
    });
});

app.delete('/cache', (req, res) => {
    threadCache.clear();
    
    if (THREAD_STORE === 'redis' && redisClient) {
        // Redis에서 모든 스레드 키 삭제
        redisClient.keys(`${REDIS_KEY_PREFIX}:*`).then(keys => {
            if (keys.length > 0) {
                return redisClient.del(keys);
            }
        }).catch(error => {
            console.error('Redis 캐시 초기화 실패:', error);
        });
    }
    
    res.json({ message: '캐시가 초기화되었습니다' });
});

app.get('/stats', async (req, res) => {
    const stats = {
        cached_threads: threadCache.size,
        thread_store: THREAD_STORE,
        environment: ENVIRONMENT,
        uptime: new Date().toISOString()
    };
    
    if (THREAD_STORE === 'redis' && redisClient) {
        try {
            const info = await redisClient.info('server');
            const memory = await redisClient.info('memory');
            const stats_info = await redisClient.info('stats');
            
            stats.redis = {
                connected_clients: extractInfoValue(stats_info, 'connected_clients'),
                used_memory_human: extractInfoValue(memory, 'used_memory_human'),
                keyspace_hits: extractInfoValue(stats_info, 'keyspace_hits'),
                keyspace_misses: extractInfoValue(stats_info, 'keyspace_misses')
            };
        } catch (error) {
            stats.redis_error = error.message;
        }
    }
    
    res.json(stats);
});

function extractInfoValue(info, key) {
    const match = info.match(new RegExp(`${key}:(.+)`));
    return match ? match[1].trim() : '0';
}

// === 서버 시작 ===

async function startServer() {
    console.log('🚀 DreamSeed Alert Threader - Advanced (Node.js) 시작 중...');
    
    if (THREAD_STORE === 'redis') {
        await loadCacheRedis();
    } else {
        loadCacheFile();
    }
    
    console.log(`저장소: ${THREAD_STORE}`);
    console.log(`환경: ${ENVIRONMENT}`);
    console.log(`채널: ${SLACK_CHANNEL}`);
    
    app.listen(BIND_PORT, BIND_HOST, () => {
        console.log(`🌐 서버 시작됨: http://${BIND_HOST}:${BIND_PORT}`);
        console.log(`엔드포인트: POST /alert, GET /health, GET /stats`);
    });
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('🛑 서버 종료 중...');
    if (redisClient) {
        await redisClient.quit();
    }
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('🛑 서버 종료 중...');
    if (redisClient) {
        await redisClient.quit();
    }
    process.exit(0);
});

startServer().catch(error => {
    console.error('서버 시작 실패:', error);
    process.exit(1);
});

