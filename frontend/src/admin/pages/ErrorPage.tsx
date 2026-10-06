import { isAxiosError } from 'axios';
import { Button } from 'primereact/button';
import {
  isRouteErrorResponse,
  useLocation,
  useNavigate,
  useRouteError,
} from 'react-router';

const errorTranslation = {
  401: {
    message:
      'Az oldal megtekintéséhez be kell jelentkezned. Lehet, hogy a korábbi munkameneted lejárt.',
    statusText: 'Bejelentkezés szükséges',
  },
  404: {
    message:
      'Az általad keresett oldal nem létezik. Lehet, hogy törlésre került, megváltozott a címe vagy ideiglenesen nem elérhető.',
    statusText: 'Az oldal nem található',
  },
};

const ErrorPage = () => {
  const { state } = useLocation();
  const error = useRouteError();
  const navigate = useNavigate();

  let message = '';
  let statusCode = 'HIBA';
  let statusText = '';

  if (isRouteErrorResponse(error)) {
    statusCode = error.status.toString();
    if (error.status == 404) {
      ({ message, statusText } = errorTranslation[error.status]);
    } else {
      message = error.data;
      statusText = error.statusText;
    }
  } else if (isAxiosError(error) && error.response) {
    statusCode = error.response.status.toString();
    if (error.response.status == 401) {
      // eslint-disable-next-line react-hooks/immutability
      window.location.href = '/';
    } else if (error.response.status == 404) {
      ({ message, statusText } = errorTranslation[error.response.status]);
    } else {
      statusText = error.response.statusText;
    }
  } else if (!error && state) {
    ({ statusCode, statusText } = state);
    if (Number(statusCode) == 404) {
      ({ message, statusText } = errorTranslation[404]);
    }
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
            {statusCode}
          </span>
        </div>
        <div className="font-bold mb-5 mt-6 text-6xl text-900 text-center">
          {statusText}
        </div>
        <p className="mb-6 mt-0 text-3xl text-700 text-center">{message}</p>
        <div className="text-center">
          <Button
            className="p-button-text mr-2"
            icon="pi pi-arrow-left"
            label="Vissza"
            onClick={() => {
              void navigate(-1);
            }}
          />
          <Button
            icon="pi pi-home"
            label="Ugrás a Kezdőoldalra"
            onClick={() => {
              void navigate('/', { replace: true });
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default ErrorPage;
