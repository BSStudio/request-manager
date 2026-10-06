import Breadcrumbs from './Breadcrumb/Breadcrumbs';
import Menubar from './Menubar/Menubar';

const Header = () => {
  return (
    <header>
      <Menubar />
      <Breadcrumbs />
    </header>
  );
};

export default Header;
