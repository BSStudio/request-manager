import { useRef } from 'react';

import { Ripple } from 'primereact/ripple';
import { StyleClass } from 'primereact/styleclass';
import type { IconType } from 'primereact/utils';
import { href, Link } from 'react-router';

type ButtonDropdownProps = {
  dropdownItems: {
    icon: IconType<ButtonDropdownProps>;
    label: string;
    path: string;
  }[];
  icon: IconType<ButtonDropdownProps>;
  label: string;
};

const DropdownButton = ({
  dropdownItems,
  icon,
  label,
}: ButtonDropdownProps) => {
  const btnRef = useRef(null);

  return (
    <li className="lg:relative">
      {/* Button */}
      <StyleClass
        enterActiveClassName="scalein"
        enterFromClassName="hidden"
        hideOnOutsideClick
        leaveActiveClassName="fadeout"
        leaveToClassName="hidden"
        nodeRef={btnRef}
        selector="@next"
      >
        <a
          className="align-items-center border-left-2 border-transparent cursor-pointer flex font-medium h-full hover:border-primary hover:text-900 lg:border-bottom-2 lg:border-left-none lg:px-3 lg:py-2 p-3 p-ripple px-6 text-600 transition-colors transition-duration-150"
          ref={btnRef}
        >
          <i className={`mr-2 pi ${icon}`}></i>
          <span>{label}</span>
          <i className="lg:ml-3 ml-auto pi pi-angle-down"></i>
          <Ripple />
        </a>
      </StyleClass>

      {/* Dropdown items */}
      <ul className="border-50 border-round cursor-pointer hidden lg:absolute lg:border-1 lg:px-0 lg:shadow-2 lg:w-15rem list-none m-0 origin-top px-6 py-0 shadow-0 surface-overlay w-full">
        {dropdownItems.map((item, index) => (
          <li key={`dropdown-${item.label}-${index}`}>
            <Link
              className="align-items-center border-left-2 border-transparent flex hover:border-primary hover:text-900 no-underline p-3 p-ripple text-600 transition-colors transition-duration-150"
              to={href(item.path)}
            >
              <i className={`mr-2 pi ${item.icon}`}></i>
              <span className="font-medium">{item.label}</span>
              <Ripple />
            </Link>
          </li>
        ))}
      </ul>
    </li>
  );
};

export default DropdownButton;
