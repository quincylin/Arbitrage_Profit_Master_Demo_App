
import type { SerpApiResult } from '../types';

// This is a MOCK service to simulate calling the SerpApi Google Shopping Engine.
// It now includes an in-memory cache to avoid redundant API calls.

// Cache to store results. The key is the UPC.
const cache = new Map<string, SerpApiResult>();
// Keep track of the last API key used to invalidate the cache if it changes.
let lastApiKey: string | null = null;

export const findLowestPrice = (upc: string, apiKey: string): Promise<SerpApiResult> => {
    // If the API key has changed, the old cache is invalid.
    if (apiKey !== lastApiKey) {
        console.log('API key changed. Clearing cache.');
        cache.clear();
        lastApiKey = apiKey;
    }

    // Check if the result is already in the cache for the given UPC.
    if (upc && cache.has(upc)) {
        console.log(`[CACHE HIT] Found price for UPC: ${upc}`);
        return Promise.resolve(cache.get(upc)!);
    }

    console.log(`[CACHE MISS] Searching for UPC: ${upc} with key: ${apiKey.substring(0, 4)}...`);

    // In a real-world scenario, you would replace this with an actual HTTP request
    // to your backend, which would then securely call the SerpApi.
    return new Promise(resolve => {
        // Simulate network latency
        const delay = 500 + Math.random() * 1000;

        setTimeout(() => {
            let result: SerpApiResult;
            // Simulate API failure rate (e.g., 10% chance of failure or no UPC)
            if (Math.random() < 0.1 || !upc) {
                result = {
                    price: 0,
                    error: 'Product not found or API error.'
                };
            } else {
                // Simulate finding a price. A real implementation would parse the SerpApi JSON response here.
                const randomPrice = 20 + Math.random() * 80;
                result = {
                    price: parseFloat(randomPrice.toFixed(2))
                };
            }
            
            // Store the result in the cache before resolving the promise, but only if there is a UPC.
            if (upc) {
                cache.set(upc, result);
            }
            resolve(result);

        }, delay);
    });
};

/**
 * Simulates validating an API key. A real implementation would call the SerpApi /account endpoint.
 * @param apiKey The API key to validate.
 * @returns A promise that resolves with the validation status.
 */
export const validateKey = (apiKey: string): Promise<{ isValid: boolean, message: string }> => {
    return new Promise(resolve => {
        // Simulate network delay for validation check
        setTimeout(() => {
            if (!apiKey) {
                resolve({ isValid: false, message: '' }); // No message for empty input
                return;
            }
            if (apiKey.length < 20) { // Basic length check
                 resolve({ isValid: false, message: 'This API key appears to be malformed.' });
                 return;
            }
            // Simulate a known bad key for testing purposes
            if (apiKey.toLowerCase().includes('invalid')) {
                resolve({ isValid: false, message: 'Authentication failed. This API key is invalid.' });
                return;
            }
            
            // If it passes basic checks, assume it's valid for this mock.
            resolve({ isValid: true, message: 'API Key is valid and ready!' });
        }, 500); // 500ms delay to simulate network request
    });
};
