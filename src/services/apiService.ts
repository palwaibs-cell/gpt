const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const USE_MOCK_API = false; // Production mode - use real backend

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
    
    return this.request<CreateOrderResponse>('/api/orders', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  }

  async getOrderStatus(orderId: string): Promise<OrderStatusResponse> {
    if (USE_MOCK_API) {
      return mockApiService.getOrderStatus(orderId);
    }
    
    return this.request<OrderStatusResponse>(`/api/orders/${orderId}/status`);
  }
}

export const apiService = new ApiService();