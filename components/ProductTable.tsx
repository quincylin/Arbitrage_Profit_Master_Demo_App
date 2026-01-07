import React from 'react';
import type { ProcessedProduct } from '../types';
import { ProductRow } from './ProductRow';
import { Tooltip } from './Tooltip';

interface ProductTableProps {
    products: ProcessedProduct[];
    onImageEnter: (e: React.MouseEvent<HTMLImageElement>, src: string) => void;
    onImageLeave: () => void;
}

export const ProductTable: React.FC<ProductTableProps> = ({ products, onImageEnter, onImageLeave }) => {
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
                <thead className="bg-slate-50 text-xs uppercase font-bold text-slate-500 tracking-wider">
                    <tr>
                        <th className="px-6 py-4 text-left w-[80px]">Image</th>
                        <th className="px-6 py-4 text-left w-2/5">Product Details</th>
                        <th className="px-6 py-4 text-left">Amazon Metrics</th>
                        <th className="px-6 py-4 text-left">
                             <Tooltip text="Cost of Goods Sold (COGS): The lowest price found from online retailers, representing your acquisition cost.">
                                <span className="border-b border-dotted border-slate-400 cursor-help">Competitor Pricing (COGS)</span>
                            </Tooltip>
                        </th>
                        <th className="px-6 py-4 text-left">
                            <Tooltip text="Net Profit and Return on Investment (ROI) are calculated based on the COGS, Amazon fees, and Buy Box price.">
                                <span className="border-b border-dotted border-slate-400 cursor-help">Analysis</span>
                            </Tooltip>
                        </th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                    {products.length > 0 ? (
                        products.map((product, index) => (
                            <ProductRow
                                key={`${product.ASIN}-${index}`}
                                product={product}
                                onImageEnter={onImageEnter}
                                onImageLeave={onImageLeave}
                            />
                        ))
                    ) : (
                        <tr>
                            <td colSpan={5} className="p-8 text-center text-slate-400">
                                No matching products found for your filter criteria.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};