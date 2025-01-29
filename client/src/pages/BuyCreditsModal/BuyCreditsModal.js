// client/src/pages/BuyCreditsModal/BuyCreditsModal.js

import React, { useEffect } from 'react';
import { usePayments } from '../../hooks/usePayments';
import './BuyCreditsModal.css';

function BuyCreditsModal({ isOpen, onClose }) {
  const {
    products,
    loading,
    error,
    fetchProducts,
    createCheckoutSession,
  } = usePayments();


  useEffect(() => {
    if (isOpen) {
      // For simplicity, always call fetchProducts. 
      // Or check if products.length === 0 before calling.
      fetchProducts().catch((err) => {
        console.error('Error fetching products:', err);
      });
    }
  }, [isOpen, fetchProducts]);

  // If not open, return null (don't render anything)
  if (!isOpen) {
    return null;
  }

  /**
   * Handler for when the user chooses a product
   */
  const handleBuy = async (productId) => {
    try {
      const checkoutUrl = await createCheckoutSession(productId);
      // Redirect to Stripe
      window.location.href = checkoutUrl;
    } catch (err) {
      console.error('Checkout session error:', err);
    }
  };

  return (
    <div className="buy-credits-overlay">
      <div className="buy-credits-modal">
        <button className="close-button" onClick={onClose}>×</button>

        <h2>Purchase Credits</h2>

        {/* If loading, show spinner or text */}
        {loading && <p>Loading...</p>}
        {/* If there's an error, show it */}
        {error && <p style={{ color: 'red' }}>{error}</p>}

        {/* The product list */}
        <div className="products-list">
          {/* Model Credits Section */}
          <div className="product-section">
            <div className="product-section-title">Model Credits</div>
            {products
              .filter(prod => prod.label.toLowerCase().includes('model'))
              .map((prod) => (
                <button
                  key={prod.id}
                  className="product-button model-product"
                  onClick={() => handleBuy(prod.id)}
                  disabled={loading}
                >
                  <span className="product-label">{prod.label}</span>
                  <span className="product-price">
                    ${(prod.price_cents / 100).toFixed(2)}
                  </span>
                </button>
              ))}
          </div>

          {/* Photoshoot Credits Section */}
          <div className="product-section">
            <div className="product-section-title">Photoshoot Credits</div>
            {products
              .filter(prod => !prod.label.toLowerCase().includes('model'))
              .map((prod) => (
                <button
                  key={prod.id}
                  className="product-button"
                  onClick={() => handleBuy(prod.id)}
                  disabled={loading}
                >
                  <span className="product-label">{prod.label}</span>
                  <span className="product-price">
                    ${(prod.price_cents / 100).toFixed(2)}
                  </span>
                </button>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default BuyCreditsModal;