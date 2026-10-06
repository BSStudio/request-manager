import React from 'react';

import { Avatar } from 'primereact/avatar';
import { Divider } from 'primereact/divider';
import { Tooltip } from 'primereact/tooltip';

import { History } from 'api/models/history';
import { dateTimeToLocaleString } from 'helpers/DateToLocaleStringCoverters';
import TimeAgo from 'helpers/TimeAgo';
import { UI_AVATAR_URL } from 'localConstants';

export interface HistoryDates // TODO: Rename?
  extends Omit<History, 'date'> {
  date: Date;
}

type HistoryComponentProps = {
  getFieldName: (name: string) => string;
  getFieldValue: (name: string, value: string) => string | React.JSX.Element;
  history: HistoryDates[];
};

export function getHistory(history_array: History[]): HistoryDates[] {
  return [...history_array].map((history) => {
    return {
      ...history,
      date: new Date(history.date),
    };
  });
}

const HistoryComponent = ({
  getFieldName,
  getFieldValue,
  history,
}: HistoryComponentProps) => {
  return (
    <div className="p-2">
      {history.map((entry, entryIndex) =>
        entry.changes.map((change, changeIndex) => (
          <span key={entry.date.toUTCString() + entryIndex + changeIndex}>
            <div className="flex flex-row">
              <div className="mr-2">
                <Avatar
                  className="flex-shrink-0 h-2rem mr-2 w-2rem"
                  icon={entry.user ? 'pi pi-user' : 'pi pi-server'}
                  image={
                    entry.user
                      ? entry.user.avatar_url ||
                        UI_AVATAR_URL + entry.user.full_name
                      : undefined
                  }
                  shape="circle"
                />
              </div>
              <div className="flex flex-column">
                <div>
                  <Tooltip className="text-xs" target=".entry-date-text" />
                  <b>{entry.user?.full_name || 'Rendszer'}</b> módosította a(z){' '}
                  <b>{getFieldName(change.field)}</b> mezőt
                  <span
                    className="entry-date-text ml-2 font-medium text-500 text-sm"
                    data-pr-position="bottom"
                    data-pr-tooltip={dateTimeToLocaleString(entry.date)}
                  >
                    <TimeAgo datetime={entry.date} locale="hu_HU" />
                  </span>
                </div>
                <div
                  className="align-items-center flex flex-row gap-3 mt-2"
                  key={change.field}
                >
                  <div className="comment-text">
                    {getFieldValue(change.field, change.old)}
                  </div>
                  <div>→</div>
                  <div className="comment-text">
                    {getFieldValue(change.field, change.new)}
                  </div>
                </div>
              </div>
            </div>
            {(entryIndex + 1 !== history.length ||
              changeIndex + 1 !== entry.changes.length) && (
              <Divider type="dashed" />
            )}
          </span>
        )),
      )}
    </div>
  );
};

export default HistoryComponent;
