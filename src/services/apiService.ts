const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://pwnzbpkprtvvwrxveixn.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB3bnpicGtwcnR2dndyeHZlaXhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyMjY2OTEsImV4cCI6MjA3NDgwMjY5MX0.XN5F7FZrITcSMp95VIVHdELDF_A5oHvl95LC72BH-lo';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const USE_MOCK_API = false;
const USE_EDGE_FUNCTIONS = true; // Use Supabase Edge Functions instead of Python backend

export interface CreateOrderRequest {
  customer_email: string;
  package_id: string;
  full_name: string;
  phone_number: string;
}

export interface CreateOrderResponse {
  order_id: string;
  checkout_url: string;
  reference: string;
  status: string;
}

export interface OrderStatusResponse {
  order_id: string;
  payment_status: 'pending' | 'paid' | 'failed' | 'expired';
  invitation_status: 'pending' | 'processing' | 'sent' | 'failed' | 'manual_review_required';
  message: string;
}

// Import mock service
import { mockApiService } from './mockApiService';

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || 
          `HTTP Error: ${response.status} ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  async createOrder(orderData: CreateOrderRequest): Promise<CreateOrderResponse> {
    if (USE_MOCK_API) {
      return mockApiService.createOrder(orderData);
    }

    if (USE_EDGE_FUNCTIONS && SUPABASE_URL && SUPABASE_ANON_KEY) {
      const edgeUrl = `${SUPABASE_URL}/functions/v1/create-order`;

      try {
        const response = await fetch(edgeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          },
          body: JSON.stringify(orderData),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP Error: ${response.status}`);
        }

        return await response.json();
      } catch (error) {
        console.error('Edge function error:', error);
        throw error;
      }
    }

    return this.request<CreateOrderResponse>('/api/orders', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  }

  async getOrderStatus(orderId: string): Promise<OrderStatusResponse> {
    if (USE_MOCK_API) {
      return mockApiService.getOrderStatus(orderId);
    }

    if (USE_EDGE_FUNCTIONS && SUPABASE_URL && SUPABASE_ANON_KEY) {
      try {
        const response = await fetch(
          `${SUPABASE_URL}/rest/v1/orders?order_id=eq.${orderId}&select=order_id,payment_status,invitation_status`,
          {
            headers: {
              'apikey': SUPABASE_ANON_KEY,
              'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();

        if (!data || data.length === 0) {
          throw new Error('Order not found');
        }

        const order = data[0];

        let message = '';
        if (order.payment_status === 'paid' && order.invitation_status === 'sent') {
          message = 'Pembayaran berhasil dan undangan telah dikirim!';
        } else if (order.payment_status === 'paid') {
          message = 'Pembayaran berhasil! Undangan sedang diproses.';
        } else if (order.payment_status === 'pending') {
          message = 'Menunggu pembayaran.';
        } else {
          message = 'Status pembayaran: ' + order.payment_status;
        }

        return {
          order_id: order.order_id,
          payment_status: order.payment_status,
          invitation_status: order.invitation_status,
          message
        };
      } catch (error) {
        console.error('Error fetching order status:', error);
        throw error;
      }
    }

    return this.request<OrderStatusResponse>(`/api/orders/${orderId}/status`);
  }
}

export const apiService = new ApiService();