import { LowConfidenceField } from '@/components/ClarificationDialog';

/**
 * Extract low confidence fields from agent outputs
 * @param agentOutputs - Array of agent outputs with confidence scores
 * @param threshold - Confidence threshold (default: 0.9)
 * @returns Array of low confidence fields
 */
export function extractLowConfidenceFields(
  agentOutputs: any[],
  threshold: number = 0.9
): LowConfidenceField[] {
  const fields: LowConfidenceField[] = [];

  if (!agentOutputs || !Array.isArray(agentOutputs)) {
    return fields;
  }

  for (const agentOutput of agentOutputs) {
    if (!agentOutput || typeof agentOutput !== 'object') {
      continue;
    }

    const agentName = agentOutput.agent_name || agentOutput.agentName || 'Unknown Agent';
    const output = agentOutput.output || agentOutput;
    const confidence = output.confidence;

    // Check if confidence exists and is below threshold
    if (typeof confidence === 'number' && confidence < threshold) {
      // Generate clarification question based on agent type
      const question = generateClarificationQuestion(agentName, output);

      fields.push({
        agentName,
        fieldName: agentName.toLowerCase().replace(/\s+/g, '_'),
        currentValue: output,
        confidence,
        question,
      });
    }
  }

  return fields;
}

/**
 * Generate targeted clarification question based on agent type and output
 * @param agentName - Name of the agent
 * @param output - Agent output data
 * @returns Clarification question string
 */
export function generateClarificationQuestion(agentName: string, output: any): string {
  const agentNameLower = agentName.toLowerCase();

  // Geo Agent - location clarification
  if (agentNameLower.includes('geo') || agentNameLower.includes('location')) {
    const locationName = output.location_name || output.locationName || 'the location';
    return `Which "${locationName}" are you referring to? Please provide city, cross streets, or nearby landmarks.`;
  }

  // Temporal Agent - time clarification
  if (agentNameLower.includes('temporal') || agentNameLower.includes('time') || agentNameLower.includes('when')) {
    const timeValue = output.timestamp || output.time || output.date || 'the time';
    return `When exactly did this occur? Please provide a specific date and time. Current value: ${timeValue}`;
  }

  // Entity Agent - category clarification
  if (agentNameLower.includes('entity') || agentNameLower.includes('category')) {
    const category = output.category || output.entity_type || 'the category';
    return `Can you provide more details about "${category}"? What specific type or characteristics?`;
  }

  // Generic clarification for other agents
  return `Please provide more details to improve the accuracy of this information.`;
}

/**
 * Check if any agent outputs have low confidence
 * @param agentOutputs - Array of agent outputs
 * @param threshold - Confidence threshold (default: 0.9)
 * @returns True if any outputs have low confidence
 */
export function hasLowConfidence(agentOutputs: any[], threshold: number = 0.9): boolean {
  return extractLowConfidenceFields(agentOutputs, threshold).length > 0;
}

/**
 * Format clarifications into enhanced text
 * @param originalText - Original input text
 * @param clarifications - Map of field names to clarification text
 * @returns Enhanced text with clarifications appended
 */
export function formatEnhancedText(
  originalText: string,
  clarifications: Record<string, string>
): string {
  const clarificationEntries = Object.entries(clarifications).filter(([_, value]) => value.trim());

  if (clarificationEntries.length === 0) {
    return originalText;
  }

  const clarificationText = clarificationEntries
    .map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`)
    .join('\n');

  return `${originalText}\n\nAdditional details:\n${clarificationText}`;
}
