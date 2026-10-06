import { Skeleton } from 'primereact/skeleton';

const LoadingPage = () => {
  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="mb-3">
        <Skeleton height="1.75rem" width="10rem" />
      </div>
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        <Skeleton height="35rem" />
      </div>
    </div>
  );
};

export default LoadingPage;
