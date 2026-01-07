import React, { useState, useMemo, useCallback } from 'react';
import { Header } from './components/Header';
import { ProductTable } from './components/ProductTable';
import { Sidebar } from './components/Sidebar';
import { Spinner } from './components/Spinner';
import { ImagePreview } from './components/ImagePreview';
import { parseKeepaCSV } from './services/csvParser';
import { findLowestPrice } from './services/serpApiService';
import type { ProcessedProduct } from './types';

const App: React.FC = () => {
    const [apiKey, setApiKey] = useState<string>('');
    const [products, setProducts] = useState<ProcessedProduct[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [showProfitableOnly, setShowProfitableOnly] = useState<boolean>(false);
    const [progress, setProgress] = useState(0);
    const [hoveredImage, setHoveredImage] = useState<{ src: string; top: number; left: number } | null>(null);


    const handleResearch = useCallback(async (file: File) => {
        if (!apiKey) {
            setError('Please enter your SerpApi Key in the sidebar to start research.');
            return;
        }
        if (!file) {
            setError('Please upload a CSV file to start research.');
            return;
        }

        setIsLoading(true);
        setError(null);
        setProducts([]);
        setProgress(0);

        try {
            const parsedProducts = await parseKeepaCSV(file);
            const totalProducts = parsedProducts.length;
            const processedProducts: ProcessedProduct[] = [];

            for (let i = 0; i < totalProducts; i++) {
                const keepaProduct = parsedProducts[i];
                
                const { price: competitorPrice, error: apiError } = await findLowestPrice(keepaProduct['Product Codes: UPC'], apiKey);

                if (apiError) {
                    console.warn(`API Error for ${keepaProduct.ASIN}: ${apiError}`);
                }

                const sellingPrice = keepaProduct['Buy Box Price'];
                const fbaFees = keepaProduct['FBA Fees'];
                const costOfGoods = competitorPrice;
                const bufferFee = costOfGoods * 0.05;
                
                let netProfit = 0;
                let roi = -100;

                if (costOfGoods > 0) {
                    netProfit = sellingPrice - fbaFees - costOfGoods - bufferFee;
                    roi = (netProfit / (costOfGoods + bufferFee)) * 100;
                } else {
                    netProfit = 0;
                    roi = 0;
                }


                const processed: ProcessedProduct = {
                    ...keepaProduct,
                    competitorPrice: costOfGoods,
                    netProfit,
                    roi,
                    status: apiError ? 'error' : 'success'
                };
                processedProducts.push(processed);
                setProducts([...processedProducts]); // Update state incrementally
                setProgress(((i + 1) / totalProducts) * 100);
            }
        } catch (e) {
            const err = e as Error;
            setError(`Failed to process file: ${err.message}`);
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    }, [apiKey]);

    const filteredProducts = useMemo(() => {
        return products.filter(p => {
            const term = searchTerm.toLowerCase();
            const matchesSearch = p.Title.toLowerCase().includes(term) ||
                                  p.ASIN.toLowerCase().includes(term) ||
                                  (p['Product Codes: UPC'] || '').toLowerCase().includes(term);

            const matchesProfit = showProfitableOnly ? p.netProfit > 0 : true;

            return matchesSearch && matchesProfit;
        });
    }, [products, searchTerm, showProfitableOnly]);
    
    const handleImageMouseEnter = (e: React.MouseEvent<HTMLImageElement>, src: string) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setHoveredImage({
            src,
            top: rect.top,
            left: rect.right + 12, // Position it to the right of the thumbnail
        });
    };

    const handleImageMouseLeave = () => {
        setHoveredImage(null);
    };

    return (
        <div className="flex min-h-screen font-sans text-slate-800">
            <Sidebar apiKey={apiKey} setApiKey={setApiKey} onStartResearch={handleResearch} isLoading={isLoading} />
            <main className="flex-1 p-4 sm:p-6 lg:p-8">
                <div className="max-w-7xl mx-auto">
                    <Header
                        products={filteredProducts}
                        searchTerm={searchTerm}
                        setSearchTerm={setSearchTerm}
                        showProfitableOnly={showProfitableOnly}
                        setShowProfitableOnly={setShowProfitableOnly}
                    />

                    {error && (
                        <div className="mb-6 bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-md" role="alert">
                            <p className="font-bold">⚠️ System Error:</p>
                            <p>{error}</p>
                        </div>
                    )}
                    
                    <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
                       {isLoading && (
                           <div className="p-8 text-center">
                               <Spinner />
                               <p className="text-lg font-semibold text-indigo-600 mt-4">Researching Products...</p>
                               <p className="text-sm text-slate-500">Please wait while we fetch live data.</p>
                               <div className="w-full bg-slate-200 rounded-full h-2.5 mt-4">
                                  <div className="bg-indigo-600 h-2.5 rounded-full" style={{ width: `${progress}%`, transition: 'width 0.2s ease-in-out' }}></div>
                               </div>
                                <p className="text-xs text-slate-400 mt-1">{Math.round(progress)}% Complete</p>
                           </div>
                       )}
                       {!isLoading && products.length === 0 && (
                           <div className="p-16 text-center text-slate-500">
                               <h2 className="text-xl font-semibold mb-2">Welcome to Arbitrage Profit Master</h2>
                               <p>To get started, enter your SerpApi key and upload a Keepa CSV file using the sidebar.</p>
                           </div>
                       )}
                        {!isLoading && products.length > 0 && (
                            <ProductTable
                                products={filteredProducts}
                                onImageEnter={handleImageMouseEnter}
                                onImageLeave={handleImageMouseLeave}
                            />
                        )}
                    </div>
                </div>
            </main>
            {hoveredImage && (
                <ImagePreview src={hoveredImage.src} top={hoveredImage.top} left={hoveredImage.left} />
            )}
        </div>
    );
};

export default App;