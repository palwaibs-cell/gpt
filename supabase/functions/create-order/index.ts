import { createClient } from 'npm:@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey',
};

interface OrderRequest {
  customer_email: string;
  package_id: string;
  full_name?: string;
  phone_number?: string;
}

interface TripayResponse {
  success: boolean;
  data?: {
    reference: string;
    checkout_url: string;
    qr_string?: string;
    status: string;
    expired_time: number;
  };
  message?: string;
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: corsHeaders,
    });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const tripayApiKey = Deno.env.get('TRIPAY_API_KEY') || 'VI4hfWUhlfX70OZIjiae18pATyHOvNq0WjvBT6ej';
    const tripayMerchantCode = Deno.env.get('TRIPAY_MERCHANT_CODE') || 'T45484';
    const tripayPrivateKey = Deno.env.get('TRIPAY_PRIVATE_KEY') || '2PW1G-zUdkm-EGiwn-femXJ-yEtIO';
    const tripayBaseUrl = 'https://tripay.co.id/api';

    const body: OrderRequest = await req.json();
    const { customer_email, package_id, full_name, phone_number } = body;

    if (!customer_email || !package_id) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const { data: pkg, error: pkgError } = await supabase
      .from('packages')
      .select('*')
      .eq('id', package_id)
      .eq('is_active', true)
      .maybeSingle();

    if (pkgError || !pkg) {
      return new Response(
        JSON.stringify({ error: 'Invalid package' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const merchantRef = `INV-${Date.now()}`;
    const amount = pkg.price;

    const signatureString = `${tripayMerchantCode}${merchantRef}${amount}`;
    const encoder = new TextEncoder();
    const keyData = encoder.encode(tripayPrivateKey);
    const messageData = encoder.encode(signatureString);

    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );

    const signatureBuffer = await crypto.subtle.sign('HMAC', cryptoKey, messageData);
    const signature = Array.from(new Uint8Array(signatureBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    const tripayPayload = {
      method: 'QRIS',
      merchant_ref: merchantRef,
      amount: parseInt(amount),
      customer_name: full_name || 'Customer',
      customer_email: customer_email,
      customer_phone: phone_number || '',
      order_items: [
        {
          sku: package_id,
          name: pkg.name,
          price: parseInt(amount),
          quantity: 1,
        },
      ],
      return_url: `https://aksesgptmurah.tech/confirmation?order_id=${merchantRef}`,
      expired_time: Math.floor(Date.now() / 1000) + 24 * 3600,
      signature: signature,
    };

    const tripayResponse = await fetch(`${tripayBaseUrl}/transaction/create`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${tripayApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tripayPayload),
    });

    const tripayResult: TripayResponse = await tripayResponse.json();

    if (!tripayResult.success || !tripayResult.data) {
      console.error('Tripay error:', tripayResult);
      return new Response(
        JSON.stringify({
          error: 'Payment gateway error',
          details: tripayResult.message || 'Unknown error'
        }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const { error: insertError } = await supabase.from('orders').insert({
      order_id: merchantRef,
      customer_email: customer_email,
      full_name: full_name || null,
      phone_number: phone_number || null,
      package_id: package_id,
      amount: amount,
      payment_status: 'pending',
      invitation_status: 'pending',
      checkout_url: tripayResult.data.checkout_url,
      payment_method: 'QRIS',
      reference: tripayResult.data.reference,
    });

    if (insertError) {
      console.error('Database insert error:', insertError);
      return new Response(
        JSON.stringify({ error: 'Failed to save order', details: insertError.message }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        order_id: merchantRef,
        reference: tripayResult.data.reference,
        checkout_url: tripayResult.data.checkout_url,
        qr_string: tripayResult.data.qr_string,
        payment_method: 'QRIS',
        amount: amount,
        status: 'pending_payment',
      }),
      { status: 201, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
