import { describe, it, expect } from '@jest/globals';
import {
  extractLowConfidenceFields,
  generateClarificationQuestion,
  hasLowConfidence,
  formatEnhancedText,
} from '../confidence-utils';

describe('confidence-utils', () => {
  describe('extractLowConfidenceFields', () => {
    it('should extract fields with confidence below threshold', () => {
      const agentOutputs = [
        {
          agent_name: 'Geo Agent',
          output: {
            confidence: 0.65,
            location_name: 'Main Street',
          },
        },
        {
          agent_name: 'Temporal Agent',
          output: {
            confidence: 0.95,
            timestamp: '2024-01-01',
          },
        },
      ];

      const result = extractLowConfidenceFields(agentOutputs, 0.9);

      expect(result).toHaveLength(1);
      expect(result[0].agentName).toBe('Geo Agent');
      expect(result[0].confidence).toBe(0.65);
    });

    it('should return empty array when all confidence is above threshold', () => {
      const agentOutputs = [
        {
          agent_name: 'Geo Agent',
          output: {
            confidence: 0.95,
          },
        },
      ];

      const result = extractLowConfidenceFields(agentOutputs, 0.9);

      expect(result).toHaveLength(0);
    });

    it('should handle empty or invalid inputs', () => {
      expect(extractLowConfidenceFields([], 0.9)).toHaveLength(0);
      expect(extractLowConfidenceFields(null as any, 0.9)).toHaveLength(0);
      expect(extractLowConfidenceFields([null, undefined] as any, 0.9)).toHaveLength(0);
    });
  });

  describe('generateClarificationQuestion', () => {
    it('should generate location clarification for Geo Agent', () => {
      const question = generateClarificationQuestion('Geo Agent', {
        location_name: 'Main Street',
        confidence: 0.6,
      });

      expect(question).toContain('Main Street');
      expect(question).toContain('city');
    });

    it('should generate time clarification for Temporal Agent', () => {
      const question = generateClarificationQuestion('Temporal Agent', {
        timestamp: 'yesterday',
        confidence: 0.7,
      });

      expect(question).toContain('When exactly');
      expect(question).toContain('yesterday');
    });

    it('should generate category clarification for Entity Agent', () => {
      const question = generateClarificationQuestion('Entity Agent', {
        category: 'incident',
        confidence: 0.65,
      });

      expect(question).toContain('incident');
      expect(question).toContain('details');
    });

    it('should generate generic clarification for unknown agents', () => {
      const question = generateClarificationQuestion('Unknown Agent', {
        confidence: 0.5,
      });

      expect(question).toContain('more details');
    });
  });

  describe('hasLowConfidence', () => {
    it('should return true when low confidence exists', () => {
      const agentOutputs = [
        {
          agent_name: 'Geo Agent',
          output: {
            confidence: 0.65,
          },
        },
      ];

      expect(hasLowConfidence(agentOutputs, 0.9)).toBe(true);
    });

    it('should return false when all confidence is high', () => {
      const agentOutputs = [
        {
          agent_name: 'Geo Agent',
          output: {
            confidence: 0.95,
          },
        },
      ];

      expect(hasLowConfidence(agentOutputs, 0.9)).toBe(false);
    });
  });

  describe('formatEnhancedText', () => {
    it('should append clarifications to original text', () => {
      const originalText = 'There was an incident on Main Street';
      const clarifications = {
        location: 'Main Street near 5th Avenue',
        time: 'around 3pm',
      };

      const result = formatEnhancedText(originalText, clarifications);

      expect(result).toContain(originalText);
      expect(result).toContain('Additional details:');
      expect(result).toContain('Main Street near 5th Avenue');
      expect(result).toContain('around 3pm');
    });

    it('should return original text when no clarifications provided', () => {
      const originalText = 'There was an incident';
      const result = formatEnhancedText(originalText, {});

      expect(result).toBe(originalText);
    });

    it('should filter out empty clarifications', () => {
      const originalText = 'There was an incident';
      const clarifications = {
        location: 'Main Street',
        time: '',
        category: '   ',
      };

      const result = formatEnhancedText(originalText, clarifications);

      expect(result).toContain('Main Street');
      expect(result).not.toContain('time:');
      expect(result).not.toContain('category:');
    });
  });
});
