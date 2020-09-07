module.exports = {
    devServer: {
        proxy: {
            "/": {
              target: 'http://localhost:8088'
            },
            "/stream/create": {
                target: 'http://localhost:8088/stream/create'
            },
            "/ws/": {
                target: 'http://locahost:8088/ws/'
            },
            "/stream/delete": {
                target: 'http://localhost:8088/stream/delete'
            }
        }
        // public: '192.168.55.105:8081',
    }
}