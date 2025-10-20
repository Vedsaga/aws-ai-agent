'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

export interface LowConfidenceField {
  agentName: string;
  fieldName: string;
  currentValue: any;
  confidence: number;
  question: string;
}

interface ClarificationDialogProps {
  isOpen: boolean;
  jobId: string;
  lowConfidenceFields: LowConfidenceField[];
  onSubmit: (clarifications: Record<string, string>) => void;
  onSkip: () => void;
}

export default function ClarificationDialog({
  isOpen,
  jobId,
  lowConfidenceFields,
  onSubmit,
  onSkip,
}: ClarificationDialogProps) {
  const [clarifications, setClarifications] = useState<Record<string, string>>({});

  const handleSubmit = () => {
    onSubmit(clarifications);
    // Reset clarifications after submit
    setClarifications({});
  };

  const handleSkip = () => {
    onSkip();
    // Reset clarifications after skip
    setClarifications({});
  };

  const handleClarificationChange = (fieldName: string, value: string) => {
    setClarifications((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Additional Information Needed</DialogTitle>
          <DialogDescription>
            Some fields have low confidence. Please provide additional details to improve accuracy.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {lowConfidenceFields.map((field, idx) => (
            <div key={idx} className="border rounded-lg p-4 bg-card">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium text-foreground">{field.agentName}</div>
                <Badge variant="destructive">
                  {(field.confidence * 100).toFixed(0)}% confidence
                </Badge>
              </div>

              <div className="text-sm text-muted-foreground mb-2">
                Current value:{' '}
                <span className="font-mono bg-muted px-1 py-0.5 rounded">
                  {typeof field.currentValue === 'object'
                    ? JSON.stringify(field.currentValue)
                    : String(field.currentValue)}
                </span>
              </div>

              <div className="mb-2">
                <Label htmlFor={`clarification-${idx}`} className="text-foreground">
                  {field.question}
                </Label>
              </div>

              <Textarea
                id={`clarification-${idx}`}
                value={clarifications[field.fieldName] || ''}
                onChange={(e) => handleClarificationChange(field.fieldName, e.target.value)}
                placeholder="Provide more details..."
                rows={3}
                className="bg-background text-foreground"
              />
            </div>
          ))}
        </div>

        <DialogFooter className="flex gap-2">
          <Button variant="outline" onClick={handleSkip}>
            Skip (Proceed with low confidence)
          </Button>
          <Button onClick={handleSubmit}>Submit Clarification</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
