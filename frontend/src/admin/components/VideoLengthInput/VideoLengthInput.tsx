import { useEffect, useRef, useState } from 'react';
import type { ComponentProps } from 'react';

import { captureException } from '@sentry/react';
import wasmUrl from 'mediainfo.js/MediaInfoModule.wasm?url';
import { Button } from 'primereact/button';
import { InputMask } from 'primereact/inputmask';

import { formatVideoLength } from 'admin/helpers/formatVideoLength';
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
    const tracks = result.media?.track ?? [];
    if (!tracks.some((track) => track['@type'] === 'Video')) return undefined;
    return tracks.find((track) => track['@type'] === 'General')?.Duration;
  } finally {
    mediaInfo.close();
  }
}

const VideoLengthInput = ({ onChange, ...props }: VideoLengthInputProps) => {
  const fileInput = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const { showToast } = useToast();
  const { disabled } = props;

  useEffect(() => {
    if (disabled) return;
    const onDragEnter = (event: globalThis.DragEvent) => {
      if (event.dataTransfer?.types.includes('Files')) setIsDragging(true);
    };
    window.addEventListener('dragenter', onDragEnter);
    return () => window.removeEventListener('dragenter', onDragEnter);
  }, [disabled]);

  const fillFrom = async (file: File) => {
    setIsReading(true);
    const length = await readLength(file).catch((error: unknown) => {
      captureException(error);
      return undefined;
    });
    setIsReading(false);
    if (length) {
      onChange?.(formatVideoLength(length));
    } else {
      showToast({
        detail: 'Nem sikerült kiolvasni a videó hosszát.',
        life: 3000,
        severity: 'error',
        summary: 'Hiba',
      });
    }
  };

  return (
    <>
      <div className="p-inputgroup">
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
          disabled={disabled}
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
      {/* Covers the page and keeps drag events off its content, so a
          dragleave means the file left the window. */}
      {isDragging && !disabled && (
        <div
          className="align-items-center fixed flex h-full justify-content-center left-0 p-component-overlay p-component-overlay-enter top-0 w-full z-5"
          onDragLeave={() => setIsDragging(false)}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            const file = event.dataTransfer.files[0];
            if (file && !isReading) void fillFrom(file);
          }}
        >
          <div className="border-3 border-dashed border-primary border-round p-5 pointer-events-none surface-card text-center">
            <i className="pi pi-video text-5xl text-primary" />
            <div className="font-medium mt-3 text-900 text-xl">
              Engedd el a videót a hossz kiolvasásához
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default VideoLengthInput;
