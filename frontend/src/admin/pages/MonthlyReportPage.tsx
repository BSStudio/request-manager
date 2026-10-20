import { useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import {
  endOfMonth,
  format,
  parseISO,
  startOfMonth,
  subMonths,
} from 'date-fns';
import { Button } from 'primereact/button';
import { Calendar } from 'primereact/calendar';
import { InputSwitch } from 'primereact/inputswitch';
import { ProgressBar } from 'primereact/progressbar';

import { reportQuery } from 'admin/api/queries';
import { useToast } from 'admin/providers/ToastProvider';
import { ReportItem } from 'api/models/report-item';
import { queryClient } from 'api/queryClient';

function lastMonth() {
  return startOfMonth(subMonths(new Date(), 1));
}

function monthRange(month: Date) {
  return [
    format(startOfMonth(month), 'yyyy-MM-dd'),
    format(endOfMonth(month), 'yyyy-MM-dd'),
  ] as const;
}

export async function loader() {
  return queryClient.query({
    ...reportQuery(...monthRange(lastMonth())),
    staleTime: 'static',
  });
}

type ReportListProps = {
  emptyMessage: string;
  items: ReportItem[];
  showDates: boolean;
  title: string;
};

const ReportList = ({
  emptyMessage,
  items,
  showDates,
  title,
}: ReportListProps) => {
  const { showToast } = useToast();
  const text = items
    .map((item) =>
      showDates
        ? `${format(parseISO(item.date), 'yyyy. MM. dd.')} ${item.title}`
        : item.title,
    )
    .join('\n');

  const copy = () => {
    void navigator.clipboard.writeText(text).then(() =>
      showToast({
        detail: `${title} a vágólapra másolva`,
        life: 3000,
        severity: 'info',
        summary: 'Információ',
      }),
    );
  };

  return (
    <section aria-label={title}>
      <div className="align-items-center flex justify-content-between mb-2">
        <h2 className="font-medium m-0 text-900 text-lg">
          {title} ({items.length})
        </h2>
        <Button
          disabled={!items.length}
          icon="pi pi-copy"
          label="Másolás"
          onClick={copy}
          size="small"
          text
        />
      </div>
      {items.length ? (
        <div
          className="border-round line-height-3 p-3 surface-ground"
          style={{ whiteSpace: 'pre-line' }}
        >
          {text}
        </div>
      ) : (
        <p className="m-0 text-600">{emptyMessage}</p>
      )}
    </section>
  );
};

const MonthlyReportPage = () => {
  const [month, setMonth] = useState(lastMonth);
  const [showDates, setShowDates] = useState(true);
  const { data, isError, isLoading } = useQuery(
    reportQuery(...monthRange(month)),
  );

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="align-items-center flex flex-wrap gap-3 justify-content-between mb-3">
        <div className="align-items-center flex flex-wrap font-medium gap-2 text-900 text-xl">
          <div>Havi beszámoló</div>
          <Calendar
            ariaLabel="Hónap"
            dateFormat="yy. MM"
            onChange={(e) => e.value && setMonth(e.value)}
            readOnlyInput
            value={month}
            view="month"
          />
        </div>
        <div className="align-items-center flex gap-2">
          <label htmlFor="showDates">Dátumok</label>
          <InputSwitch
            checked={showDates}
            inputId="showDates"
            onChange={(e) => setShowDates(!!e.value)}
          />
        </div>
      </div>
      <div className="border-round flex flex-column gap-4 p-3 shadow-2 sm:p-4 surface-card">
        {isLoading && <ProgressBar mode="indeterminate" />}
        {isError && !data && (
          <p className="m-0">Nem sikerült betölteni a beszámolót.</p>
        )}
        {data && (
          <>
            <ReportList
              emptyMessage="Ebben a hónapban nem volt felkérés."
              items={data.requests}
              showDates={showDates}
              title="Felkérések"
            />
            <ReportList
              emptyMessage="Ebben a hónapban nem volt vágás."
              items={data.videos}
              showDates={showDates}
              title="Vágások"
            />
          </>
        )}
      </div>
    </div>
  );
};

export { MonthlyReportPage as Component };
