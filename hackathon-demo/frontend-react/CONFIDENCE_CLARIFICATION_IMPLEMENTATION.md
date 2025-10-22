# Confidence-Based Clarification Implementation

## Overview

This document describes the implementation of the confidence-based clarification dialog feature for the Multi-Agent Orchestration System. This feature allows the system to detect low-confidence agent outputs and prompt users for additional information to improve accuracy.

## Implementation Summary

### Components Created

1. **ClarificationDialog.tsx** - Main dialog component for collecting clarifications
   - Displays low confidence fields with current values
   - Shows confidence score badges
   - Provides targeted clarification questions
   - Includes textarea for user input
   - Has "Submit Clarification" and "Skip" buttons

2. **confidence-utils.ts** - Utility functions for confidence detection
   - `extractLowConfidenceFields()` - Extracts fields with confidence < threshold
   - `generateClarificationQuestion()` - Generates agent-specific questions
   - `hasLowConfidence()` - Checks if any outputs have low confidence
   - `formatEnhancedText()` - Formats clarifications into enhanced text

3. **UI Components**
   - `label.tsx` - Label component for form fields
   - `textarea.tsx` - Textarea component for multi-line input

### Integration Points

#### IngestionPanel.tsx
- Added state management for clarification flow
- Integrated confidence detection after job completion
- Implemented clarification submission handler
- Added 3-round limit for clarification attempts
- Re-submits report with enhanced context

#### QueryPanel.tsx
- Added state management for clarification flow
- Integrated confidence detection after query completion
- Implemented clarification submission handler
- Added 3-round limit for clarification attempts
- Re-submits query with enhanced context

## Features

### Confidence Detection
- Monitors agent outputs during execution
- Collects confidence scores from status updates
- Checks confidence threshold (default: 0.9)
- Identifies low-confidence fields automatically

### Targeted Questions
The system generates specific clarification questions based on agent type:

- **Geo Agent**: "Which [location] are you referring to? Please provide city, cross streets, or nearby landmarks."
- **Temporal Agent**: "When exactly did this occur? Please provide a specific date and time."
- **Entity Agent**: "Can you provide more details about [category]? What specific type or characteristics?"
- **Generic**: "Please provide more details to improve the accuracy of this information."

### Clarification Flow

1. User submits report/query
2. System processes with agents
3. Agents complete with confidence scores
4. System detects low confidence (< 0.9)
5. ClarificationDialog appears with targeted questions
6. User provides additional details or skips
7. System re-submits with enhanced context
8. Process repeats up to 3 times
9. Final results displayed

### Enhanced Text Format

When user provides clarifications, they are appended to the original text:

```
[Original text]

Additional details:
location: Main Street near 5th Avenue
time: around 3pm yesterday
```

## Configuration

### Confidence Threshold
Default threshold is 0.9 (90% confidence). Can be adjusted in the code:

```typescript
const lowConfFields = extractLowConfidenceFields(agentOutputs, 0.9);
```

### Maximum Clarification Rounds
Default is 3 rounds. Controlled by:

```typescript
if (lowConfFields.length > 0 && clarificationRound < 3) {
  // Show clarification dialog
}
```

## User Experience

### Dialog Appearance
- Modal dialog with dark mode styling
- Clear indication of low confidence with red badges
- Shows current values for context
- Provides specific questions for each field
- Non-blocking - user can skip if desired

### Skip Behavior
- User can proceed with low confidence results
- System shows toast: "Processing complete (with low confidence)"
- Results are still displayed/saved

### Success Behavior
- After clarification, system re-processes automatically
- User sees updated execution status
- Higher confidence results displayed
- Success toast shown when complete

## Technical Details

### State Management
Each panel maintains:
- `originalText/originalQuestion` - Original user input
- `clarificationRound` - Current round counter (0-3)
- `lowConfidenceFields` - Array of fields needing clarification
- `showClarification` - Dialog visibility state
- `agentOutputs` - Collected agent outputs with confidence

### Agent Output Format
```typescript
{
  agent_name: string;
  output: {
    confidence: number;
    // ... other fields
  };
}
```

### Low Confidence Field Format
```typescript
{
  agentName: string;
  fieldName: string;
  currentValue: any;
  confidence: number;
  question: string;
}
```

## Testing

### Manual Testing Scenarios

1. **Low Confidence Location**
   - Submit: "There was an incident on Main Street"
   - Expected: Clarification dialog asks which Main Street
   - Provide: "Main Street in downtown near City Hall"
   - Expected: Re-processes with higher confidence

2. **Low Confidence Time**
   - Submit: "The incident happened yesterday"
   - Expected: Clarification dialog asks for specific time
   - Provide: "Yesterday around 3pm"
   - Expected: Re-processes with specific timestamp

3. **Multiple Low Confidence Fields**
   - Submit: "There was an incident somewhere yesterday"
   - Expected: Dialog shows multiple clarification fields
   - Provide details for each
   - Expected: Re-processes with all clarifications

4. **Skip Clarification**
   - Submit report with ambiguous info
   - Expected: Clarification dialog appears
   - Click "Skip"
   - Expected: Results shown with low confidence warning

5. **Maximum Rounds**
   - Submit report with very ambiguous info
   - Provide clarifications 3 times
   - Expected: After 3rd round, no more clarification prompts

## Future Enhancements

1. **Smart Question Generation**
   - Use LLM to generate more contextual questions
   - Analyze original text for better prompts

2. **Confidence Visualization**
   - Show confidence trends across rounds
   - Highlight which fields improved

3. **Partial Clarification**
   - Allow users to clarify only some fields
   - Skip individual fields instead of all

4. **Clarification History**
   - Show previous clarifications in dialog
   - Allow editing of previous responses

5. **Adaptive Threshold**
   - Adjust threshold based on agent type
   - Learn from user skip patterns

## Requirements Satisfied

This implementation satisfies all requirements from the specification:

- ✅ 19.1: Detect low confidence in ingestion agents
- ✅ 19.2: Detect low confidence in query agents
- ✅ 19.3: Identify specific low-confidence fields
- ✅ 19.4: Generate targeted follow-up questions
- ✅ 19.5: Display clarification dialog with questions
- ✅ 19.6: Re-process with additional context
- ✅ 19.7: Continue until confidence >= 0.9
- ✅ 19.8: Allow users to skip clarification
- ✅ 19.9: Display confidence scores in dialog

## Files Modified/Created

### Created
- `infrastructure/frontend/components/ClarificationDialog.tsx`
- `infrastructure/frontend/lib/confidence-utils.ts`
- `infrastructure/frontend/components/ui/label.tsx`
- `infrastructure/frontend/components/ui/textarea.tsx`
- `infrastructure/frontend/lib/__tests__/confidence-utils.test.ts`
- `infrastructure/frontend/CONFIDENCE_CLARIFICATION_IMPLEMENTATION.md`

### Modified
- `infrastructure/frontend/components/IngestionPanel.tsx`
- `infrastructure/frontend/components/QueryPanel.tsx`

## Conclusion

The confidence-based clarification dialog feature is now fully implemented and integrated into both the ingestion and query flows. The system can automatically detect low-confidence agent outputs and guide users to provide additional information, resulting in more accurate data processing and analysis.
