const path = require('path')

const outputPath = path.resolve('../assets/build/');
const components = {
    'FileInputComponent':
        path.resolve(__dirname, 'components', 'FileInputComponent/index.js'),
    'BulkFileUploaderComponent':
        path.resolve(__dirname, 'components', 'BulkFileUploaderComponent/index.js'),
    'DatasetReleaseComponent':
        path.resolve(__dirname, 'components', 'DatasetReleaseComponent/index.js'),
}

module.exports = {
    mode: 'development',
    target: 'web',
    entry: components,
    output: {
        path: outputPath,
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
