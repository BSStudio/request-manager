import React from 'react';

import { classNames } from 'primereact/utils';

interface DetailsRowProps {
  button?: React.JSX.Element;
  content: string | React.JSX.Element;
  firstElement?: boolean;
  label: string;
  lastElement?: boolean;
  multipleLines?: boolean;
}

const DetailsRow = ({
  button,
  content,
  firstElement,
  label,
  lastElement,
  multipleLines,
}: DetailsRowProps) => {
  return (
    <li
      className={classNames(
        'align-items-center flex flex-wrap px-2',
        firstElement ? 'md:pt-3 pb-3 pt-1 sm:pt-2' : 'py-3',
        { 'border-bottom-1 surface-border': !lastElement },
      )}
    >
      <div className="font-medium md:pb-0 md:w-2 pb-1 pr-3 text-500 w-6">
        {label}
      </div>
      <div
        className={classNames(
          'flex-order-1 md:flex-order-0 text-900 w-full',
          button ? 'md:w-8' : 'md:w-10',
          { 'line-height-3': multipleLines },
        )}
      >
        {content}
      </div>
      {button && (
        <div className="flex justify-content-end md:w-2 w-6">{button}</div>
      )}
    </li>
  );
};

export default DetailsRow;
