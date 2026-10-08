import { useState } from 'react';

import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import { InputTextarea } from 'primereact/inputtextarea';
import {
  isRouteErrorResponse,
  useLocation,
  useNavigate,
  useRouteError,
} from 'react-router';

import { getErrorMessage } from 'admin/helpers/ErrorMessageProvider';
import { useReportRouteError } from 'hooks/useReportRouteError';

// Editor pages whose data fails to load navigate here with this state instead
// of throwing.
export type LoadErrorState = { message: string; status?: number };

const loggedOut = {
  message:
    'Az oldal megtekintéséhez be kell jelentkezned. Lehet, hogy a korábbi munkameneted lejárt.',
  title: 'Bejelentkezés szükséges',
};

const notFound = {
  message:
    'Az általad keresett oldal nem létezik. Lehet, hogy törlésre került, megváltozott a címe vagy ideiglenesen nem elérhető.',
  title: 'Az oldal nem található',
};

const unexpected = {
  message:
    'Töltsd újra az oldalt, és ha így sem működik, jelezd a hibát a fejlesztőknek.',
  title: 'Váratlan hiba történt',
};

const ErrorPage = () => {
  const { state } = useLocation() as { state: LoadErrorState | null };
  const error = useRouteError();
  const navigate = useNavigate();
  const [message, setMessage] = useState('');

  const { feedback, reported } = useReportRouteError(error);

  let status: number | undefined;
  let loadError: string | undefined;
  if (isRouteErrorResponse(error)) {
    status = error.status;
  } else if (isAxiosError(error)) {
    status = error.response?.status;
    loadError = getErrorMessage(error);
  } else if (!error && state) {
    ({ message: loadError, status } = state);
  }

  let text = unexpected;
  // The API client is already on its way to the login page.
  if (status === 401) text = loggedOut;
  else if (status === 404) text = notFound;
  else if (loadError) {
    text = { message: loadError, title: 'Nem sikerült betölteni az oldalt' };
  }

  return (
    <div className="flex flex-auto flex-column p-5">
      <div className="md:px-6 lg:px-8 px-4 py-8 surface-card">
        <div
          style={{
            background:
              'radial-gradient(50% 109137.91% at 50% 50%, rgba(233, 30, 99, 0.1) 0%, rgba(254, 244, 247, 0) 100%)',
          }}
          className="text-center"
        >
          <span className="font-bold inline-block px-3 text-2xl text-pink-500">
            {status ?? 'HIBA'}
          </span>
        </div>
        <div className="font-bold mb-5 mt-6 text-6xl text-900 text-center">
          {text.title}
        </div>
        <p className="mb-6 mt-0 text-3xl text-700 text-center">
          {text.message}
        </p>
        <div className="text-center">
          <Button
            className="p-button-text mr-2"
            icon="pi pi-arrow-left"
            label="Vissza"
            onClick={() => {
              void navigate(-1);
            }}
          />
          {text !== notFound && (
            <Button
              className="p-button-text mr-2"
              icon="pi pi-refresh"
              label="Újratöltés"
              onClick={() => window.location.reload()}
            />
          )}
          <Button
            icon="pi pi-home"
            label="Ugrás a kezdőlapra"
            onClick={() => {
              void navigate('/', { replace: true });
            }}
          />
        </div>
        {reported && (
          <div className="max-w-30rem mt-6 mx-auto">
            {feedback.isSuccess ? (
              <p className="m-0 text-700 text-center">
                Köszönjük, hogy segítesz kijavítani a hibát!
              </p>
            ) : (
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  if (message.trim()) feedback.mutate(message.trim());
                }}
              >
                <label className="block font-medium" htmlFor="crash-feedback">
                  Mit csináltál, amikor a hiba történt?
                </label>
                <small
                  className="block mb-2 mt-1 text-600"
                  id="crash-feedback-hint"
                >
                  Ha leírod, könnyebben megtaláljuk és kijavítjuk.
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
                    Nem sikerült elküldeni. Próbáld újra!
                  </small>
                )}
                <div className="flex justify-content-end mt-2">
                  <Button
                    disabled={!message.trim()}
                    icon="pi pi-send"
                    label="Küldés"
                    loading={feedback.isPending}
                    type="submit"
                  />
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ErrorPage;
