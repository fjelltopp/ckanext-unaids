import React from 'react';

export default function HiddenFormInputs({ hiddenInputs }) {

    hiddenInputs = {
        ...hiddenInputs,
        last_modified: new Date().toISOString().replace('Z', '')
    };

    return Object.keys(hiddenInputs).map(key => (
        <input
            key={key}
            name={key}
            data-testid={key}
            value={hiddenInputs[key] || ''}
            type="hidden"
        />
    ));

}
