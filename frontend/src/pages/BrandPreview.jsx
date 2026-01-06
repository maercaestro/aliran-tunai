import brandConfig from '../config/brand'

export default function BrandPreview() {
  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-8">Brand Configuration Preview</h1>
        
        {/* Logo Preview */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Logo</h2>
          <div className="bg-gray-900 rounded p-8 flex justify-center items-center">
            <img 
              src={brandConfig.logo.path} 
              alt={brandConfig.logo.alt} 
              className="h-32 object-contain"
            />
          </div>
          <div className="mt-4 text-sm text-gray-400">
            <p>Path: {brandConfig.logo.path}</p>
            <p>Alt Text: {brandConfig.logo.alt}</p>
          </div>
        </div>

        {/* Brand Name */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Brand Name</h2>
          <p className="text-3xl font-bold" style={{ color: brandConfig.colors.primary }}>
            {brandConfig.name}
          </p>
        </div>

        {/* Colors */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Color Palette</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(brandConfig.colors).map(([name, color]) => (
              <div key={name} className="flex flex-col items-center">
                <div 
                  className="w-20 h-20 rounded-lg shadow-lg mb-2" 
                  style={{ backgroundColor: color }}
                />
                <p className="text-xs text-gray-400 text-center">{name}</p>
                <p className="text-xs text-gray-500">{color}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Meta Information */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Meta Information</h2>
          <div className="space-y-2 text-gray-300">
            <p><span className="text-gray-500">Title:</span> {brandConfig.meta.title}</p>
            <p><span className="text-gray-500">Description:</span> {brandConfig.meta.description}</p>
            <p><span className="text-gray-500">Keywords:</span> {brandConfig.meta.keywords}</p>
          </div>
        </div>

        {/* Button Preview */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Button Samples</h2>
          <div className="space-x-4">
            <button 
              className="px-6 py-3 rounded-lg font-semibold text-white transition"
              style={{ 
                backgroundColor: brandConfig.colors.primary,
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = brandConfig.colors.primaryHover}
              onMouseLeave={(e) => e.target.style.backgroundColor = brandConfig.colors.primary}
            >
              Primary Button
            </button>
            <button 
              className="px-6 py-3 rounded-lg font-semibold text-white transition"
              style={{ 
                backgroundColor: brandConfig.colors.secondary,
              }}
            >
              Secondary Button
            </button>
          </div>
        </div>

        {/* Environment Check */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Environment Variables Status</h2>
          <div className="space-y-1 text-sm font-mono">
            <p className={import.meta.env.VITE_BRAND_NAME ? 'text-green-400' : 'text-yellow-400'}>
              VITE_BRAND_NAME: {import.meta.env.VITE_BRAND_NAME || '(using default)'}
            </p>
            <p className={import.meta.env.VITE_BRAND_LOGO_PATH ? 'text-green-400' : 'text-yellow-400'}>
              VITE_BRAND_LOGO_PATH: {import.meta.env.VITE_BRAND_LOGO_PATH || '(using default)'}
            </p>
            <p className={import.meta.env.VITE_BRAND_COLOR_PRIMARY ? 'text-green-400' : 'text-yellow-400'}>
              VITE_BRAND_COLOR_PRIMARY: {import.meta.env.VITE_BRAND_COLOR_PRIMARY || '(using default)'}
            </p>
          </div>
          <p className="mt-4 text-xs text-gray-500">
            Green = Environment variable set | Yellow = Using default value
          </p>
        </div>

        {/* Back Link */}
        <div className="mt-8 text-center">
          <a href="/" className="text-blue-400 hover:text-blue-300">← Back to App</a>
        </div>
      </div>
    </div>
  )
}
