
import type { ProcessedProduct } from '../types';

/**
 * Converts an array of product data into a CSV string and triggers a download.
 * @param products The array of processed products to export.
 */
export const exportToCSV = (products: ProcessedProduct[]): void => {
    if (products.length === 0) {
        console.warn('No products to export.');
        return;
    }

    const headers: (keyof ProcessedProduct)[] = [
        'ASIN',
        'Title',
        'Image',
        'Product Codes: UPC',
        'Buy Box Price',
        'FBA Fees',
        'competitorPrice',
        'netProfit',
        'roi',
    ];

    const headerRow = headers.join(',');

    const rows = products.map(product => {
        const values = headers.map(header => {
            const value = product[header];
            if (typeof value === 'string') {
                // Escape quotes and wrap in quotes if it contains a comma
                const sanitizedValue = value.replace(/"/g, '""');
                return `"${sanitizedValue}"`;
            }
             if (typeof value === 'number') {
                // Format numbers to 2 decimal places where appropriate
                if (header === 'netProfit' || header === 'roi') {
                    return value.toFixed(2);
                }
            }
            return value;
        });
        return values.join(',');
    });

    const csvContent = [headerRow, ...rows].join('\n');
    
    // Create a Blob and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'arbitrage-profit-master-export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
};
