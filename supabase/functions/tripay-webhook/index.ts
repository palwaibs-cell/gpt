import { createClient } from 'npm:@supabase/supabase-js@2.57.4';
import { crypto } from 'https://deno.land/std@0.224.0/crypto/mod.ts';

const TRIPAY_PRIVATE_KEY = Deno.env.get('TRIPAY_PRIVATE_KEY') || 'l3bJu-5D1QE-cBP0k-5rJuV-Zm3Cs';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey',
};

interface TripayCallback {
  reference: string;
  merchant_ref: string;
  payment_method: string;
  payment_method_code: string;
  total_amount: number;
  fee_merchant: number;
  amount_received: number;
  is_closed_payment: number;
  status: 'PAID' | 'UNPAID' | 'FAILED' | 'EXPIRED' | 'REFUND';
  paid_at: number;
  note: string;
}

interface WebhookPayload {
  event: string;
  data: TripayCallback;
}

function verifySignature(callbackSignature: string, payload: string): boolean {
  try {
    const encoder = new TextEncoder();
    const keyData = encoder.encode(TRIPAY_PRIVATE_KEY);
    const message = encoder.encode(payload);

    // HMAC SHA256
    const key = crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );

    return key.then(k => 
      crypto.subtle.sign('HMAC', k, message)
    ).then(signature => {
      const signatureArray = Array.from(new Uint8Array(signature));
      const signatureHex = signatureArray.map(b => b.toString(16).padStart(2, '0')).join('');
      return signatureHex === callbackSignature;
    });
  } catch (error) {
    console.error('Signature verification error:', error);
    return false;
  }
}

Deno.serve(async (req: Request) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: corsHeaders,
    });
  }

  try {
    console.log('Webhook received:', req.method);

    // Get signature from headers
    const callbackSignature = req.headers.get('x-callback-signature');
    if (!callbackSignature) {
      console.error('Missing signature');
      return new Response(
        JSON.stringify({ error: 'Missing signature' }),
        { 
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    // Get raw body for signature verification
    const rawBody = await req.text();
    console.log('Raw body:', rawBody);

    // Verify signature
    const isValid = await verifySignature(callbackSignature, rawBody);
    if (!isValid) {
      console.error('Invalid signature');
      return new Response(
        JSON.stringify({ error: 'Invalid signature' }),
        { 
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    // Parse payload
    const payload: WebhookPayload = JSON.parse(rawBody);
    console.log('Webhook payload:', payload);

    // Only process payment status callbacks
    if (payload.event !== 'payment_status') {
      return new Response(
        JSON.stringify({ message: 'Event not handled' }),
        { 
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    const { reference, merchant_ref, status, paid_at } = payload.data;

    // Initialize Supabase client
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Find order by merchant reference (order_id)
    const { data: orders, error: fetchError } = await supabase
      .from('orders')
      .select('*')
      .eq('order_id', merchant_ref)
      .maybeSingle();

    if (fetchError || !orders) {
      console.error('Order not found:', merchant_ref, fetchError);
      return new Response(
        JSON.stringify({ error: 'Order not found' }),
        { 
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    console.log('Order found:', orders);

    // Map Tripay status to our status
    let paymentStatus = 'pending';
    if (status === 'PAID') {
      paymentStatus = 'paid';
    } else if (status === 'FAILED') {
      paymentStatus = 'failed';
    } else if (status === 'EXPIRED') {
      paymentStatus = 'expired';
    }

    // Update order status
    const { error: updateError } = await supabase
      .from('orders')
      .update({
        payment_status: paymentStatus,
        updated_at: new Date().toISOString()
      })
      .eq('order_id', merchant_ref);

    if (updateError) {
      console.error('Failed to update order:', updateError);
      return new Response(
        JSON.stringify({ error: 'Failed to update order' }),
        { 
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      );
    }

    console.log('Order updated successfully, payment_status:', paymentStatus);

    // If payment is successful, trigger invitation process
    if (status === 'PAID') {
      console.log('Payment successful, updating invitation status to processing');
      
      // Update invitation status to processing
      await supabase
        .from('orders')
        .update({
          invitation_status: 'processing'
        })
        .eq('order_id', merchant_ref);

      // TODO: Trigger Python automation script or Edge Function to send invitation
      // For now, just log that we would trigger the invitation
      console.log('TODO: Trigger invitation automation for email:', orders.customer_email);
    }

    return new Response(
      JSON.stringify({ 
        success: true, 
        message: 'Webhook processed successfully',
        order_id: merchant_ref,
        payment_status: paymentStatus
      }),
      { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );

  } catch (error) {
    console.error('Webhook error:', error);
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    );
  }
});