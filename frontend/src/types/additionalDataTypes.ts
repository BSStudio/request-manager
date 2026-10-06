export type RequestAdditionalDataRecordingType = {
  path?: string;
  copied_to_gdrive?: boolean;
  removed?: boolean;
};

export type RequestAdditionalDataType = {
  accepted?: boolean;
  calendar_id?: string;
  canceled?: boolean;
  external?: {
    sch_events_callback_url?: string;
  };
  failed?: boolean;
  recording?: RequestAdditionalDataRecordingType;
  requester?: {
    first_name: string;
    last_name: string;
    phone_number: string;
  };
  status_by_admin?: {
    status: number | null;
    admin_id: number;
    admin_name: string;
  };
};

export type VideoAdditionalDataType = {
  aired?: [string];
  archiving?: {
    hq_archive?: boolean;
  };
  coding?: {
    website?: boolean;
  };
  editing_done?: boolean;
  length?: number | null;
  publishing?: {
    email_sent_to_user?: boolean;
    website?: string;
  };
  status_by_admin?: {
    admin_id: number;
    admin_name: string;
    status: number | null;
  };
};
