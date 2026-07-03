export interface Deal {
  id: number;
  ebay_item_id: string;
  title: string;
  price: number | null;
  currency: string;
  condition: string | null;
  listing_type: string | null;
  image_url: string | null;
  category_key: string;
  category_display: string;
  score: number | null;
  classification: string | null;
  price_range: string | null;
  view_url: string | null;
}

export interface PricePoint {
  price: number;
  captured_at: string;
}

export interface DealDetail extends Deal {
  price_history: PricePoint[];
}

export interface Category {
  key: string;
  display_name: string;
  group_key: string;
  listing_count: number;
  median_price: number | null;
}

export interface Stats {
  total_listings: number;
  total_categories: number;
  hot_deals_count: number;
  good_deals_count: number;
  last_updated: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  total_pages: number;
  total_items: number;
}

export interface SetupGuide {
  slug: string;
  title: string;
  description: string;
  icon: string;
  content: string;
}
