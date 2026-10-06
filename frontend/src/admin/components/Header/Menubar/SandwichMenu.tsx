import { useRef } from 'react';

import { StyleClass } from 'primereact/styleclass';

const SandwichMenu = () => {
  const btnRef = useRef(null);

  return (
    <StyleClass
      enterFromClassName="hidden"
      hideOnOutsideClick
      leaveToClassName="hidden"
      nodeRef={btnRef}
      selector="@next"
    >
      <a
        className="align-self-center block cursor-pointer lg:hidden p-ripple text-700"
        ref={btnRef}
      >
        <i className="pi pi-bars text-4xl"></i>
      </a>
    </StyleClass>
  );
};

export default SandwichMenu;
