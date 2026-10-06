import React from 'react';

import { classNames } from 'primereact/utils';
import type { IconType } from 'primereact/utils';

import { StatusStyle } from 'components/StatusTag/StatusTagTypes';
import { useTheme } from 'hooks/useTheme';

type ActiveTaskItemProps = {
  label: string;
};

type ActiveTaskProps = {
  children: React.JSX.Element[] | React.JSX.Element;
  icon: IconType<StatusStyle>;
  label: string;
};

type TaskProps = {
  icon?: IconType<StatusStyle>;
  label: string;
  type: 'complete' | 'failed' | 'pending';
};

export const ActiveCompleteTaskItem = ({ label }: ActiveTaskItemProps) => {
  const [darkMode] = useTheme();
  return (
    <li className="align-items-center flex p-2">
      <i
        className={classNames(
          'pi pi-check',
          darkMode ? 'text-green-300' : 'text-green-500',
        )}
      ></i>
      <span className="ml-3 text-600">{label}</span>
    </li>
  );
};

export const ActivePendingTaskItem = ({ label }: ActiveTaskItemProps) => {
  return (
    <li className="align-items-center flex p-2">
      <span className="font-bold ml-5 text-900">{label}</span>
      <i className="ml-auto pi pi-arrow-right text-900"></i>
    </li>
  );
};

export const ActiveTask = ({ children, icon, label }: ActiveTaskProps) => {
  return (
    <li className="border-top-1 p-3 surface-border">
      <div className="align-items-center flex mb-3">
        <span
          className="align-items-center border-1 border-circle border-transparent inline-flex justify-content-center mr-3 surface-900 text-0 text-2xl"
          style={{ height: '35px', width: '35px' }}
        >
          <i className={classNames('pi', icon)}></i>
        </span>
        <span className="font-bold font-medium text-900">{label}</span>
      </div>
      <ul className="list-none p-0 m-0">{children}</ul>
    </li>
  );
};

export const Task = ({ icon, label, type }: TaskProps) => {
  const [darkMode] = useTheme();

  return (
    <li className="align-items-center border-top-1 flex p-3 surface-border">
      <span
        className={classNames(
          'align-items-center border-1 border-circle inline-flex justify-content-center mr-3 text-2xl',
          type === 'pending'
            ? 'surface-border'
            : 'border-transparent text-color-primary',
          {
            'bg-green-300': darkMode && type === 'complete',
            'bg-green-500': !darkMode && type === 'complete',
            'bg-red-300': darkMode && type === 'failed',
            'bg-red-500': !darkMode && type === 'failed',
          },
        )}
        style={{ height: '35px', width: '35px' }}
      >
        <i
          className={classNames('pi', {
            icon: !!icon,
            'pi-check': type === 'complete',
            'pi-times': type === 'failed',
            'text-700': type === 'pending',
          })}
        ></i>
      </span>
      <span className="font-medium text-700">{label}</span>
    </li>
  );
};
