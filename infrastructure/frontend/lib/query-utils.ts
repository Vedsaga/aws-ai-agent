/**
 * Query Clarification Utilities
 * 
 * Provides functions to detect ambiguous queries and generate clarification questions
 * to help users refine their queries before submission.
 */

export interface ClarificationQuestion {
  field: string;
  question: string;
  options?: string[];
  required: boolean;
}

/**
 * Checks if a query needs clarification based on ambiguous patterns
 * 
 * @param query - The user's query string
 * @returns boolean indicating if clarification is needed
 */
export const needsClarification = (query: string): boolean => {
  if (!query || query.trim().length === 0) {
    return false;
  }

  const normalizedQuery = query.trim().toLowerCase();

  // Patterns that indicate ambiguous queries
  const ambiguousPatterns = [
    /^show me/i,                    // "show me" without specifics
    /^what('s| is)/i,               // "what's" or "what is" without context
    /^how many$/i,                  // "how many" without subject
    /^where$/i,                     // "where" alone
    /complaints?$/i,                // Ends with "complaint(s)" only
    /^tell me about/i,              // "tell me about" without specifics
    /^give me/i,                    // "give me" without specifics
    /^list/i,                       // "list" without specifics
  ];

  // Check if query matches any ambiguous pattern
  const matchesAmbiguousPattern = ambiguousPatterns.some(pattern => 
    pattern.test(normalizedQuery)
  );

  if (matchesAmbiguousPattern) {
    return true;
  }

  // Check if query is very short (less than 5 words) and lacks specificity
  const wordCount = normalizedQuery.split(/\s+/).length;
  if (wordCount < 5) {
    // Check if it lacks category, location, or time context
    const hasCategory = /pothole|street light|sidewalk|trash|flooding|fire|damage|repair/i.test(normalizedQuery);
    const hasLocation = /in|at|near|downtown|neighborhood|area|zone|district|street|avenue/i.test(normalizedQuery);
    const hasTime = /today|yesterday|week|month|year|recent|last|this|past/i.test(normalizedQuery);

    // If it lacks at least 2 of these contexts, it needs clarification
    const contextCount = [hasCategory, hasLocation, hasTime].filter(Boolean).length;
    if (contextCount < 2) {
      return true;
    }
  }

  return false;
};

/**
 * Generates clarification questions based on what's missing from the query
 * 
 * @param query - The user's query string
 * @returns Array of clarification questions
 */
export const getClarificationQuestions = (query: string): ClarificationQuestion[] => {
  const questions: ClarificationQuestion[] = [];
  const normalizedQuery = query.toLowerCase();

  // Check for missing category
  const hasCategory = /pothole|street light|sidewalk|trash|flooding|fire|damage|repair/i.test(query);
  if (!hasCategory) {
    questions.push({
      field: 'category',
      question: 'What type of complaints are you interested in?',
      options: ['All', 'Potholes', 'Street Lights', 'Sidewalks', 'Trash', 'Flooding', 'Fire'],
      required: false
    });
  }

  // Check for missing location
  const hasLocation = /in|at|near|downtown|neighborhood|area|zone|district|street|avenue/i.test(query);
  if (!hasLocation) {
    questions.push({
      field: 'location',
      question: 'Which area are you asking about?',
      options: ['All', 'Downtown', 'North Side', 'South Side', 'East End', 'West End'],
      required: false
    });
  }

  // Check for missing time range
  const hasTime = /today|yesterday|week|month|year|recent|last|this|past/i.test(query);
  if (!hasTime) {
    questions.push({
      field: 'time_range',
      question: 'What time period should we look at?',
      options: ['All time', 'Today', 'This week', 'This month', 'This year'],
      required: false
    });
  }

  return questions;
};

/**
 * Builds a refined query by appending clarification answers to the original query
 * 
 * @param originalQuery - The user's original query
 * @param answers - Map of field names to selected values
 * @returns Refined query string
 */
export const buildRefinedQuery = (
  originalQuery: string,
  answers: Record<string, string>
): string => {
  let refined = originalQuery.trim();

  // Add category filter
  if (answers.category && answers.category !== 'All') {
    refined += ` about ${answers.category.toLowerCase()}`;
  }

  // Add location filter
  if (answers.location && answers.location !== 'All') {
    refined += ` in ${answers.location}`;
  }

  // Add time range
  if (answers.time_range && answers.time_range !== 'All time') {
    refined += ` from ${answers.time_range.toLowerCase()}`;
  }

  return refined;
};
