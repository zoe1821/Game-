import Constants from 'expo-constants';

import { tKey } from '@/i18n';

import type { ApiErrorBody, Tokens } from './types';

const DEFAULT_BASE_URL = 'http://localhost:8000';

export function baseUrl(): string {
  const configured = Constants.expoConfig?.extra?.apiBaseUrl;
  return typeof configured === 'string' && configured.length > 0 ? configured : DEFAULT_BASE_URL;
}

/**
 * Error de la API ya traducido.
 *
 * El backend manda `message_key` y `details`; la traducción ocurre aquí, una
 * sola vez, en vez de repartirse por cada pantalla.
 */
export class ApiError extends Error {
  readonly code: string;
  readonly messageKey: string;
  readonly details: Record<string, unknown>;
  readonly status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(tKey(body.message_key, body.details as Record<string, string | number>));
    this.name = 'ApiError';
    this.status = status;
    this.code = body.code;
    this.messageKey = body.message_key;
    this.details = body.details ?? {};
  }

  /** Falta un consentimiento concreto. La UI lo trata distinto de un fallo. */
  get isConsentRequired(): boolean {
    return this.code === 'consent_required';
  }

  get requiresReauthentication(): boolean {
    return this.status === 401;
  }

  get consentPurpose(): string | null {
    const purpose = this.details.purpose;
    return typeof purpose === 'string' ? purpose : null;
  }
}

export class NetworkError extends Error {
  constructor() {
    super(tKey('error.network'));
    this.name = 'NetworkError';
  }
}

export interface TokenStore {
  getAccessToken(): Promise<string | null>;
  getRefreshToken(): Promise<string | null>;
  setTokens(tokens: Tokens): Promise<void>;
  clear(): Promise<void>;
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  /** Para subir fotos: se manda tal cual, sin serializar a JSON. */
  formData?: FormData;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(path.startsWith('/') ? path : `/${path}`, baseUrl());
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export class ApiClient {
  private refreshInFlight: Promise<boolean> | null = null;

  constructor(private readonly tokens: TokenStore) {}

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const response = await this.send(path, options);

    // Un 401 dispara un único refresh compartido: si cinco peticiones fallan a
    // la vez, no se lanzan cinco refrescos que se invaliden entre sí.
    if (response.status === 401 && !path.includes('/auth/')) {
      const refreshed = await this.refreshOnce();
      if (refreshed) {
        const retried = await this.send(path, options);
        return this.parse<T>(retried);
      }
      await this.tokens.clear();
    }

    return this.parse<T>(response);
  }

  private async send(path: string, options: RequestOptions): Promise<Response> {
    const accessToken = await this.tokens.getAccessToken();
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }

    let body: BodyInit | undefined;
    if (options.formData) {
      body = options.formData;
    } else if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(options.body);
    }

    try {
      return await fetch(buildUrl(path, options.query), {
        method: options.method ?? 'GET',
        headers,
        body,
        signal: options.signal,
      });
    } catch {
      throw new NetworkError();
    }
  }

  private async refreshOnce(): Promise<boolean> {
    this.refreshInFlight ??= this.doRefresh().finally(() => {
      this.refreshInFlight = null;
    });
    return this.refreshInFlight;
  }

  private async doRefresh(): Promise<boolean> {
    const refreshToken = await this.tokens.getRefreshToken();
    if (!refreshToken) {
      return false;
    }
    try {
      const response = await fetch(buildUrl('/api/v1/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) {
        return false;
      }
      await this.tokens.setTokens((await response.json()) as Tokens);
      return true;
    } catch {
      return false;
    }
  }

  private async parse<T>(response: Response): Promise<T> {
    if (response.status === 204) {
      return undefined as T;
    }
    const text = await response.text();
    const payload: unknown = text.length > 0 ? JSON.parse(text) : null;

    if (!response.ok) {
      const body = payload as ApiErrorBody | null;
      throw new ApiError(response.status, {
        code: body?.code ?? 'unknown',
        message_key: body?.message_key ?? 'error.generic',
        details: body?.details ?? {},
      });
    }
    return payload as T;
  }
}
