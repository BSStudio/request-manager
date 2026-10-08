import { Button } from 'primereact/button';
import { InputTextarea } from 'primereact/inputtextarea';

import { crashFeedbackText, useCrashFeedback } from 'hooks/useCrashFeedback';

type CrashFeedbackProps = {
  eventId: string;
};

const CrashFeedback = ({ eventId }: CrashFeedbackProps) => {
  const { feedback, message, setMessage, submit } = useCrashFeedback(eventId);

  if (feedback.isSuccess) {
    return (
      <p className="m-0 text-700 text-center" role="status">
        {crashFeedbackText.thanks}
      </p>
    );
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <label className="block font-medium" htmlFor="crash-feedback">
        {crashFeedbackText.label}
      </label>
      <small className="block mb-2 mt-1 text-600" id="crash-feedback-hint">
        {crashFeedbackText.hint}
      </small>
      <InputTextarea
        aria-describedby="crash-feedback-hint"
        autoResize
        className="w-full"
        id="crash-feedback"
        onChange={(event) => setMessage(event.target.value)}
        readOnly={feedback.isPending}
        rows={3}
        value={message}
      />
      {feedback.isError && (
        <small className="block p-error" role="alert">
          {crashFeedbackText.error}
        </small>
      )}
      <div className="flex justify-content-end mt-2">
        <Button
          disabled={!message.trim()}
          icon="pi pi-send"
          label={crashFeedbackText.send}
          loading={feedback.isPending}
          type="submit"
        />
      </div>
    </form>
  );
};

export default CrashFeedback;
