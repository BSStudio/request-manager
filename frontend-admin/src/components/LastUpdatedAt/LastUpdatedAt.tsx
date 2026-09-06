import type { QueryObserverResult } from '@tanstack/react-query';

import TimeAgo from 'helpers/TimeAgo';

type LastUpdatedAtProps = {
  lastUpdatedAt: Date;
  refetch?: () => Promise<QueryObserverResult>;
};

const LastUpdatedAt = ({ lastUpdatedAt, refetch }: LastUpdatedAtProps) => {
  return (
    <div>
      <p className="text-xs">
        Utoljára frissítve: <TimeAgo datetime={lastUpdatedAt} locale="hu_HU" />
        {refetch && (
          <>
            {' ('}
            <a
              className="cursor-pointer hover:dashed underline"
              onClick={() => refetch()}
            >
              frissítés
            </a>
            {')'}
          </>
        )}
      </p>
    </div>
  );
};

export default LastUpdatedAt;
