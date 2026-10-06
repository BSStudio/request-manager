import { Skeleton } from 'primereact/skeleton';
import type { IconType } from 'primereact/utils';

export type StatisticsFieldProps = {
  color: 'blue' | 'cyan' | 'orange' | 'purple';
  description: string;
  icon: IconType<StatisticsFieldProps>;
  loading: boolean;
  title: string;
  value: string;
};

type StatisticsProps = {
  statistics: StatisticsFieldProps[];
};

const StatisticsField = ({
  color,
  description,
  icon,
  loading,
  title,
  value,
}: StatisticsFieldProps) => {
  return (
    <div className="col-12 lg:col-3 md:col-6">
      <div className="border-round p-3 shadow-2 surface-card">
        <div className="flex justify-content-between mb-3">
          <div>
            <span className="block font-medium mb-3 text-500">{title}</span>
            <div className="font-medium text-900 text-xl">
              {loading ? <Skeleton width="3rem" height="1.5rem" /> : value}
            </div>
          </div>
          <div
            className={
              'align-items-center border-round flex justify-content-center p-statistics p-statistics-' +
              color
            }
            style={{ height: '2.5rem', width: '2.5rem' }}
          >
            <i className={icon + ' text-xl'}></i>
          </div>
        </div>
        <span className="text-500">{description}</span>
      </div>
    </div>
  );
};

const Statistics = ({ statistics }: StatisticsProps) => {
  return (
    <div className="pt-5 px-3 sm:px-5 surface-ground">
      <div className="grid">
        {statistics.map((statistic, index) => (
          <StatisticsField
            color={statistic.color}
            description={statistic.description}
            icon={statistic.icon}
            loading={statistic.loading}
            key={'stat-' + index}
            title={statistic.title}
            value={statistic.value}
          />
        ))}
      </div>
    </div>
  );
};

export default Statistics;
