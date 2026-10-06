import { useEffect, useState } from 'react';

export default function useMobile() {
  const mdBreakpoint = 768;
  const [isMobile, setIsMobile] = useState(window.innerWidth < mdBreakpoint);

  useEffect(() => {
    function handleResize() {
      if (window.innerWidth < mdBreakpoint) {
        setIsMobile(true);
      } else {
        setIsMobile(false);
      }
    }

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return isMobile;
}
