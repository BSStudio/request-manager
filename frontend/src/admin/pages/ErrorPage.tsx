import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import {
  isRouteErrorResponse,
  useLocation,
  useNavigate,
  useRouteError,
} from 'react-router';

import CrashFeedback from 'admin/components/CrashFeedback';
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

  const eventId = useReportRouteError(error);

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
        {eventId && (
          <div className="max-w-30rem mt-6 mx-auto">
            <CrashFeedback eventId={eventId} key={eventId} />
          </div>
        )}
      </div>
    </div>
  );
};

export default ErrorPage;
