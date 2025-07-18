const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
    app.use(
        '/ws',
        createProxyMiddleware({
            target: 'ws://localhost:5000',
            ws: true,
            changeOrigin: true,
        })
    );
};