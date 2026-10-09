import { useRef } from 'react';

import { Button } from 'primereact/button';
import { Message } from 'primereact/message';
import { StyleClass } from 'primereact/styleclass';
import { classNames } from 'primereact/utils';

import { VIDEO_STATUSES } from 'admin/components/StatusTag/statusTagConsts';
import useMobile from 'admin/hooks/useMobile';
import { VideoStatus } from 'helpers/statuses';

import {
  ActiveCompleteTaskItem,
  ActivePendingTaskItem,
  ActiveTask,
  Task,
} from './components/Tasks';

type VideoStatusHelperSlideoverProps = {
  adminStatusOverride: boolean;
  editor: boolean;
  id: string;
  status: number;
};

const VideoStatusHelperSlideover = ({
  adminStatusOverride,
  editor,
  id,
  status,
}: VideoStatusHelperSlideoverProps) => {
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
            {status === VideoStatus.PENDING && (
              <ActiveTask
                icon={VIDEO_STATUSES[VideoStatus.PENDING].icon}
                label={VIDEO_STATUSES[VideoStatus.PENDING].text}
              >
                <ActivePendingTaskItem label="Felkérés beírva státuszú" />
                {editor ? (
                  <ActiveCompleteTaskItem label="Vágó kijelölése" />
                ) : (
                  <ActivePendingTaskItem label="Vágó kijelölése" />
                )}
              </ActiveTask>
            )}
            {status > VideoStatus.PENDING && (
              <Task
                label={VIDEO_STATUSES[VideoStatus.IN_PROGRESS].text}
                type="complete"
              />
            )}

            {status < VideoStatus.IN_PROGRESS && (
              <Task
                icon={VIDEO_STATUSES[VideoStatus.EDITED].icon}
                label={VIDEO_STATUSES[VideoStatus.EDITED].text}
                type="pending"
              />
            )}
            {status === VideoStatus.IN_PROGRESS && (
              <ActiveTask
                icon={VIDEO_STATUSES[VideoStatus.EDITED].icon}
                label={VIDEO_STATUSES[VideoStatus.EDITED].text}
              >
                <ActivePendingTaskItem label="Vágás befejezése" />
              </ActiveTask>
            )}
            {status > VideoStatus.IN_PROGRESS && (
              <Task
                label={VIDEO_STATUSES[VideoStatus.EDITED].text}
                type="complete"
              />
            )}

            {status < VideoStatus.EDITED && (
              <Task
                icon={VIDEO_STATUSES[VideoStatus.CODED].icon}
                label={VIDEO_STATUSES[VideoStatus.CODED].text}
                type="pending"
              />
            )}
            {status === VideoStatus.EDITED && (
              <ActiveTask
                icon={VIDEO_STATUSES[VideoStatus.CODED].icon}
                label={VIDEO_STATUSES[VideoStatus.CODED].text}
              >
                <ActivePendingTaskItem label="Videó kikódolása a weboldalra" />
              </ActiveTask>
            )}
            {status > VideoStatus.EDITED && (
              <Task
                label={VIDEO_STATUSES[VideoStatus.CODED].text}
                type="complete"
              />
            )}

            {status < VideoStatus.CODED && (
              <Task
                icon={VIDEO_STATUSES[VideoStatus.PUBLISHED].icon}
                label={VIDEO_STATUSES[VideoStatus.PUBLISHED].text}
                type="pending"
              />
            )}
            {status === VideoStatus.CODED && (
              <ActiveTask
                icon={VIDEO_STATUSES[VideoStatus.PUBLISHED].icon}
                label={VIDEO_STATUSES[VideoStatus.PUBLISHED].text}
              >
                <ActivePendingTaskItem label="Videó publikálása" />
              </ActiveTask>
            )}
            {status > VideoStatus.CODED && (
              <Task
                label={VIDEO_STATUSES[VideoStatus.PUBLISHED].text}
                type="complete"
              />
            )}

            {status < VideoStatus.PUBLISHED && (
              <Task
                icon={VIDEO_STATUSES[VideoStatus.DONE].icon}
                label={VIDEO_STATUSES[VideoStatus.DONE].text}
                type="pending"
              />
            )}
            {status === VideoStatus.PUBLISHED && (
              <ActiveTask
                icon={VIDEO_STATUSES[VideoStatus.DONE].icon}
                label={VIDEO_STATUSES[VideoStatus.DONE].text}
              >
                <ActivePendingTaskItem label="Logó nélküli export áthelyezése az archívumba" />
              </ActiveTask>
            )}
            {status > VideoStatus.PUBLISHED && (
              <Task
                label={VIDEO_STATUSES[VideoStatus.DONE].text}
                type="complete"
              />
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default VideoStatusHelperSlideover;
