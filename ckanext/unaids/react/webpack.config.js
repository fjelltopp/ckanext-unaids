const path = require('path')

const components = {
    'FileInputComponent':
        path.resolve(__dirname, 'components', 'FileInputComponent/index.js')
}

module.exports = {
    mode: 'development',
    target:'web',
    entry: components,
    output: {
        path: path.resolve('../assets/'),
        filename: '[name].js'
    },
    devtool: 'eval-source-map',
    module: {
        rules: [
            {
                test: /\.(jsx|js)$/,
                exclude: /node_modules/,
                use: [{
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            [
                                '@babel/preset-env', {
                                    "targets": "defaults"
                                }
                            ],
                            '@babel/preset-react'
                        ]
                    }
                }]
            }
        ]
    }    
}
