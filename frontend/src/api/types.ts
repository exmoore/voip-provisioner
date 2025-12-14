/**
 * TypeScript types matching backend API schemas
 */

export interface Phone {
  mac: string;
  model: string;
  extension: string;
  display_name: string;
  pbx_server: string | null;
  pbx_port: number | null;
  transport: string | null;
  label: string | null;
  codecs: string[] | null;
  vendor: string | null;
  effective_settings: Record<string, any> | null;
}

export interface CreatePhoneRequest {
  mac: string;
  model: string;
  extension: string;
  display_name: string;
  password: string;
  pbx_server?: string | null;
  pbx_port?: number | null;
  transport?: string | null;
  label?: string | null;
  codecs?: string[] | null;
}

export interface UpdatePhoneRequest {
  model?: string | null;
  extension?: string | null;
  display_name?: string | null;
  password?: string | null;
  pbx_server?: string | null;
  pbx_port?: number | null;
  transport?: string | null;
  label?: string | null;
  codecs?: string[] | null;
}

export interface PhoneListResponse {
  phones: Phone[];
  total: number;
}

export interface PhoneConfigResponse {
  mac: string;
  extension: string;
  vendor: string;
  config: string;
}

export interface PhonebookEntry {
  id: number;
  name: string;
  number: string;
}

export interface CreatePhonebookEntryRequest {
  name: string;
  number: string;
}

export interface UpdatePhonebookEntryRequest {
  name?: string | null;
  number?: string | null;
}

export interface PhonebookListResponse {
  phonebook_name: string;
  entries: PhonebookEntry[];
  total: number;
}

export interface GlobalSettings {
  pbx_server: string;
  pbx_port: number;
  transport: string;
  ntp_server: string;
  timezone: string;
  codecs: string[];
}

export interface UpdateGlobalSettingsRequest {
  pbx_server: string;
  pbx_port: number;
  transport: string;
  ntp_server: string;
  timezone: string;
  codecs: string[];
}

export interface ApiError {
  detail: string;
}
