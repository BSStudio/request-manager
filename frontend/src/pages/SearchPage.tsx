import { useState } from 'react';

import { ToggleButton } from 'primereact/togglebutton';

import { RequestAdminList, VideoAdminSearch } from 'api/models';
import RequestsDataTable from 'components/RequestsDataTable/RequestsDataTable';
import RequestSearchForm from 'components/Search/RequestSearchForm';
import VideoSearchForm from 'components/Search/VideoSearchForm';
import { Status } from 'components/StatusTag/StatusTagTypes';
import VideoSearchDataTable from 'components/VideosDataTable/VideoSearchDataTable';

export type SearchStatusDropdownType = Status & { status: number };

const SearchPage = () => {
  const [searchVideo, setSearchVideo] = useState<boolean>(false);
  const [requestSearchResults, setRequestSearchResults] = useState<
    RequestAdminList[]
  >([]);
  const [videoSearchResults, setVideoSearchResults] = useState<
    VideoAdminSearch[]
  >([]);

  return (
    <div className="p-3 sm:p-5 surface-ground">
      <div className="align-items-center flex font-medium mb-3 text-900 text-xl">
        <div>Keresés</div>
        <ToggleButton
          checked={searchVideo}
          pt={{ box: { className: 'ml-2 p-1 text-sm font-medium' } }}
          offIcon="pi pi-video text-sm "
          offLabel="Felkérések"
          onChange={(e) => setSearchVideo(e.value)}
          onIcon="bi bi-film text-sm"
          onLabel="Videók"
        />
      </div>
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        {searchVideo ? (
          <VideoSearchForm setVideoSearchResults={setVideoSearchResults} />
        ) : (
          <RequestSearchForm
            setRequestSearchResults={setRequestSearchResults}
          />
        )}
      </div>
      <div className="font-medium mb-3 mt-5 text-900 text-xl">Találatok</div>
      <div className="border-round p-3 shadow-2 sm:p-4 surface-card">
        {searchVideo ? (
          <VideoSearchDataTable videos={videoSearchResults} />
        ) : (
          <RequestsDataTable requests={requestSearchResults} />
        )}
      </div>
    </div>
  );
};

export { SearchPage as Component };
