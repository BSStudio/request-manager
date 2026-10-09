import type { RefObject } from 'react';

import { StyleClass } from 'primereact/styleclass';

const SandwichMenu = ({ ref }: { ref: RefObject<null> }) => {
  return (
    <StyleClass
      enterFromClassName="hidden"
      hideOnOutsideClick
      leaveToClassName="hidden"
      nodeRef={ref}
      selector="@next"
    >
      <a
        className="align-self-center block cursor-pointer lg:hidden p-ripple text-700"
        ref={ref}
      >
        <i className="pi pi-bars text-4xl"></i>
      </a>
    </StyleClass>
  );
};

export default SandwichMenu;
