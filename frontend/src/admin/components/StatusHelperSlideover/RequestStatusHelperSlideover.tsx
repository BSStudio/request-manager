import { useRef } from 'react';

import { Button } from 'primereact/button';
import { Message } from 'primereact/message';
import { StyleClass } from 'primereact/styleclass';
import { classNames } from 'primereact/utils';

import { REQUEST_STATUSES } from 'admin/components/StatusTag/statusTagConsts';
import useMobile from 'admin/hooks/useMobile';
import { RequestStatus } from 'helpers/statuses';

import {
  ActiveCompleteTaskItem,
  ActivePendingTaskItem,
  ActiveTask,
  Task,
} from './components/Tasks';

type RequestStatusHelperSlideoverProps = {
  adminStatusOverride: boolean;
  allVideosDone: boolean;
  copiedToDrive: boolean;
  id: string;
  status: number;
};

const RequestStatusHelperSlideover = ({
  adminStatusOverride,
  allVideosDone,
  copiedToDrive,
  id,
  status,
}: RequestStatusHelperSlideoverProps) => {
  const closeBtnRef = useRef(null);
  const isMobile = useMobile();

  return (
    <div
      className="h-screen hidden left-0 shadow-2 sticky surface-overlay top-0 w-18rem z-5"
      id={id}
      style={{ marginBottom: '-100vh' }}
    >
      <div className="flex flex-column h-full">
        <div
          className={classNames(
            'align-items-center flex justify-content-between',
            {
              'mb-2 pb-2 pt-4 px-4': !isMobile && adminStatusOverride,
              'mb-2 px-4 py-2': isMobile && !adminStatusOverride,
              'mb-4 p-4': !isMobile && !adminStatusOverride,
              'pt-2 px-4': isMobile && adminStatusOverride,
            },
          )}
        >
          <span className="font-medium text-900 text-xl">Munkafolyamat</span>
          <StyleClass
            leaveActiveClassName="fadeoutleft"
            leaveToClassName="hidden"
            nodeRef={closeBtnRef}
            selector={`#${id}`}
          >
            <Button
              className="p-button-plain p-button-rounded p-button-text"
              icon="pi pi-times"
              ref={closeBtnRef}
            />
          </StyleClass>
        </div>
        {adminStatusOverride && (
          <div className="mb-1 p-3">
            <Message
              className="w-full"
              severity="warn"
              text="Admin által felülírt státusz"
            />
          </div>
        )}
        <div className="flex-auto overflow-y-auto">
          <ul className="list-none m-0 p-0">
            {status === RequestStatus.DENIED && (
              <Task
                label={REQUEST_STATUSES[RequestStatus.DENIED].text}
                type="failed"
              />
            )}

            {status === RequestStatus.REQUESTED && (
              <ActiveTask
                icon={REQUEST_STATUSES[RequestStatus.REQUESTED].icon}
                label={REQUEST_STATUSES[RequestStatus.REQUESTED].text}
              >
                <ActivePendingTaskItem label="Elfogadásra vár" />
              </ActiveTask>
            )}
            {status > RequestStatus.REQUESTED && (
              <Task
                label={REQUEST_STATUSES[RequestStatus.ACCEPTED].text}
                type="complete"
              />
            )}

            {status < RequestStatus.ACCEPTED &&
              status > RequestStatus.DENIED && (
                <Task
                  icon={REQUEST_STATUSES[RequestStatus.RECORDED].icon}
                  label={REQUEST_STATUSES[RequestStatus.RECORDED].text}
                  type="pending"
                />
              )}
            {status === RequestStatus.ACCEPTED && (
              <ActiveTask
                icon={REQUEST_STATUSES[RequestStatus.RECORDED].icon}
                label={REQUEST_STATUSES[RequestStatus.RECORDED].text}
              >
                <ActivePendingTaskItem label="Várakozás a forgatás időpontjára" />
              </ActiveTask>
            )}
            {status > RequestStatus.ACCEPTED &&
              status < RequestStatus.CANCELED && (
                <Task
                  label={REQUEST_STATUSES[RequestStatus.RECORDED].text}
                  type="complete"
                />
              )}

            {status === RequestStatus.CANCELED && (
              <Task
                label={REQUEST_STATUSES[RequestStatus.CANCELED].text}
                type="failed"
              />
            )}

            {status === RequestStatus.FAILED && (
              <Task
                label={REQUEST_STATUSES[RequestStatus.FAILED].text}
                type="failed"
              />
            )}

            {status < RequestStatus.RECORDED &&
              status > RequestStatus.DENIED && (
                <Task
                  icon={REQUEST_STATUSES[RequestStatus.UPLOADED].icon}
                  label={REQUEST_STATUSES[RequestStatus.UPLOADED].text}
                  type="pending"
                />
              )}
            {status === RequestStatus.RECORDED && (
              <ActiveTask
                icon={REQUEST_STATUSES[RequestStatus.UPLOADED].icon}
                label={REQUEST_STATUSES[RequestStatus.UPLOADED].text}
              >
                <ActivePendingTaskItem label="Nyersek helyének megadása" />
              </ActiveTask>
            )}
            {status > RequestStatus.RECORDED &&
              status < RequestStatus.CANCELED && (
                <Task
                  label={REQUEST_STATUSES[RequestStatus.UPLOADED].text}
                  type="complete"
                />
              )}

            {status < RequestStatus.UPLOADED &&
              status > RequestStatus.DENIED && (
                <Task
                  icon={REQUEST_STATUSES[RequestStatus.EDITED].icon}
                  label={REQUEST_STATUSES[RequestStatus.EDITED].text}
                  type="pending"
                />
              )}
            {status === RequestStatus.UPLOADED && (
              <ActiveTask
                icon={REQUEST_STATUSES[RequestStatus.EDITED].icon}
                label={REQUEST_STATUSES[RequestStatus.EDITED].text}
              >
                <ActivePendingTaskItem label="Videó(k) megvágása" />
              </ActiveTask>
            )}
            {status > RequestStatus.UPLOADED &&
              status < RequestStatus.CANCELED && (
                <Task
                  label={REQUEST_STATUSES[RequestStatus.EDITED].text}
                  type="complete"
                />
              )}

            {status < RequestStatus.EDITED && status > RequestStatus.DENIED && (
              <Task
                icon={REQUEST_STATUSES[RequestStatus.ARCHIVED].icon}
                label={REQUEST_STATUSES[RequestStatus.ARCHIVED].text}
                type="pending"
              />
            )}
            {status === RequestStatus.EDITED && (
              <ActiveTask
                icon={REQUEST_STATUSES[RequestStatus.ARCHIVED].icon}
                label={REQUEST_STATUSES[RequestStatus.ARCHIVED].text}
              >
                {allVideosDone ? (
                  <ActiveCompleteTaskItem label="Minden videó lezárva" />
                ) : (
                  <ActivePendingTaskItem label="Videó(k) lezárása" />
                )}
                {copiedToDrive ? (
                  <ActiveCompleteTaskItem label="Nyersek felmásolva Drive-ra" />
                ) : (
                  <ActivePendingTaskItem label="Nyersek felmásolása Drive-ra" />
                )}
              </ActiveTask>
            )}
            {status > RequestStatus.EDITED &&
              status < RequestStatus.CANCELED && (
                <Task
                  label={REQUEST_STATUSES[RequestStatus.ARCHIVED].text}
                  type="complete"
                />
              )}

            {status < RequestStatus.ARCHIVED &&
              status > RequestStatus.DENIED && (
                <Task
                  icon={REQUEST_STATUSES[RequestStatus.DONE].icon}
                  label={REQUEST_STATUSES[RequestStatus.DONE].text}
                  type="pending"
                />
              )}
            {status === RequestStatus.ARCHIVED && (
              <ActiveTask
                icon={REQUEST_STATUSES[RequestStatus.DONE].icon}
                label={REQUEST_STATUSES[RequestStatus.DONE].text}
              >
                <ActivePendingTaskItem label="Nyersek törlése" />
              </ActiveTask>
            )}
            {status > RequestStatus.ARCHIVED &&
              status < RequestStatus.CANCELED && (
                <Task
                  label={REQUEST_STATUSES[RequestStatus.DONE].text}
                  type="complete"
                />
              )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RequestStatusHelperSlideover;
