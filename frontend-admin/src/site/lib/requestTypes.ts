import {
  type LucideIcon,
  MegaphoneIcon,
  MicIcon,
  MusicIcon,
  PresentationIcon,
  RadioIcon,
} from 'lucide-react';

type RequestType = {
  description: string;
  icon: LucideIcon;
  title: string;
};

export const requestTypes: RequestType[] = [
  {
    description:
      'Élőben közvetítjük az eseményt, így az is láthatja, aki nem tud ott lenni.',
    icon: RadioIcon,
    title: 'Élő közvetítés',
  },
  {
    description:
      'Rövid, zenés összefoglaló, ami visszaadja az esemény hangulatát.',
    icon: MusicIcon,
    title: 'Zenés hangulatvideó',
  },
  {
    description:
      'Hangulatvideó, amelyben a résztvevők és a szervezők is megszólalnak.',
    icon: MicIcon,
    title: 'Hangulatvideó riportokkal',
  },
  {
    description:
      'Kedvcsináló videó egy közelgő esemény vagy egy kör népszerűsítésére.',
    icon: MegaphoneIcon,
    title: 'Promóciós videó',
  },
  {
    description:
      'Teljes hosszában rögzítjük az előadásokat vagy a rendezvényt, hogy később is vissza lehessen nézni.',
    icon: PresentationIcon,
    title: 'Előadás, rendezvény videós dokumentálása',
  },
];
