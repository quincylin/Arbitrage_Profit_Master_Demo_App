
import type { KeepaProduct } from '../types';

export const parseKeepaCSV = (file: File): Promise<KeepaProduct[]> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (event: ProgressEvent<FileReader>) => {
            if (!event.target?.result) {
                return reject(new Error('File content is empty.'));
            }
            const csvData = event.target.result as string;
            const lines = csvData.split('\n');
            if (lines.length < 2) {
                return reject(new Error('CSV file must have a header and at least one data row.'));
            }

            const header = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
            const requiredColumns: (keyof KeepaProduct)[] = ['Image', 'Title', 'ASIN', 'Product Codes: UPC', 'Buy Box Price', 'FBA Fees'];
            
            const columnIndices = requiredColumns.reduce((acc, colName) => {
                const index = header.indexOf(colName);
                if (index === -1) {
                    throw new Error(`Missing required column in CSV: ${colName}`);
                }
                acc[colName] = index;
                return acc;
            }, {} as Record<keyof KeepaProduct, number>);


            const products: KeepaProduct[] = [];
            for (let i = 1; i < lines.length; i++) {
                if (!lines[i].trim()) continue;

                // Simple CSV parsing - doesn't handle commas within quotes
                const data = lines[i].split(',');

                try {
                    const priceStr = data[columnIndices['Buy Box Price']];
                    const feesStr = data[columnIndices['FBA Fees']];

                    products.push({
                        'Image': data[columnIndices['Image']].replace(/"/g, ''),
                        'Title': data[columnIndices['Title']].replace(/"/g, ''),
                        'ASIN': data[columnIndices['ASIN']].replace(/"/g, ''),
                        'Product Codes: UPC': data[columnIndices['Product Codes: UPC']].replace(/"/g, ''),
                        'Buy Box Price': priceStr ? parseFloat(priceStr) : 0,
                        'FBA Fees': feesStr ? parseFloat(feesStr) : 0,
                    });
                } catch (e) {
                     console.warn(`Skipping malformed row ${i+1}: ${lines[i]}`);
                }
            }
            resolve(products);
        };

        reader.onerror = () => {
            reject(new Error('Failed to read the file.'));
        };

        reader.readAsText(file);
    });
};
