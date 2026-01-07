import React from 'react';
import type { ProcessedProduct } from '../types';
import { CopyToClipboardButton } from './CopyToClipboardButton';
import { Tooltip } from './Tooltip';

interface ProductRowProps {
    product: ProcessedProduct;
    onImageEnter: (e: React.MouseEvent<HTMLImageElement>, src: string) => void;
    onImageLeave: () => void;
}

export const ProductRow: React.FC<ProductRowProps> = ({ product, onImageEnter, onImageLeave }) => {
    const isProfitable = product.netProfit > 0;
    const costWithBuffer = product.competitorPrice * 1.05;

    return (
        <tr className="fade-in hover:bg-slate-50 border-b border-slate-50 last:border-0 align-top">
            <td className="px-6 py-4">
                <img 
                    src={product.Image} 
                    className="w-16 h-16 object-contain bg-white p-1 rounded-md border border-slate-200 cursor-pointer transition-transform duration-200 hover:scale-110" 
                    alt={product.Title}
                    onMouseEnter={(e) => onImageEnter(e, product.Image)}
                    onMouseLeave={onImageLeave}
                />
            </td>
            
            <td className="px-6 py-4">
                <div className="font-bold text-slate-800 leading-snug mb-2 text-sm">{product.Title}</div>
                
                <div className="flex flex-wrap items-center gap-2 mb-1">
                    <div className="flex items-center bg-white rounded border border-slate-200 overflow-hidden shadow-sm group hover:border-indigo-300 transition-colors">
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-50 px-2 py-1 border-r border-slate-200">ASIN</span>
                        <span className="text-[10px] font-mono text-slate-700 px-2 py-1">{product.ASIN}</span>
                        <CopyToClipboardButton textToCopy={product.ASIN} />
                    </div>

                    <div className="flex items-center bg-white rounded border border-slate-200 overflow-hidden shadow-sm group hover:border-indigo-300 transition-colors">
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-50 px-2 py-1 border-r border-slate-200">UPC</span>
                        <span className="text-[10px] font-mono text-slate-700 px-2 py-1">{product['Product Codes: UPC'] || 'N/A'}</span>
                        <CopyToClipboardButton textToCopy={product['Product Codes: UPC'] || ''} />
                    </div>
                </div>
            </td>

            <td className="px-6 py-4">
                <a 
                    href={`https://www.amazon.com/dp/${product.ASIN}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-lg font-black text-slate-900 hover:text-orange-500"
                >
                    ${product['Buy Box Price'].toFixed(2)}
                </a>
                <div className="text-xs font-semibold text-red-500 bg-red-50 inline-block px-1.5 py-0.5 rounded mt-1 border border-red-100">
                    -${product['FBA Fees'].toFixed(2)} Fees
                </div>
            </td>
            
            <td className="px-6 py-4">
                 {product.status === 'error' ? (
                     <div className="bg-red-50 border border-red-200 rounded-lg p-2 shadow-sm max-w-[260px] text-xs text-red-700">
                         Could not find competitor pricing for this item.
                     </div>
                 ) : (
                    <div className="bg-white border border-slate-200 rounded-lg p-2 shadow-sm max-w-[260px]">
                        <div className="flex justify-between items-center mb-1 text-xs group">
                            <span className="text-slate-500 font-medium truncate w-24" title="Lowest Price Found">Lowest Price Found</span>
                             <span className="text-blue-600 font-bold bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                                ${product.competitorPrice.toFixed(2)}
                            </span>
                        </div>
                        <div className="mt-2 pt-2 border-t border-slate-100 text-[10px] text-slate-400">
                             <Tooltip text="The sum of COGS and a 5% buffer fee for incidentals. This is your total 'all-in' cost.">
                                <span className="border-b border-dotted border-slate-400 cursor-help">Total Cost (w/ 5% fee):</span>
                            </Tooltip>
                            {' '}
                            <span className="font-bold text-slate-600">${costWithBuffer.toFixed(2)}</span>
                        </div>
                    </div>
                 )}
            </td>

            <td className="px-6 py-4">
                 {product.status !== 'error' && (
                    <div className="flex flex-col items-start gap-1">
                        <Tooltip text="Net Profit = (Amazon Price) - (FBA Fees) - (Total Cost).">
                            <div className={`text-sm font-bold px-3 py-1.5 rounded-lg border shadow-sm ${isProfitable ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-400 border-slate-200'}`}>
                                {isProfitable ? '+' : ''}${product.netProfit.toFixed(2)}
                            </div>
                        </Tooltip>
                        <Tooltip text="Return on Investment = (Net Profit / Total Cost) * 100.">
                            <div className={`text-xs font-bold ml-1 ${isProfitable ? 'text-emerald-600' : 'text-slate-400'}`}>
                                ROI: {product.roi.toFixed(1)}%
                            </div>
                        </Tooltip>
                    </div>
                )}
            </td>
        </tr>
    );
};