import type {
  Deal,
  Category,
  Stats,
  PaginatedResponse,
  DealDetail,
} from '../types';

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8183';

async function fetchJSON<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }
    return res.json();
  } catch (err) {
    console.error(`Fetch failed for ${url}:`, err);
    throw err;
  }
}

function emptyPaginated<T>(): PaginatedResponse<T> {
  return { items: [], page: 1, total_pages: 0, total_items: 0 };
}

export const api = {
  async getStats(): Promise<Stats> {
    try {
      return await fetchJSON<Stats>(`${BASE}/api/stats`);
    } catch {
      return {
        total_listings: 0,
        total_categories: 0,
        hot_deals_count: 0,
        good_deals_count: 0,
        last_updated: null,
      };
    }
  },

  async getHotDeals(limit = 20): Promise<Deal[]> {
    try {
      return await fetchJSON<Deal[]>(
        `${BASE}/api/deals/hot?limit=${limit}`,
      );
    } catch {
      return [];
    }
  },

  async getDeals(params: {
    page?: number;
    per_page?: number;
    category?: string;
    group?: string;
    classification?: string;
    sort?: string;
  } = {}): Promise<PaginatedResponse<Deal>> {
    try {
      const qs = new URLSearchParams();
      if (params.page) qs.set('page', String(params.page));
      if (params.per_page) qs.set('per_page', String(params.per_page));
      if (params.category) qs.set('category', params.category);
      if (params.group) qs.set('group', params.group);
      if (params.classification)
        qs.set('classification', params.classification);
      if (params.sort) qs.set('sort', params.sort);

      const query = qs.toString();
      return await fetchJSON<PaginatedResponse<Deal>>(
        `${BASE}/api/deals${query ? `?${query}` : ''}`,
      );
    } catch {
      return emptyPaginated();
    }
  },

  async getDeal(id: number): Promise<DealDetail | null> {
    try {
      return await fetchJSON<DealDetail>(`${BASE}/api/deals/${id}`);
    } catch {
      return null;
    }
  },

  async getCategories(): Promise<Category[]> {
    try {
      return await fetchJSON<Category[]>(`${BASE}/api/categories`);
    } catch {
      return [];
    }
  },
};
