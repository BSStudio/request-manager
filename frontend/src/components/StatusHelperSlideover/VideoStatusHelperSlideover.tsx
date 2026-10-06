import { useRef } from 'react';

import { Button } from 'primereact/button';
import { Message } from 'primereact/message';
import { StyleClass } from 'primereact/styleclass';
import { classNames } from 'primereact/utils';

import { VIDEO_STATUSES } from 'components/StatusTag/statusTagConsts';
import useMobile from 'hooks/useMobile';

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
            {status == 1 && (
              <ActiveTask
                icon={VIDEO_STATUSES[1].icon}
                label={VIDEO_STATUSES[1].text}
              >
                <ActivePendingTaskItem label="Felkérés beírva státuszú" />
                {editor ? (
                  <ActiveCompleteTaskItem label="Vágó kijelölése" />
                ) : (
                  <ActivePendingTaskItem label="Vágó kijelölése" />
                )}
              </ActiveTask>
            )}
            {status > 1 && (
              <Task label={VIDEO_STATUSES[2].text} type="complete" />
            )}

            {status < 2 && (
              <Task
                icon={VIDEO_STATUSES[3].icon}
                label={VIDEO_STATUSES[3].text}
                type="pending"
              />
            )}
            {status == 2 && (
              <ActiveTask
                icon={VIDEO_STATUSES[3].icon}
                label={VIDEO_STATUSES[3].text}
              >
                <ActivePendingTaskItem label="Vágás befejezése" />
              </ActiveTask>
            )}
            {status > 2 && (
              <Task label={VIDEO_STATUSES[3].text} type="complete" />
            )}

            {status < 3 && (
              <Task
                icon={VIDEO_STATUSES[4].icon}
                label={VIDEO_STATUSES[4].text}
                type="pending"
              />
            )}
            {status == 3 && (
              <ActiveTask
                icon={VIDEO_STATUSES[4].icon}
                label={VIDEO_STATUSES[4].text}
              >
                <ActivePendingTaskItem label="Videó kikódolása a weboldalra" />
              </ActiveTask>
            )}
            {status > 3 && (
              <Task label={VIDEO_STATUSES[4].text} type="complete" />
            )}

            {status < 4 && (
              <Task
                icon={VIDEO_STATUSES[5].icon}
                label={VIDEO_STATUSES[5].text}
                type="pending"
              />
            )}
            {status == 4 && (
              <ActiveTask
                icon={VIDEO_STATUSES[5].icon}
                label={VIDEO_STATUSES[5].text}
              >
                <ActivePendingTaskItem label="Videó publikálása" />
              </ActiveTask>
            )}
            {status > 4 && (
              <Task label={VIDEO_STATUSES[5].text} type="complete" />
            )}

            {status < 5 && (
              <Task
                icon={VIDEO_STATUSES[6].icon}
                label={VIDEO_STATUSES[6].text}
                type="pending"
              />
            )}
            {status == 5 && (
              <ActiveTask
                icon={VIDEO_STATUSES[6].icon}
                label={VIDEO_STATUSES[6].text}
              >
                <ActivePendingTaskItem label="Logó nélküli export áthelyezése az archívumba" />
              </ActiveTask>
            )}
            {status > 5 && (
              <Task label={VIDEO_STATUSES[6].text} type="complete" />
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default VideoStatusHelperSlideover;
