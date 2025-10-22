'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ClarificationQuestion, buildRefinedQuery } from '@/lib/query-utils';

interface QueryClarificationPanelProps {
  query: string;
  questions: ClarificationQuestion[];
  onSubmit: (refinedQuery: string) => void;
  onSkip: () => void;
}

export const QueryClarificationPanel: React.FC<QueryClarificationPanelProps> = ({
  query,
  questions,
  onSubmit,
  onSkip
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleAnswerChange = (field: string, value: string) => {
    setAnswers(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = () => {
    const refinedQuery = buildRefinedQuery(query, answers);
    onSubmit(refinedQuery);
  };

  const canSubmit = questions
    .filter(q => q.required)
    .every(q => answers[q.field]);

  return (
    <Card className="border-primary/50">
      <CardHeader>
        <CardTitle className="text-lg">Clarify Your Question</CardTitle>
        <CardDescription>
          Your question: <span className="italic text-foreground">&quot;{query}&quot;</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Please provide more details to help us give you better results:
        </p>

        <div className="space-y-3">
          {questions.map(question => (
            <div key={question.field} className="space-y-2">
              <label className="text-sm font-medium">
                {question.question}
                {question.required && <span className="text-destructive ml-1">*</span>}
              </label>
              
              {question.options ? (
                <Select
                  value={answers[question.field] || ''}
                  onValueChange={(value) => handleAnswerChange(question.field, value)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select an option..." />
                  </SelectTrigger>
                  <SelectContent>
                    {question.options.map(option => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <input
                  type="text"
                  value={answers[question.field] || ''}
                  onChange={(e) => handleAnswerChange(question.field, e.target.value)}
                  placeholder="Enter your answer..."
                  className="w-full px-3 py-2 border rounded-md bg-background text-foreground"
                />
              )}
            </div>
          ))}
        </div>

        <div className="flex gap-2 pt-2">
          <Button 
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex-1"
          >
            Submit Query
          </Button>
          <Button 
            variant="outline" 
            onClick={onSkip}
            className="flex-1"
          >
            Skip (use as-is)
          </Button>
        </div>

        {Object.keys(answers).length > 0 && (
          <div className="mt-4 p-3 bg-muted rounded-md">
            <p className="text-xs font-medium text-muted-foreground mb-1">
              Refined query preview:
            </p>
            <p className="text-sm italic">
              &quot;{buildRefinedQuery(query, answers)}&quot;
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
