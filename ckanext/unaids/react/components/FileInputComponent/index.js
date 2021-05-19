import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/App';

const componentElement =
  document.getElementById('FileInputComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};
const
  loadingHtml = componentElement.innerHTML,
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
}

// wait for ckan.i18n to load
window.addEventListener('load', function () {
  ReactDOM.render(
    <App {...{
      loadingHtml,
      maxResourceSize, lfsServer, orgId,
      datasetName, existingResourceData
    }} />,
    componentElement
  );
})
