const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';
const API_FALLBACK_BASE_URL = 'http://localhost:8000/api';

/**
 * Helper to handle fetch requests and return JSON
 */
async function fetchJson(endpoint, options = {}) {
  const requestOptions = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };
  const fetchFromBaseUrl = async (baseUrl) => {
    const res = await fetch(`${baseUrl}${endpoint}`, requestOptions);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
    }

    return await res.json();
  };

  try {
    return await fetchFromBaseUrl(API_BASE_URL);
  } catch (error) {
    if (!process.env.NEXT_PUBLIC_API_URL && API_BASE_URL !== API_FALLBACK_BASE_URL) {
      try {
        return await fetchFromBaseUrl(API_FALLBACK_BASE_URL);
      } catch (fallbackError) {
        console.error(`API Error fetching ${endpoint}:`, fallbackError);
        throw fallbackError;
      }
    }

    console.error(`API Error fetching ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Prices Endpoints
  async getLatestPrice(currency = 'USD') {
    return fetchJson(`/prices/current?currency=${currency}`);
  },
  
  async getHistoricalPrices(startDate, endDate, currency = 'USD') {
    let url = `/prices/historical?currency=${currency}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    return fetchJson(url);
  },

  async getChartData(period = '1Y', currency = 'USD') {
    return fetchJson(`/prices/chart-data?period=${period}&currency=${currency}`);
  },

  // Predictions Endpoints
  async get30DayPredictions(currency = 'USD') {
    return fetchJson(`/predictions/latest?currency=${currency}`);
  },

  async getModelPerformance() {
    return fetchJson(`/predictions/accuracy`);
  },

  async getLatestLLMAnalysis() {
    return fetchJson(`/predictions/llm-latest`);
  },

  async regenerateMLPredictions() {
    return fetchJson('/predictions/generate', {
      method: 'POST'
    });
  },

  async regenerateLLMAnalysis() {
    return fetchJson('/predictions/run-llm', {
      method: 'POST'
    });
  },

  async getPredictionJobStatus() {
    return fetchJson('/predictions/jobs/status');
  },

  // Events Endpoints
  async getEvents(params = {}) {
    let url = '/events/';
    const queryParams = [];
    if (params.event_type) queryParams.push(`event_type=${params.event_type}`);
    if (params.impact_level) queryParams.push(`impact_level=${params.impact_level}`);
    if (params.start_date) queryParams.push(`start_date=${params.start_date}`);
    if (params.end_date) queryParams.push(`end_date=${params.end_date}`);
    if (queryParams.length) url += `?${queryParams.join('&')}`;
    return fetchJson(url);
  },

  async getEventTimeline() {
    return fetchJson('/events/timeline');
  },

  async getEventImpactAnalysis() {
    return fetchJson('/events/impact-analysis');
  },

  async getEventDetail(id) {
    return fetchJson(`/events/${id}`);
  },

  // Indicators Endpoints
  async getIndicators() {
    return fetchJson('/indicators/latest');
  },

  async getIndicatorData(name, startDate, endDate) {
    let url = `/indicators/historical?indicator_name=${name}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    return fetchJson(url);
  },

  async getIndicatorCorrelation() {
    return fetchJson('/indicators/correlation');
  },

  // News Endpoints
  async getLatestNews(limit = 10) {
    return fetchJson(`/news/latest?limit=${limit}`);
  },

  async getSentimentTrend(days = 30) {
    return fetchJson(`/news/sentiment-trend?days=${days}`);
  },

  async getSentimentImpact() {
    return fetchJson('/news/impact');
  },

  // Settings Endpoints
  async getApiKeys() {
    return fetchJson('/settings/keys');
  },

  async addApiKey(provider, key_value, is_primary = false) {
    return fetchJson('/settings/keys', {
      method: 'POST',
      body: JSON.stringify({ provider, key_value, is_primary })
    });
  },

  async deleteApiKey(key_id) {
    return fetchJson(`/settings/keys/${key_id}`, {
      method: 'DELETE'
    });
  },

  async reactivateApiKey(key_id) {
    return fetchJson(`/settings/keys/${key_id}/reactivate`, {
      method: 'POST'
    });
  },

  async getSetting(key) {
    return fetchJson(`/settings/${encodeURIComponent(key)}`);
  },

  async saveSetting(key, value) {
    return fetchJson(`/settings/${encodeURIComponent(key)}`, {
      method: 'POST',
      body: JSON.stringify({ value })
    });
  }
};
