import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './src/App';

const componentElement = document.getElementById('FileInputComponent');

const getAttr = (key) => {
    const val = componentElement.getAttribute(`data-${key}`);
    return ['None', ''].includes(val) ? null : val;
};

const loadingHtml = componentElement.innerHTML,
    maxResourceSize = parseInt(getAttr('maxResourceSize')),
    lfsServer = getAttr('lfsServer'),
    orgId = getAttr('orgId'),
    datasetName = getAttr('datasetName');

const existingResourceData = {
    urlType: getAttr('existingUrlType'),
    url: getAttr('existingUrl'),
    sha256: getAttr('existingSha256'),
    fileName: getAttr('existingFileName'),
    size: getAttr('existingSize'),
    forkResource: getAttr('existingForkResource'),
    forkSynced: getAttr('existingForkSynced') === 'True',
    forkActivity: getAttr('existingForkActivity'),
};

const currentResourceID = getAttr('currentResource');

const root = createRoot(componentElement);

// wait for ckan.i18n to load
window.addEventListener('load', function () {
    root.render(
        <App
            {...{
                loadingHtml,
                maxResourceSize,
                lfsServer,
                orgId,
                datasetName,
                existingResourceData,
                currentResourceID,
            }}
        />
    );
});
