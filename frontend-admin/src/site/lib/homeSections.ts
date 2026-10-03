import {
  LayersIcon,
  ListOrderedIcon,
  type LucideIcon,
  MailIcon,
} from 'lucide-react';

// Anchors of the home page sections, matching their ids.
export const homeSections: { icon: LucideIcon; label: string; to: string }[] = [
  { icon: LayersIcon, label: 'Szolgáltatások', to: '/#szolgaltatasok' },
  { icon: ListOrderedIcon, label: 'Így működik', to: '/#igy-mukodik' },
  { icon: MailIcon, label: 'Kapcsolat', to: '/#kapcsolat' },
];
