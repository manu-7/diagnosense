/**
 * Opens Razorpay Checkout for a given order, then hands the resulting
 * payment_id/signature back to the caller to verify server-side. The
 * checkout.js script itself is loaded via a <script> tag in index.html.
 */
export function openRazorpayCheckout({ order, patientName, patientEmail, onSuccess, onDismiss }) {
  if (!window.Razorpay) {
    alert("Payment SDK failed to load. Check your connection and try again.");
    return;
  }

  const rzp = new window.Razorpay({
    key: order.key_id,
    amount: order.amount,
    currency: order.currency || "INR",
    name: "DiagnoSense",
    description: "Diagnostic test booking",
    order_id: order.razorpay_order_id,
    prefill: {
      name: patientName,
      email: patientEmail,
    },
    theme: { color: "#0F6B5C" },
    handler: function (response) {
      onSuccess({
        booking_id: order.booking_id,
        razorpay_order_id: response.razorpay_order_id,
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_signature: response.razorpay_signature,
      });
    },
    modal: {
      ondismiss: () => onDismiss && onDismiss(),
    },
  });

  rzp.open();
}
