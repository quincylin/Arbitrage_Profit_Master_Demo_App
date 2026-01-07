
export interface KeepaProduct {
    'Image': string;
    'Title': string;
    'ASIN': string;
    'Product Codes: UPC': string;
    'Buy Box Price': number;
    'FBA Fees': number;
}

export interface ProcessedProduct extends KeepaProduct {
    competitorPrice: number;
    netProfit: number;
    roi: number;
    status: 'success' | 'error';
}

export interface SerpApiResult {
    price: number;
    error?: string;
}
