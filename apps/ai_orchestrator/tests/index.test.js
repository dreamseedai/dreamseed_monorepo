const request = require('supertest');
const app = require('../src/index');

describe('AI Orchestrator Service', () => {
  
  describe('POST /ai/assist', () => {
    
    test('should select korean-llm for Korean language', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          language: 'ko',
          message: '안녕하세요'
        });

      expect(response.status).toBe(200);
      expect(response.body.model).toBe('korean-llm');
      expect(response.body.language).toBe('ko');
      expect(response.body.message).toBe('안녕하세요');
      expect(response.body.status).toBe('processed');
    });

    test('should select deepseek for Chinese language', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          language: 'zh',
          message: '你好'
        });

      expect(response.status).toBe(200);
      expect(response.body.model).toBe('deepseek');
      expect(response.body.language).toBe('zh');
      expect(response.body.message).toBe('你好');
    });

    test('should select gpt-4o-mini for English language', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          language: 'en',
          message: 'Hello world'
        });

      expect(response.status).toBe(200);
      expect(response.body.model).toBe('gpt-4o-mini');
      expect(response.body.language).toBe('en');
    });

    test('should select gpt-4o-mini for unknown language', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          language: 'fr',
          message: 'Bonjour'
        });

      expect(response.status).toBe(200);
      expect(response.body.model).toBe('gpt-4o-mini');
      expect(response.body.language).toBe('fr');
    });

    test('should default to gpt-4o-mini when no language provided', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          message: 'Hello world'
        });

      expect(response.status).toBe(200);
      expect(response.body.model).toBe('gpt-4o-mini');
      expect(response.body.language).toBe('en');
    });

    test('should return 400 when message is missing', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          language: 'en'
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toBe('Message is required');
    });

    test('should handle case-insensitive language codes', async () => {
      const response = await request(app)
        .post('/ai/assist')
        .send({
          language: 'KO',
          message: 'test'
        });

      expect(response.status).toBe(200);
      expect(response.body.model).toBe('korean-llm');
    });

  });

  describe('GET /health', () => {
    
    test('should return health status', async () => {
      const response = await request(app)
        .get('/health');

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('healthy');
      expect(response.body.service).toBe('ai-orchestrator');
      expect(response.body.timestamp).toBeDefined();
    });

  });

});