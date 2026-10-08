import { cn } from 'cn';
import { Loader2Icon, SendIcon } from 'lucide-react';

import { crashFeedbackText, useCrashFeedback } from 'hooks/useCrashFeedback';
import { outlineOnInk } from 'site/components/NoSignal';
import { Button } from 'site/components/ui/button';
import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from 'site/components/ui/field';
import { Textarea } from 'site/components/ui/textarea';

export default function CrashFeedback({ eventId }: { eventId: string }) {
  const { feedback, message, setMessage, submit } = useCrashFeedback(eventId);

  if (feedback.isSuccess) {
    return (
      <p className="text-sm text-white/70" role="status">
        {crashFeedbackText.thanks}
      </p>
    );
  }

  return (
    <form
      className="text-left"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <Field>
        <FieldLabel htmlFor="crash-feedback">
          {crashFeedbackText.label}
        </FieldLabel>
        <FieldDescription className="text-white/60" id="crash-feedback-hint">
          {crashFeedbackText.hint}
        </FieldDescription>
        <Textarea
          aria-describedby="crash-feedback-hint"
          className="min-h-24 resize-none border-white/20 dark:bg-white/5"
          id="crash-feedback"
          onChange={(event) => setMessage(event.target.value)}
          readOnly={feedback.isPending}
          value={message}
        />
        {feedback.isError && <FieldError>{crashFeedbackText.error}</FieldError>}
      </Field>
      <Button
        className={cn('mt-3 w-full', outlineOnInk)}
        disabled={feedback.isPending || !message.trim()}
        type="submit"
        variant="outline"
      >
        {feedback.isPending ? (
          <Loader2Icon className="animate-spin" data-icon="inline-start" />
        ) : (
          <SendIcon data-icon="inline-start" />
        )}
        {crashFeedbackText.send}
      </Button>
    </form>
  );
}
