#!/usr/bin/env node
/**
 * DreamSeed Alertmanager Slack Threader
 * Alertmanager webhook을 받아서 Slack Bot API로 스레드 메시지를 전송하는 래퍼 서비스
 */

const express = require('express');
const fetch = require('node-fetch');

// 환경 변수
const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN;
const SLACK_CHANNEL = process.env.SLACK_CHANNEL;
const ENVIRONMENT = process.env.ENVIRONMENT || 'staging';
const BIND_HOST = process.env.BIND_HOST || '0.0.0.0';
const BIND_PORT = parseInt(process.env.BIND_PORT || '9009');

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

// 스레드 캐시 (실제 운영에서는 Redis나 파일 저장 권장)
const threadCache = new Map();

/**
 * 알림의 스레드 키를 생성합니다
 */
function threadKey(alert) {
    const name = alert.labels?.alertname || 'unknown';
    const severity = alert.labels?.severity || 'info';
    const service = alert.labels?.service || 'unknown';
    return `${name}|${severity}|${service}|${ENVIRONMENT}`;
}

/**
 * 심각도에 따른 이모지를 반환합니다
 */
function getEmoji(severity) {
    const emojiMap = {
        'critical': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️',
        'error': '❌',
        'success': '✅'
    };
    return emojiMap[severity.toLowerCase()] || '📢';
}

/**
 * 심각도에 따른 색상을 반환합니다
 */
function getColor(severity) {
    const colorMap = {
        'critical': '#E01E5A',
        'warning': '#ECB22E',
        'info': '#2EB67D',
        'error': '#E01E5A',
        'success': '#2EB67D'
    };
    return colorMap[severity.toLowerCase()] || '#2EB67D';
}

/**
 * Slack API로 메시지를 전송합니다
 */
async function postSlack(text, threadTs = null, blocks = null) {
    const payload = {
        channel: SLACK_CHANNEL,
        text: text,
        unfurl_links: false,
        unfurl_media: false
    };
    
    if (threadTs) {
        payload.thread_ts = threadTs;
    }
    
    if (blocks) {
        payload.blocks = blocks;
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

/**
 * 알림 메시지를 포맷팅합니다
 */
function formatAlertMessage(alert, status) {
    const labels = alert.labels || {};
    const annotations = alert.annotations || {};
    
    const alertname = labels.alertname || 'Unknown';
    const severity = labels.severity || 'info';
    const service = labels.service || 'unknown';
    const summary = annotations.summary || alertname;
    const description = annotations.description || '';
    
    const emoji = getEmoji(severity);
    
    // 상태에 따른 메시지 포맷
    let text;
    if (status === 'resolved') {
        text = `*[${ENVIRONMENT}]* ✅ **RESOLVED** - ${summary}`;
    } else {
        text = `*[${ENVIRONMENT}]* ${emoji} **${summary}** (\`${severity}\`)`;
    }
    
    // Slack Block Kit 포맷
    const blocks = [
        {
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: text
            }
        }
    ];
    
    if (description) {
        blocks.push({
            type: 'section',
            text: {
                type: 'mrkdwn',
                text: `*설명:* ${description}`
            }
        });
    }
    
    // 라벨 정보
    const labelKeys = ['alertname', 'severity', 'service', 'instance'];
    const labelText = labelKeys
        .filter(key => labels[key])
        .map(key => `\`${key}=${labels[key]}\``)
        .join(' | ');
    
    if (labelText) {
        blocks.push({
            type: 'context',
            elements: [
                {
                    type: 'mrkdwn',
                    text: `*라벨:* ${labelText}`
                }
            ]
        });
    }
    
    return { text, blocks };
}

// 헬스체크 엔드포인트
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        environment: ENVIRONMENT,
        channel: SLACK_CHANNEL,
        cached_threads: threadCache.size
    });
});

// Alertmanager webhook 엔드포인트
app.post('/alert', async (req, res) => {
    try {
        const { status, alerts = [], groupKey = '' } = req.body;
        
        console.log(`📨 Received ${alerts.length} alerts with status: ${status}`);
        
        const results = [];
        
        for (const alert of alerts) {
            try {
                const key = threadKey(alert);
                let threadTs = threadCache.get(key);
                
                const { text, blocks } = formatAlertMessage(alert, status);
                
                // 스레드가 없으면 새 메시지 생성
                if (!threadTs) {
                    const data = await postSlack(text, null, blocks);
                    threadTs = data.ts;
                    threadCache.set(key, threadTs);
                    console.log(`🧵 새 스레드 생성: ${key} -> ${threadTs}`);
                } else {
                    // 기존 스레드에 답글
                    await postSlack(text, threadTs, blocks);
                    console.log(`💬 스레드 답글: ${key} -> ${threadTs}`);
                }
                
                results.push({
                    key,
                    thread_ts: threadTs,
                    status,
                    alertname: alert.labels?.alertname || 'unknown'
                });
                
            } catch (error) {
                console.error('알림 처리 실패:', error);
                results.push({
                    key: threadKey(alert),
                    error: error.message
                });
            }
        }
        
        res.json({
            ok: true,
            count: results.length,
            status,
            group_key: groupKey,
            results
        });
        
    } catch (error) {
        console.error('Webhook 처리 실패:', error);
        res.status(500).json({
            ok: false,
            error: error.message
        });
    }
});

// 캐시 상태 조회 (디버깅용)
app.get('/cache', (req, res) => {
    const threads = {};
    for (const [key, ts] of threadCache.entries()) {
        threads[key] = ts;
    }
    
    res.json({
        cached_threads: threadCache.size,
        threads
    });
});

// 캐시 초기화 (디버깅용)
app.delete('/cache', (req, res) => {
    threadCache.clear();
    res.json({ message: '캐시가 초기화되었습니다' });
});

// 서버 시작
app.listen(BIND_PORT, BIND_HOST, () => {
    console.log(`🚀 DreamSeed Alert Threader 시작됨`);
    console.log(`   환경: ${ENVIRONMENT}`);
    console.log(`   채널: ${SLACK_CHANNEL}`);
    console.log(`   주소: http://${BIND_HOST}:${BIND_PORT}`);
    console.log(`   엔드포인트: POST /alert, GET /health`);
});

