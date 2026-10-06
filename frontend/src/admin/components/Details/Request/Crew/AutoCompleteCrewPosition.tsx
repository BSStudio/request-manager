import { forwardRef, useState } from 'react';

import { AutoComplete } from 'primereact/autocomplete';
import type {
  AutoCompleteCompleteEvent,
  AutoCompleteProps,
} from 'primereact/autocomplete';

const positionSuggestions = [
  {
    items: ['Operatőr', 'Riporter', 'Technikus'],
    label: 'Általános',
  },

  {
    items: [
      'Bejátszós-feliratozó',
      'Díszletes',
      'Fénytechnikus',
      'Hangtechnikus',
      'Képmérnök',
      'Képvágó',
      'Mikroportos',
      'Rendező',
      'Stream',
      'Videotechnikus',
    ],
    label: 'Élő közvetítés',
  },
];

const AutoCompleteCrewPosition = forwardRef<
  React.Ref<HTMLInputElement>,
  AutoCompleteProps
>((props, ref) => {
  const [filteredPositions, setFilteredPositions] = useState<
    { items: string[]; label: string }[] | string[]
  >([]);

  const search = (event: AutoCompleteCompleteEvent) => {
    const query = event.query;
    const _filteredPositions = [];

    for (const category of positionSuggestions) {
      const filteredItems = category.items.filter((item) =>
        item.toLowerCase().includes(query.toLowerCase()),
      );

      if (filteredItems.length) {
        _filteredPositions.push({ ...category, ...{ items: filteredItems } });
      }
    }

    setFilteredPositions(_filteredPositions);
  };

  return (
    <AutoComplete
      completeMethod={search}
      dropdown
      optionGroupChildren="items"
      optionGroupLabel="label"
      suggestions={filteredPositions}
      {...props}
      {...ref}
    />
  );
});

AutoCompleteCrewPosition.displayName = 'AutoCompleteCrewPosition';

export default AutoCompleteCrewPosition;
