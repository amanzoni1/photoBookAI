// client/src/hooks/usePayments.js

import { useState, useCallback } from 'react';
import axios from '../utils/axiosConfig';

export const usePayments = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [products, setProducts] = useState([]);

    const createCheckoutSession = useCallback(async (productId) => {
        setLoading(true);
        setError(null);
        try {
            const res = await axios.post('/api/payments/create-checkout-session', {
                product_id: productId
            });
            // res.data => { url: 'https://checkout.stripe.com/...' }
            return res.data.url;
        } catch (err) {
            const errorMsg = err.response?.data?.message || 'Error creating checkout session';
            setError(errorMsg);
            throw err; // re-throw so caller can handle if needed
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchProducts = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await axios.get('/api/payments/products');
            setProducts(res.data); // e.g. an array of product objects
        } catch (err) {
            const errorMsg = err.response?.data?.message || 'Error fetching products';
            setError(errorMsg);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        products,
        loading,
        error,
        fetchProducts,
        createCheckoutSession,
    };
};