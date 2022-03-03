import ReactDOM from 'react-dom';
import React from 'react';
import App from './src/App';

const componentElement =
  document.getElementById('DatasetReleaseComponent');
const getAttr = key => {
  const val = componentElement.getAttribute(`data-${key}`);
  return ['None', ''].includes(val) ? null : val;
};

const datasetReleases = JSON.parse(getAttr('datasetReleases'));

const loadCkan = callback => {
  if (
    typeof ckan === 'undefined' ||
    typeof ckan.i18n === 'undefined' ||
    typeof ckan.i18n._ === 'undefined') {
    setTimeout(() => loadCkan(callback), 10);
  } else {
    callback();
  }
};

loadCkan(() => {
  ReactDOM.render(
    <App {...{ datasetReleases }} />,
    componentElement
  );
});
