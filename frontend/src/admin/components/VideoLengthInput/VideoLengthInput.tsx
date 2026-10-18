import { useRef, useState } from 'react';
import type { ComponentProps, DragEvent } from 'react';

import wasmUrl from 'mediainfo.js/MediaInfoModule.wasm?url';
import { Button } from 'primereact/button';
import { InputMask } from 'primereact/inputmask';

import { useToast } from 'admin/providers/ToastProvider';

type VideoLengthInputProps = Omit<
  ComponentProps<typeof InputMask>,
  'onChange'
> & {
  onChange?: (value: string | undefined) => void;
};

async function readLength(file: File) {
  const { default: mediaInfoFactory } = await import('mediainfo.js');
  // Its default lookup expects the WASM file next to its bundle, which is not
  // where the build puts it.
  const mediaInfo = await mediaInfoFactory({ locateFile: () => wasmUrl });
  try {
    const result = await mediaInfo.analyzeData(
      file.size,
      async (size, offset) =>
        new Uint8Array(await file.slice(offset, offset + size).arrayBuffer()),
    );
    return result.media?.track.find((track) => track['@type'] === 'General')
      ?.Duration;
  } finally {
    mediaInfo.close();
  }
}

const VideoLengthInput = ({ onChange, ...props }: VideoLengthInputProps) => {
  const fileInput = useRef<HTMLInputElement>(null);
  const [isReading, setIsReading] = useState(false);
  const { showToast } = useToast();

  const fillFrom = async (file: File) => {
    setIsReading(true);
    const length = await readLength(file).catch(() => undefined);
    setIsReading(false);
    if (length) {
      onChange?.(
        new Date(1000 * Math.round(length)).toISOString().substring(11, 19),
      );
    } else {
      showToast({
        detail: 'Nem sikerült kiolvasni a videó hosszát.',
        life: 3000,
        severity: 'error',
        summary: 'Hiba',
      });
    }
  };

  const onDragOver = (event: DragEvent) => {
    if (event.dataTransfer.types.includes('Files')) event.preventDefault();
  };

  const onDrop = (event: DragEvent) => {
    const file = event.dataTransfer.files[0];
    if (!file) return;
    event.preventDefault();
    if (!props.disabled && !isReading) void fillFrom(file);
  };

  return (
    <>
      <div className="p-inputgroup" onDragOver={onDragOver} onDrop={onDrop}>
        <span className="p-inputgroup-addon">
          <i className="pi pi-clock" />
        </span>
        <InputMask
          mask="99:99:99"
          placeholder="hh:mm:ss"
          type="text"
          {...props}
          onChange={(event) => onChange?.(event.value ?? undefined)}
        />
        <Button
          aria-label="Hossz kiolvasása fájlból"
          disabled={props.disabled}
          icon="pi pi-folder-open"
          loading={isReading}
          onClick={() => fileInput.current?.click()}
          tooltip="Hossz kiolvasása fájlból"
          tooltipOptions={{ position: 'top' }}
          type="button"
        />
      </div>
      <input
        accept="video/*,.mxf"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = '';
          if (file) void fillFrom(file);
        }}
        ref={fileInput}
        type="file"
      />
    </>
  );
};

export default VideoLengthInput;
